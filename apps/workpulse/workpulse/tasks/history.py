"""Build auditable employee/project history records from ERPNext activity."""

from __future__ import annotations

import json

import frappe
from frappe.utils import getdate, nowdate


def build_employee_project_history() -> int:
    """Upsert one history record per employee/project with completed task evidence."""
    assignments = frappe.get_all(
        "ToDo",
        filters={"reference_type": "Task", "status": "Closed"},
        fields=["allocated_to", "reference_name"],
        limit_page_length=50000,
    )
    grouped = {}
    for assignment in assignments:
        employee = frappe.db.get_value("Employee", {"user_id": assignment.allocated_to}, "name")
        if not employee:
            continue
        task = frappe.db.get_value(
            "Task", assignment.reference_name,
            ["project", "exp_start_date", "exp_end_date", "expected_time", "actual_time"],
            as_dict=True,
        )
        if not task or not task.project:
            continue
        grouped.setdefault((employee, task.project), []).append(task)

    written = 0
    for (employee, project), tasks in grouped.items():
        start_dates = [getdate(task.exp_start_date) for task in tasks if task.exp_start_date]
        end_dates = [getdate(task.exp_end_date) for task in tasks if task.exp_end_date]
        from_date = min(start_dates) if start_dates else getdate(nowdate())
        to_date = max(end_dates) if end_dates else getdate(nowdate())
        on_time = sum(
            1 for task in tasks
            if float(task.actual_time or 0) <= float(task.expected_time or 0)
        )
        estimated = sum(float(task.expected_time or 0) for task in tasks)
        actual = sum(float(task.actual_time or 0) for task in tasks)
        error_pct = abs(actual - estimated) / estimated * 100 if estimated else 0
        filters = {"employee": employee, "project": project}
        name = frappe.db.exists("WP Employee Project History", filters)
        history = frappe.get_doc("WP Employee Project History", name) if name else frappe.new_doc("WP Employee Project History")
        history.update({
            "employee": employee,
            "project": project,
            "role": frappe.db.get_value("Employee", employee, "designation"),
            "from_date": from_date,
            "to_date": to_date,
            "tech_stack": json.dumps([]),
            "tasks_done": len(tasks),
            "on_time_pct": round(on_time / len(tasks) * 100, 2),
            "est_error_pct": round(error_pct, 2),
            "skills_demonstrated": json.dumps([]),
        })
        history.save(ignore_permissions=True)
        written += 1
    return written


def enqueue_history_build() -> None:
    frappe.enqueue(
        "workpulse.tasks.history.build_employee_project_history",
        queue="long",
        job_id="workpulse-history-build",
        deduplicate=True,
        enqueue_after_commit=True,
    )
