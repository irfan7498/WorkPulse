import json

import frappe
from frappe.utils import getdate, today


def enqueue_daily_project_snapshots():
    frappe.enqueue(
        "workpulse.tasks.project_snapshots.build_daily_project_snapshots",
        queue="long",
        job_id=f"project-snapshots-{today()}",
        deduplicate=True,
    )


def build_daily_project_snapshots(snapshot_date=None):
    snapshot_date = getdate(snapshot_date or today())
    created = 0
    for project in frappe.get_all("Project", pluck="name"):
        metrics = _project_metrics(project, snapshot_date)
        snapshot = frappe.db.exists(
            "WP Project Snapshot", {"project": project, "date": snapshot_date}
        )
        doc = frappe.get_doc("WP Project Snapshot", snapshot) if snapshot else frappe.new_doc(
            "WP Project Snapshot"
        )
        doc.update({"project": project, "date": snapshot_date, **metrics})
        doc.save(ignore_permissions=True)
        created += 1
    return {"date": str(snapshot_date), "created": created}


def _project_metrics(project, snapshot_date):
    tasks = frappe.get_all(
        "Task",
        filters={"project": project},
        fields=["name", "status", "progress", "priority", "exp_end_date", "expected_time"],
    )
    total = sum(max(float(task.expected_time or 0), 1) for task in tasks)
    weighted_progress = (
        sum(max(float(task.expected_time or 0), 1) * float(task.progress or 0) for task in tasks)
        / total
        if tasks
        else 0
    )
    planned = _planned_progress(tasks, snapshot_date)
    overdue = [
        task for task in tasks
        if task.exp_end_date and getdate(task.exp_end_date) < snapshot_date
        and task.status not in {"Completed", "Cancelled"}
    ]
    open_tasks = [task for task in tasks if task.status not in {"Completed", "Cancelled"}]
    risk_score = min(100, len(overdue) * 8 + len(open_tasks) * 2)
    if planned > weighted_progress + 15:
        risk_score = min(100, risk_score + 20)
    risk_level = "High" if risk_score >= 55 else "Medium" if risk_score >= 25 else "Low"
    bottlenecks = sorted(
        ({"task": task.name, "priority": task.priority, "reason": "overdue"} for task in overdue),
        key=lambda item: {"Urgent": 0, "High": 1, "Medium": 2, "Low": 3}.get(item["priority"], 4),
    )[:10]
    spi = weighted_progress / planned if planned else (1 if weighted_progress else 0)
    return {
        "weighted_progress": weighted_progress,
        "planned_progress": planned,
        "spi": spi,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "bottlenecks": json.dumps(bottlenecks),
        "critical_path": json.dumps([item["task"] for item in bottlenecks[:5]]),
        "delay_probability": min(100, risk_score),
        "top_factors": json.dumps(
            [{"factor": "Overdue tasks", "count": len(overdue)}]
            if overdue else [{"factor": "No overdue tasks", "count": 0}]
        ),
    }


def _planned_progress(tasks, snapshot_date):
    dated = [task for task in tasks if task.exp_end_date]
    if not dated:
        return 0
    due = sum(1 for task in dated if getdate(task.exp_end_date) <= snapshot_date)
    return due / len(dated) * 100
