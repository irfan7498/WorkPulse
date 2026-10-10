"""Data-quality helpers for WorkPulse."""

from __future__ import annotations


def summarize_data_quality(tasks: list[dict]) -> dict[str, int]:
    """Summarize common data defects across a list of tasks.

    This is intentionally simple and pure so it can be unit-tested without a Frappe site.
    """
    summary = {
        "missing_estimate": 0,
        "missing_dates": 0,
        "missing_assignee": 0,
    }

    for task in tasks:
        if task.get("expected_time") in (None, "", 0):
            summary["missing_estimate"] += 1

        start_missing = task.get("exp_start_date") in (None, "")
        end_missing = task.get("exp_end_date") in (None, "")
        if start_missing or end_missing:
            summary["missing_dates"] += 1

        assignee = task.get("assigned_to", task.get("owner"))
        if assignee in (None, "", False, []):
            summary["missing_assignee"] += 1

    return summary
