"""Lightweight document hooks that keep workload data flags current."""

from __future__ import annotations

import json

import frappe

from workpulse.engines.workload import task_remaining_hours


def mark_task_health(doc, method=None) -> None:
    if not hasattr(doc, "wp_data_flags"):
        return
    settings = frappe.get_cached_doc("WorkPulse Settings")
    _, flags = task_remaining_hours(
        expected_time=doc.get("expected_time"),
        logged_hours=doc.get("actual_time"),
        fallback_hours=settings.default_task_hours or 8,
    )
    if not doc.get("exp_start_date") or not doc.get("exp_end_date"):
        flags.append("no_dates")
    if doc.get("status") in {"Completed", "Cancelled"}:
        flags = []
    doc.wp_data_flags = json.dumps(sorted(set(flags)))


def queue_task_snapshot(doc, method=None) -> None:
    if getattr(doc.flags, "in_patch", False):
        return
    frappe.enqueue(
        "workpulse.tasks.snapshots.nightly_workload",
        queue="short",
        job_id="workpulse-task-workload",
        deduplicate=True,
        enqueue_after_commit=True,
    )
