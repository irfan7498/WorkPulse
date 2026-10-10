"""Approval endpoints for auditable allocation recommendations."""

from __future__ import annotations

import json

import frappe
from workpulse.engines.allocation import rank_candidates


@frappe.whitelist()
def suggest(task: str) -> dict:
    task_doc = frappe.get_doc("Task", task)
    if not frappe.has_permission("Task", "read", task_doc):
        frappe.throw("You do not have permission to view this task.", frappe.PermissionError)
    candidates = _rank_task_candidates(task_doc)
    recommendation = frappe.new_doc("WP Allocation Recommendation")
    recommendation.task = task_doc.name
    recommendation.status = "Suggested"
    recommendation.candidates = json.dumps(candidates)
    recommendation.explanation = (
        f"{len(candidates)} candidates ranked using workload, history, and reliability."
    )
    recommendation.engine_version = "rules-1"
    recommendation.weights_used = json.dumps(
        {"skill": 0.4, "capacity": 0.25, "history": 0.2, "reliability": 0.15}
    )
    recommendation.insert(ignore_permissions=True)
    return recommendation.as_dict()


def _rank_task_candidates(task_doc) -> list[dict]:
    employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name"],
        limit_page_length=5000,
    )
    candidates = []
    for employee in employees:
        snapshot = frappe.get_all(
            "WP Workload Snapshot",
            filters={"employee": employee.name},
            fields=["workload_pct"],
            order_by="week_start desc",
            limit_page_length=1,
        )
        history = frappe.get_all(
            "WP Employee Project History",
            filters={"employee": employee.name},
            fields=["on_time_pct", "est_error_pct", "tasks_done"],
            order_by="to_date desc",
            limit_page_length=20,
        )
        task_count = sum(int(row.tasks_done or 0) for row in history)
        on_time = sum(float(row.on_time_pct or 0) for row in history) / len(history) / 100 if history else 0
        error = sum(float(row.est_error_pct or 0) for row in history) / len(history) / 100 if history else 1
        candidates.append({
            "employee": employee.name,
            "current_workload_pct": float(snapshot[0].workload_pct or 0) if snapshot else 0,
            "level_by_skill": {},
            "history_score": min(1, on_time + min(task_count / 100, 0.2)),
            "reliability_score": max(0, on_time * (1 - min(error, 1))),
        })
    return rank_candidates(task_skills={}, candidates=candidates, workload_ceiling_pct=85)


@frappe.whitelist()
def approve(recommendation: str, employee: str | None = None) -> dict:
    rec = frappe.get_doc("WP Allocation Recommendation", recommendation)
    if not frappe.has_permission("WP Allocation Recommendation", "write", rec):
        frappe.throw("You do not have permission to approve recommendations.", frappe.PermissionError)
    if rec.status not in {"Suggested", "Approved"}:
        frappe.throw("Only suggested recommendations can be approved.")
    chosen = employee or rec.chosen_employee
    if not chosen:
        frappe.throw("Choose an employee before approving.")
    if not frappe.has_permission("Employee", "read", chosen):
        frappe.throw("You do not have permission to use this employee.", frappe.PermissionError)
    task = frappe.get_doc("Task", rec.task)
    user_id = frappe.db.get_value("Employee", chosen, "user_id")
    if not user_id:
        frappe.throw("The chosen employee has no linked user.")
    existing = frappe.db.exists(
        "ToDo",
        {"reference_type": "Task", "reference_name": task.name, "allocated_to": user_id, "status": ["in", ["Open", "Working"]]},
    )
    if not existing:
        frappe.get_doc(
            {
                "doctype": "ToDo",
                "allocated_to": user_id,
                "reference_type": "Task",
                "reference_name": task.name,
                "description": f"WorkPulse allocation recommendation {rec.name}",
                "status": "Open",
            }
        ).insert(ignore_permissions=True)
    frappe.db.set_value(
        "WP Allocation Recommendation",
        {"task": task.name, "status": "Suggested", "name": ["!=", rec.name]},
        "status",
        "Superseded",
    )
    rec.update({"status": "Approved", "chosen_employee": chosen, "approved_by": frappe.session.user})
    rec.save(ignore_permissions=True)
    return {"approved": True, "todo_created": not bool(existing), "employee": chosen}
