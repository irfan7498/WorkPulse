import frappe


@frappe.whitelist()
def get_dashboard_data():
    metrics = [
        ("employees", "Employee", None, "People"),
        (
            "active_tasks",
            "Task",
            {"status": ["not in", ["Completed", "Cancelled"]]},
            "Active Tasks",
        ),
        (
            "active_projects",
            "Project",
            {"status": ["not in", ["Completed", "Cancelled"]]},
            "Active Projects",
        ),
        ("open_leave", "Leave Application", {"status": "Open"}, "Open Leave"),
        ("candidates", "Job Applicant", None, "Candidates"),
        ("snapshots", "WP Workload Snapshot", None, "Workload Snapshots"),
        ("project_snapshots", "WP Project Snapshot", None, "Project Snapshots"),
    ]
    counts = {
        key: _count(doctype, filters)
        for key, doctype, filters, _label in metrics
    }

    return {
        "title": "WorkPulse",
        "user": frappe.session.user,
        "metrics": [
            {"key": key, "label": label, "value": counts[key]}
            for key, _doctype, _filters, label in metrics
        ],
        "links": {
            "data_health": "/desk/query-report/WorkPulse Data Health",
            "settings": "/desk/workpulse-settings",
        },
        "project_health": _project_health(),
    }


def _count(doctype, filters=None):
    if not frappe.has_permission(doctype, "read"):
        return None

    result = frappe.get_list(
        doctype,
        fields=[{"COUNT": "*", "as": "count"}],
        filters=filters,
        limit_page_length=1,
    )
    return result[0]["count"] if result else 0


def _project_health():
    if not frappe.has_permission("WP Project Snapshot", "read"):
        return None
    rows = frappe.get_all(
        "WP Project Snapshot",
        filters={"date": frappe.utils.today()},
        fields=["risk_level"],
    )
    return {
        "total": len(rows),
        "high": sum(row.risk_level == "High" for row in rows),
        "medium": sum(row.risk_level == "Medium" for row in rows),
        "low": sum(row.risk_level == "Low" for row in rows),
    }
