"""Capacity calculations for WorkPulse."""


def calculate_capacity(
    *,
    working_days: float,
    leave_days: float,
    daily_hours: float,
    meeting_overhead_pct: float,
    project_allocation_share: float,
) -> float:
    """Return employee capacity in hours for a given period.

    The formula follows the WorkPulse plan:
    ((working_days - leave_days) * daily_hours * (1 - meeting_overhead_pct/100) * allocation_share)
    with negative values clamped to zero.
    """
    effective_days = max(working_days - leave_days, 0.0)
    effective_hours = daily_hours * (1 - (meeting_overhead_pct / 100.0))
    capacity = effective_days * effective_hours * max(project_allocation_share, 0.0)
    return max(capacity, 0.0)
