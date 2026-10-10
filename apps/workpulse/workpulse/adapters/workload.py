"""Frappe adapters for workload snapshots."""

from __future__ import annotations

from datetime import date, timedelta

import frappe
from frappe.utils import getdate, today

from workpulse.engines.capacity import calculate_capacity
from workpulse.engines.workload import calculate_workload_pct, task_week_allocation


def build_week_snapshots(*, week_start: date | str | None = None, employee: str | None = None) -> list[dict]:
    """Build current-week snapshot dictionaries for permitted active employees."""
    start = getdate(week_start or today())
    start -= timedelta(days=start.weekday())
    employee_filters = {"status": "Active"}
    if employee:
        employee_filters["name"] = employee
    employees = frappe.get_all(
        "Employee",
        filters=employee_filters,
        fields=["name", "user_id", "holiday_list"],
    )
    settings = frappe.get_cached_doc("WorkPulse Settings")
    result = []
    for row in employees:
        if not frappe.has_permission("Employee", "read", row["name"]):
            continue
        tasks = _employee_tasks(row.user_id)
        capacity = calculate_capacity(
            working_days=5,
            leave_days=_leave_days(row.name, start),
            daily_hours=settings.daily_hours or 8,
            meeting_overhead_pct=settings.meeting_overhead_pct or 0,
            project_allocation_share=1,
        )
        planned, flags = 0.0, set()
        for task in tasks:
            allocation, task_flags = task_week_allocation(
                task=task,
                week_start=start,
                fallback_hours=settings.default_task_hours or 8,
            )
            planned += allocation
            flags.update(task_flags)
        result.append(
            {
                "employee": row["name"],
                "week_start": start,
                "capacity_h": capacity,
                "planned_h": planned,
                "workload_pct": calculate_workload_pct(planned_hours=planned, capacity_hours=capacity),
                "active_tasks": len(tasks),
                "critical_tasks": sum(task.get("priority") in {"High", "Urgent"} for task in tasks),
                "leave_days": _leave_days(row.name, start),
                "flags": sorted(flags | ({"no_capacity"} if capacity == 0 and planned else set())),
            }
        )
    return result


def _employee_tasks(user_id: str | None) -> list[dict]:
    if not user_id:
        return []
    names = frappe.get_all(
        "ToDo",
        filters={"allocated_to": user_id, "reference_type": "Task", "status": ["in", ["Open", "Working"]]},
        pluck="reference_name",
    )
    if not names:
        return []
    return frappe.get_all(
        "Task",
        filters={"name": ["in", names], "status": ["not in", ["Completed", "Cancelled"]]},
        fields=[
            "name", "expected_time", "actual_time", "exp_start_date", "exp_end_date",
            "priority", "project",
        ],
    )


def _leave_days(employee: str, week_start: date) -> float:
    leaves = frappe.get_all(
        "Leave Application",
        filters={
            "employee": employee,
            "status": ["in", ["Open", "Approved"]],
            "from_date": ["<=", week_start + timedelta(days=6)],
            "to_date": [">=", week_start],
        },
        fields=["from_date", "to_date", "total_leave_days", "status"],
    )
    return sum(
        min(float(leave.total_leave_days or 0), 5)
        * (1 if leave.status == "Approved" else 0.5)
        for leave in leaves
    )
