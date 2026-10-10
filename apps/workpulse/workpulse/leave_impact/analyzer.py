import json

import frappe
from frappe.utils import add_days, getdate, now_datetime, today


PRIORITY_WEIGHT = {"Urgent": 25, "High": 15, "Medium": 8, "Low": 3}


def run(leave_application: str):
    leave = frappe.get_doc("Leave Application", leave_application)
    if leave.status != "Open":
        return

    analysis = _get_or_create_analysis(leave)
    analysis.status = "Processing"
    analysis.error_message = ""
    analysis.job_id = f"leave-impact-{leave.name}"
    analysis.save(ignore_permissions=True)

    try:
        settings = frappe.get_doc("WorkPulse Settings")
        evidence = gather_evidence(leave, settings)
        score, level = score_risk(evidence)
        evidence.update({"risk_score": score, "risk_level": level})
        recommendation = rules_recommendation(evidence)
        _save_success(analysis, leave, evidence, recommendation, score, level)
    except Exception:
        analysis.status = "Failed"
        analysis.error_message = frappe.get_traceback()[-4000:]
        analysis.generated_on = now_datetime()
        analysis.save(ignore_permissions=True)
        frappe.log_error(title=f"WorkPulse analysis failed: {leave.name}")
        raise


def gather_evidence(leave, settings):
    start, end = getdate(leave.from_date), getdate(leave.to_date)
    buffer_end = add_days(end, settings.lookahead_days or 7)
    user = frappe.db.get_value("Employee", leave.employee, "user_id")
    tasks = []

    if user:
        task_names = frappe.get_all(
            "ToDo",
            filters={"reference_type": "Task", "allocated_to": user, "status": "Open"},
            pluck="reference_name",
        )
        if task_names:
            rows = frappe.get_all(
                "Task",
                filters={
                    "name": ["in", task_names],
                    "status": ["not in", ["Completed", "Cancelled"]],
                },
                fields=[
                    "name",
                    "subject",
                    "project",
                    "priority",
                    "status",
                    "exp_start_date",
                    "exp_end_date",
                    "progress",
                ],
            )
            for task in rows:
                due = getdate(task.exp_end_date) if task.exp_end_date else None
                task_start = getdate(task.exp_start_date) if task.exp_start_date else None
                if due and due < getdate(today()):
                    task["reason"] = "overdue"
                elif due and start <= due <= buffer_end:
                    task["reason"] = "due during leave or shortly after return"
                elif task_start and due and task_start <= end and due >= start:
                    task["reason"] = "work window overlaps leave"
                else:
                    continue
                task["exp_start_date"] = str(task.exp_start_date or "")
                task["exp_end_date"] = str(task.exp_end_date or "")
                tasks.append(task)

    overlaps, team_size = [], 0
    if leave.department:
        overlaps = frappe.get_all(
            "Leave Application",
            filters={
                "department": leave.department,
                "name": ["!=", leave.name],
                "docstatus": ["<", 2],
                "status": ["in", ["Open", "Approved"]],
                "from_date": ["<=", leave.to_date],
                "to_date": [">=", leave.from_date],
            },
            fields=["employee_name", "from_date", "to_date", "status"],
        )
        for overlap in overlaps:
            overlap["from_date"] = str(overlap.from_date)
            overlap["to_date"] = str(overlap.to_date)
        team_size = frappe.db.count("Employee", {"department": leave.department, "status": "Active"})

    balance = None
    try:
        from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on

        balance = get_leave_balance_on(leave.employee, leave.leave_type, leave.from_date)
    except Exception:
        pass

    return {
        "employee": leave.employee_name,
        "department": leave.department,
        "leave_type": leave.leave_type,
        "from_date": str(leave.from_date),
        "to_date": str(leave.to_date),
        "total_leave_days": leave.total_leave_days,
        "impacted_tasks": tasks,
        "teammates_on_leave": overlaps,
        "team_size": team_size,
        "leave_balance": balance,
    }


def score_risk(evidence):
    score = 0
    high_priority_tasks = 0
    for task in evidence["impacted_tasks"]:
        score += PRIORITY_WEIGHT.get(task.get("priority"), 5)
        if task.get("priority") in {"Urgent", "High"}:
            high_priority_tasks += 1
        if task["reason"] == "overdue":
            score += 5
    if high_priority_tasks >= 2:
        score += 15
    if evidence["team_size"]:
        absent_ratio = (len(evidence["teammates_on_leave"]) + 1) / evidence["team_size"]
        score += 30 if absent_ratio >= 0.5 else 15 if absent_ratio >= 0.3 else 0
    if (evidence["total_leave_days"] or 0) > 5:
        score += 5
    score = min(score, 100)
    level = "Low" if score < 25 else "Medium" if score < 55 else "High"
    return score, level


def rules_recommendation(evidence):
    level = evidence["risk_level"]
    action = {"Low": "Approve", "Medium": "Approve with conditions", "High": "Defer"}[level]
    tasks = "".join(
        f"<li>{task['name']}: {task['subject']} ({task.get('priority')}, {task['reason']})</li>"
        for task in evidence["impacted_tasks"]
    ) or "<li>No impacted tasks found.</li>"
    return {
        "suggested_action": action,
        "summary": (
            f"{level} risk: {len(evidence['impacted_tasks'])} task(s) affected, "
            f"{len(evidence['teammates_on_leave'])} teammate(s) also away."
        ),
        "reasoning": f"<ul>{tasks}</ul>",
        "mitigations": "<ul><li>Reassign or reschedule the listed tasks before approval.</li></ul>",
    }


def _get_or_create_analysis(leave):
    name = frappe.db.get_value("Leave Impact Analysis", {"leave_application": leave.name}, "name")
    if name:
        return frappe.get_doc("Leave Impact Analysis", name)

    analysis = frappe.new_doc("Leave Impact Analysis")
    analysis.leave_application = leave.name
    analysis.name = f"LIA-{leave.name.rsplit('-', 1)[-1]}"
    return analysis


def _save_success(analysis, leave, evidence, recommendation, score, level):
    analysis.update(
        {
            "leave_application": leave.name,
            "employee": leave.employee,
            "employee_name": leave.employee_name,
            "from_date": leave.from_date,
            "to_date": leave.to_date,
            "risk_level": level,
            "risk_score": score,
            "suggested_action": recommendation["suggested_action"],
            "summary": recommendation["summary"],
            "reasoning": recommendation["reasoning"],
            "mitigations": recommendation["mitigations"],
            "evidence": json.dumps(evidence, default=str, indent=2),
            "model_used": "rules",
            "generated_on": now_datetime(),
            "status": "Completed",
            "error_message": "",
        }
    )
    analysis.save(ignore_permissions=True)
    frappe.publish_realtime(
        "workpulse_leave_impact_ready",
        {"leave": leave.name},
        doctype="Leave Application",
        docname=leave.name,
    )