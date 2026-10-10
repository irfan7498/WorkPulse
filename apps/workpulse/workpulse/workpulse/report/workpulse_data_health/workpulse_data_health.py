import frappe
from frappe import _

from workpulse.engines.data_health import summarize_data_quality


def execute(filters=None):
	if not frappe.has_permission("Task", "read"):
		frappe.throw(_("You do not have permission to view Task data."), frappe.PermissionError)

	tasks = _get_all("Task", ["name", "expected_time", "exp_start_date", "exp_end_date"])
	assigned_task_names = {
		todo.reference_name
		for todo in _get_all(
			"ToDo",
			["reference_name"],
			{"reference_type": "Task", "status": ["in", ["Open", "Working"]]},
		)
	}
	for task in tasks:
		task["assigned_to"] = task["name"] in assigned_task_names

	summary = summarize_data_quality(tasks)
	columns = [
		{"label": _("Data Issue"), "fieldname": "issue", "fieldtype": "Data", "width": 240},
		{"label": _("Affected Tasks"), "fieldname": "count", "fieldtype": "Int", "width": 140},
	]
	data = [
		{"issue": label, "count": summary[key]}
		for key, label in (
			("missing_estimate", _("Missing estimate")),
			("missing_dates", _("Missing start or end date")),
			("missing_assignee", _("No active assignee")),
		)
	]
	return columns, data


def _get_all(doctype, fields, filters=None):
	rows = []
	start = 0
	while True:
		batch = frappe.get_list(
			doctype,
			fields=fields,
			filters=filters,
			limit_start=start,
			limit_page_length=500,
		)
		rows.extend(batch)
		if len(batch) < 500:
			return rows
		start += len(batch)