"""Permission-aware data endpoints for Workforce Explorer."""

from __future__ import annotations

import json

import frappe


@frappe.whitelist()
def get_tree(
    parent: str | None = None,
    node_type: str = "portfolio",
    filters: dict | None = None,
) -> list[dict]:
    """Return one lazy tree level without exposing unreadable linked records."""
    if not frappe.has_permission("Employee", "read"):
        if not _is_privileged_user():
            return [_current_employee_node()] if _current_employee_node() else []
        frappe.throw("You do not have permission to view workforce data.", frappe.PermissionError)

    filters = frappe.parse_json(filters) if isinstance(filters, str) else (filters or {})
    nodes = []
    if node_type == "portfolio":
        portfolios = frappe.get_all(
            "WP Portfolio",
            filters={"parent_wp_portfolio": parent} if parent else {"parent_wp_portfolio": ["is", "not set"]},
            fields=["name", "portfolio_name", "is_group"],
        )
        nodes.extend(
            {
                "id": portfolio.name,
                "type": "portfolio",
                "label": portfolio.portfolio_name,
                "has_children": True,
            }
            for portfolio in portfolios
        )
        if not parent:
            nodes.extend(_unassigned_project_nodes(filters))
            if not nodes:
                nodes.extend(_employee_nodes(filters))
    elif node_type == "project" and parent:
        project_filters = _project_filters(filters)
        if _has_field("Project", "wp_portfolio"):
            project_filters["wp_portfolio"] = parent
        for project in frappe.get_all(
            "Project",
            filters=project_filters,
            fields=["name", "project_name", "status", "percent_complete"],
        ):
            if frappe.has_permission("Project", "read", project.name):
                nodes.append(
                    {
                        "id": project.name,
                        "type": "project",
                        "label": project.project_name or project.name,
                        "status": project.status,
                        "progress": project.percent_complete,
                        "has_children": True,
                    }
                )
    elif node_type == "team" and parent:
        for team in frappe.get_all(
            "WP Team", filters={"project": parent}, fields=["name", "team_name", "lead"]
        ):
            if frappe.has_permission("WP Team", "read", team.name):
                nodes.append(
                    {"id": team.name, "type": "team", "label": team.team_name, "lead": team.lead, "has_children": True}
                )
    elif node_type == "member" and parent:
        team = frappe.get_doc("WP Team", parent)
        if frappe.has_permission("WP Team", "read", team.name):
            for member in team.members:
                if _employee_visible(member.employee, filters):
                    nodes.append(
                        {
                            "id": member.employee,
                            "type": "employee",
                            "label": frappe.db.get_value("Employee", member.employee, "employee_name"),
                            "allocation_pct": member.allocation_pct,
                            "has_children": False,
                        }
                    )
    return nodes


@frappe.whitelist()
def get_employee_card(employee: str) -> dict:
    """Return the employee summary and latest permitted workload snapshot."""
    if not _employee_visible(employee):
        frappe.throw("You do not have permission to view this employee.", frappe.PermissionError)
    row = frappe.db.get_value(
        "Employee",
        employee,
        ["name", "employee_name", "designation", "department", "status", "user_id"],
        as_dict=True,
    )
    if not row:
        frappe.throw("Employee not found.", frappe.DoesNotExistError)
    snapshots = frappe.get_all(
        "WP Workload Snapshot",
        filters={"employee": employee},
        fields=["week_start", "capacity_h", "planned_h", "workload_pct", "active_tasks", "flags"],
        order_by="week_start desc",
        limit_page_length=5,
    )
    for snapshot in snapshots:
        snapshot["flags"] = _parse_json(snapshot.get("flags"))
    return {
        "employee": row,
        "snapshots": snapshots,
        "contribution": _get_contribution(row),
        "history": frappe.get_all(
            "WP Employee Project History",
            filters={"employee": employee},
            fields=["project", "role", "from_date", "to_date", "tasks_done", "on_time_pct"],
            order_by="to_date desc",
            limit_page_length=10,
        ),
    }


def _project_filters(filters: dict) -> dict:
    allowed = {"status": "status", "project": "name"}
    return {allowed[key]: value for key, value in filters.items() if key in allowed and value not in (None, "")}


def _unassigned_project_nodes(filters: dict) -> list[dict]:
    if not _has_field("Project", "wp_portfolio"):
        return []
    projects = frappe.get_all(
        "Project",
        filters={"wp_portfolio": ["is", "not set"], **_project_filters(filters)},
        fields=["name", "project_name", "status", "percent_complete"],
    )
    return [
        {
            "id": project.name,
            "type": "project",
            "label": project.project_name or project.name,
            "status": project.status,
            "progress": project.percent_complete,
            "has_children": True,
            "unassigned_portfolio": True,
        }
        for project in projects
        if frappe.has_permission("Project", "read", project.name)
    ]


def _employee_nodes(filters: dict) -> list[dict]:
    employee_filters = {}
    if filters.get("employee_status"):
        employee_filters["status"] = filters["employee_status"]
    rows = frappe.get_all(
        "Employee",
        filters=employee_filters,
        fields=["name", "employee_name", "department", "designation"],
        order_by="employee_name asc",
        limit_page_length=500,
    )
    return [
        {
            "id": row.name,
            "type": "employee",
            "label": row.employee_name or row.name,
            "department": row.department,
            "designation": row.designation,
            "has_children": False,
        }
        for row in rows
        if _employee_visible(row.name, filters)
    ]


def _employee_visible(employee: str, filters: dict | None = None) -> bool:
    if not frappe.has_permission("Employee", "read", employee):
        return False
    if _is_self(employee):
        return True
    if _is_privileged_user():
        return _matches_employee_filters(employee, filters or {})
    return False


def _is_self(employee: str | None) -> bool:
    if not employee:
        return False
    return frappe.db.get_value("Employee", employee, "user_id") == frappe.session.user


def _is_privileged_user() -> bool:
    return bool(
        set(frappe.get_roles()) & {"System Manager", "HR Manager", "Projects Manager", "Projects User"}
    )


def _current_employee_node() -> dict | None:
    employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    if not employee:
        return None
    row = frappe.db.get_value("Employee", employee, "employee_name")
    return {"id": employee, "type": "employee", "label": row or employee, "has_children": False}


def _has_field(doctype: str, fieldname: str) -> bool:
    return bool(frappe.get_meta(doctype).has_field(fieldname))


def _matches_employee_filters(employee: str, filters: dict) -> bool:
    row = frappe.db.get_value("Employee", employee, ["department", "status", "employee_name"], as_dict=True)
    if not row:
        return False
    if filters.get("department") and row.department != filters["department"]:
        return False
    if filters.get("employee_status") and row.status != filters["employee_status"]:
        return False
    search = (filters.get("search") or "").strip().lower()
    return not search or search in (row.employee_name or "").lower() or search in employee.lower()


def _get_contribution(employee: dict) -> dict:
    timesheets = frappe.get_all(
        "Timesheet",
        filters={"employee": employee.name, "docstatus": 1},
        fields=["name"],
        limit_page_length=5000,
    )
    details = (
        frappe.get_all(
            "Timesheet Detail",
            filters={"parent": ["in", [row.name for row in timesheets]]},
            fields=["hours", "task", "project"],
            limit_page_length=5000,
        )
        if timesheets
        else []
    )
    tasks = frappe.get_all(
        "ToDo",
        filters={
            "allocated_to": employee.user_id,
            "reference_type": "Task",
            "status": ["in", ["Open", "Working", "Closed"]],
        },
        fields=["reference_name", "status"],
        limit_page_length=5000,
    ) if employee.user_id else []
    return {
        "logged_hours": round(sum(float(row.hours or 0) for row in details), 2),
        "timesheet_entries": len(details),
        "task_count": len({row.reference_name for row in tasks if row.reference_name}),
        "open_task_count": sum(row.status in {"Open", "Working"} for row in tasks),
    }


def _parse_json(value):
    if not value:
        return []
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return [value]
