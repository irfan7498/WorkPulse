import frappe
from frappe.utils import date_diff

from workpulse.engines.leave_policy import build_approval_chain, compact_chain


@frappe.whitelist()
def get_analysis(leave_application):
    leave = frappe.get_doc("Leave Application", leave_application)
    if not _can_view(leave):
        return None

    name = frappe.db.get_value(
        "Leave Impact Analysis", {"leave_application": leave_application}, "name"
    )
    if not name:
        return None
    analysis = frappe.get_doc("Leave Impact Analysis", name).as_dict()
    analysis["policy_chain"] = _policy_chain(leave, analysis)
    return analysis


def _policy_chain(leave, analysis):
    days = date_diff(leave.to_date, leave.from_date) + 1
    policies = frappe.get_all(
        "WP Leave Approval Policy",
        filters={"disabled": 0} if frappe.get_meta("WP Leave Approval Policy").has_field("disabled") else {},
        fields=["leave_types", "min_days", "max_days", "impact_level", "approver_chain", "priority"],
        order_by="priority asc",
    )
    for policy in policies:
        leave_types = [item.strip() for item in (policy.leave_types or "").split(",") if item.strip()]
        if leave_types and leave.leave_type not in leave_types:
            continue
        if policy.min_days and days < policy.min_days:
            continue
        if policy.max_days and days > policy.max_days:
            continue
        if policy.impact_level not in (None, "", "Any", analysis.get("risk_level")):
            continue
        try:
            chain = frappe.parse_json(policy.approver_chain or "[]")
        except (TypeError, ValueError):
            chain = []
        if chain:
            return compact_chain(chain, applicant_role=frappe.db.get_value("Employee", leave.employee, "designation"))
    return build_approval_chain(days=days, impact_level=analysis.get("risk_level"))


@frappe.whitelist()
def rerun(leave_application):
    leave = frappe.get_doc("Leave Application", leave_application)
    frappe.has_permission("Leave Application", "write", leave, throw=True)
    if leave.status != "Open":
        frappe.throw("Only Open Leave Applications can be analyzed.")

    frappe.enqueue(
        "workpulse.leave_impact.analyzer.run",
        queue="short",
        leave_application=leave.name,
        job_id=f"leave-impact-{leave.name}",
        deduplicate=True,
        enqueue_after_commit=True,
    )
    return {"queued": True}


def _can_view(leave):
    if not frappe.has_permission("Leave Application", "read", leave):
        return False
    if frappe.session.user == leave.leave_approver:
        return True
    return bool({"HR Manager", "System Manager"} & set(frappe.get_roles()))