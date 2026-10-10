import frappe


@frappe.whitelist()
def list_snapshots(risk_level=None, limit=20):
    filters = {"risk_level": risk_level} if risk_level else {}
    return frappe.get_all(
        "WP Project Snapshot",
        filters=filters,
        fields=[
            "project", "date", "weighted_progress", "planned_progress", "spi",
            "risk_score", "risk_level", "bottlenecks", "delay_probability",
        ],
        order_by="date desc, risk_score desc",
        limit_page_length=min(int(limit), 100),
    )


@frappe.whitelist()
def get_snapshot(project: str) -> dict | None:
    if not frappe.has_permission("Project", "read", project):
        frappe.throw("You do not have permission to view this project.", frappe.PermissionError)
    return frappe.db.get_value(
        "WP Project Snapshot",
        {"project": project},
        ["date", "weighted_progress", "planned_progress", "spi", "risk_score", "risk_level", "bottlenecks", "top_factors"],
        order_by="date desc",
        as_dict=True,
    )
