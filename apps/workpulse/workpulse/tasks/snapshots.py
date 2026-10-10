"""Background workload snapshot generation."""

from __future__ import annotations

import frappe
from frappe.utils import now_datetime

from workpulse.adapters.workload import build_week_snapshots


def nightly_workload() -> int:
    """Recompute the current-week snapshot for every readable active employee."""
    rows = build_week_snapshots()
    for row in rows:
        name = frappe.db.get_value(
            "WP Workload Snapshot",
            {"employee": row["employee"], "week_start": row["week_start"]},
            "name",
        )
        snapshot = frappe.get_doc("WP Workload Snapshot", name) if name else frappe.new_doc("WP Workload Snapshot")
        snapshot.update(
            {
                key: value
                for key, value in {
                    **row,
                    "computed_at": now_datetime(),
                    "engine_version": "rules-1",
                }.items()
                if key != "flags"
            }
        )
        snapshot.save(ignore_permissions=True)
        frappe.db.set_value(
            "WP Workload Snapshot",
            snapshot.name,
            "flags",
            frappe.as_json(row["flags"]),
            update_modified=False,
        )
    return len(rows)


def enqueue_nightly_workload() -> None:
    frappe.enqueue(
        "workpulse.tasks.snapshots.nightly_workload",
        queue="long",
        job_id="workpulse-nightly-workload",
        deduplicate=True,
        enqueue_after_commit=True,
    )
