"""Pure Python leave-impact scoring for WorkPulse."""

from __future__ import annotations


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def score_leave_impact(*, team_capacity_drop: float, critical_tasks: int, overlap: float, backup_coverage: float) -> float:
    """Compute leave-impact score on a 0..100 scale.

    Formula from the project plan:
        100 * (0.35 * team_capacity_drop + 0.30 * min(critical_tasks / 3, 1) + 0.20 * overlap + 0.15 * (1 - backup_coverage))
    """
    team_drop = clamp(float(team_capacity_drop), 0.0, 1.0)
    overlap_ratio = clamp(float(overlap), 0.0, 1.0)
    backup = clamp(float(backup_coverage), 0.0, 1.0)
    critical = min(float(critical_tasks) / 3.0, 1.0)

    score = (
        0.35 * team_drop
        + 0.30 * critical
        + 0.20 * overlap_ratio
        + 0.15 * (1.0 - backup)
    ) * 100.0
    return round(clamp(score, 0.0, 100.0), 3)


def classify_leave_impact(score: float) -> str:
    """Map a leave impact score to a level."""
    value = float(score)
    if value < 30:
        return "Low"
    if value < 60:
        return "Medium"
    return "High"
