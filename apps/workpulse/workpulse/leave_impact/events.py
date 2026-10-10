import frappe


def on_leave_saved(doc, method=None):
    if doc.status != "Open":
        _mark_stale(doc)
        return

    if not frappe.db.exists("DocType", "WorkPulse Settings") or not frappe.db.get_single_value(
        "WorkPulse Settings", "enabled"
    ):
        return

    if not doc.is_new():
        before = doc.get_doc_before_save()
        if before and _same_inputs(before, doc) and frappe.db.exists(
            "Leave Impact Analysis", {"leave_application": doc.name}
        ):
            return

    frappe.enqueue(
        "workpulse.leave_impact.analyzer.run",
        queue="short",
        leave_application=doc.name,
        job_id=f"leave-impact-{doc.name}",
        deduplicate=True,
        enqueue_after_commit=True,
    )


def _same_inputs(before, current):
    fields = ("employee", "from_date", "to_date", "leave_type", "department")
    return all(before.get(field) == current.get(field) for field in fields)


def _mark_stale(doc):
    analysis_name = frappe.db.get_value(
        "Leave Impact Analysis", {"leave_application": doc.name}, "name"
    )
    if analysis_name:
        frappe.db.set_value(
            "Leave Impact Analysis",
            analysis_name,
            {"status": "Stale", "error_message": f"Leave status is {doc.status or 'not Open'}"},
            update_modified=False,
        )