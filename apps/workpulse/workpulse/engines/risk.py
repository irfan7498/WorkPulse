"""Pure Python rule-based project risk calculations for WorkPulse."""

from __future__ import annotations


def calculate_project_risk(
    *,
    schedule_slip: float,
    blocked_share: float,
    overdue_share: float,
    team_overload: float,
    unassigned_share: float,
) -> float:
    """Compute the fallback rule-based project risk score on a 0..100 scale."""
    risk = (
        0.30 * float(schedule_slip)
        + 0.25 * float(blocked_share)
        + 0.20 * float(overdue_share)
        + 0.15 * float(team_overload)
        + 0.10 * float(unassigned_share)
    ) * 100.0
    return round(max(0.0, min(risk, 100.0)), 3)
