"""Workload calculations for WorkPulse.

The module deliberately contains no Frappe imports. Adapters turn ERPNext rows into
the small dictionaries accepted here, which keeps forecast behavior testable.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta


def calculate_remaining_hours(*, expected_time: float, logged_hours: float) -> float:
    """Return remaining hours for an assignment, never below zero."""
    return max(expected_time - logged_hours, 0.0)


def calculate_workload_pct(*, planned_hours: float, capacity_hours: float) -> float:
    """Return workload percent relative to employee capacity.

    The rule from the project plan says: if capacity_hours is zero and planned_hours > 0,
    return 999 to flag a no-capacity condition.
    """
    if capacity_hours == 0:
        return 999.0 if planned_hours > 0 else 0.0
    return max((planned_hours / capacity_hours) * 100.0, 0.0)


def task_remaining_hours(
    *,
    expected_time: float | None,
    logged_hours: float = 0.0,
    fallback_hours: float = 8.0,
) -> tuple[float, list[str]]:
    """Return residual effort and data flags for one open task."""
    flags: list[str] = []
    estimate = float(expected_time or 0)
    if estimate <= 0:
        estimate = max(float(fallback_hours), 0.0)
        flags.append("no_estimate")
    logged = max(float(logged_hours or 0), 0.0)
    if logged > estimate:
        flags.append("over_budget")
        return max(estimate * 0.25, 0.0), flags
    return max(estimate - logged, 0.0), flags


def task_week_allocation(
    *,
    task: dict,
    week_start: date,
    fallback_hours: float = 8.0,
    today: date | None = None,
) -> tuple[float, list[str]]:
    """Allocate a task's remaining hours into a week using working-day overlap."""
    current = today or date.today()
    remaining, flags = task_remaining_hours(
        expected_time=task.get("expected_time"),
        logged_hours=task.get("logged_hours", task.get("actual_time", 0)),
        fallback_hours=fallback_hours,
    )
    start = _as_date(task.get("exp_start_date")) or current
    end = _as_date(task.get("exp_end_date"))
    if not end:
        end = start + timedelta(days=7)
        flags.append("no_dates")
    if end < current:
        start, end = week_start, week_start + timedelta(days=6)
        flags.append("overdue")
    window_days = _weekdays(start, end)
    overlap_days = _weekdays(max(start, week_start), min(end, week_start + timedelta(days=6)))
    if not window_days:
        return 0.0, flags
    assignees = max(int(task.get("assignee_count") or 1), 1)
    return remaining * overlap_days / window_days / assignees, flags


def _as_date(value: date | str | None) -> date | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    return value if isinstance(value, date) else date.fromisoformat(str(value)[:10])


def _weekdays(start: date, end: date) -> int:
    if end < start:
        return 0
    return sum((start + timedelta(days=offset)).weekday() < 5 for offset in range((end - start).days + 1))
