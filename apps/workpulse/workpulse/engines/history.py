"""History-based scoring helpers for WorkPulse allocation and skill evidence."""

from __future__ import annotations


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def score_employee_history(*, on_time_rate: float, recency_days: list[int] | None = None, task_count: int = 0) -> float:
    """Return a normalized history score between 0 and 1.

    The score rewards recent, consistent delivery and penalizes stale or inconsistent work.
    """
    rate = clamp(float(on_time_rate), 0.0, 1.0)
    days = recency_days or []
    if not days:
        base = rate
    else:
        weights = []
        for age in days:
            age = max(age, 0)
            weight = 1.0 / (1.0 + (age / 90.0))
            weights.append(weight)
        avg_weight = sum(weights) / len(weights)
        base = (0.7 * rate) + (0.3 * avg_weight)

    if task_count > 0:
        volume_bonus = clamp(task_count / 20.0, 0.0, 0.2)
        base = clamp(base + volume_bonus, 0.0, 1.0)

    return round(clamp(base, 0.0, 1.0), 6)


def estimate_reliability(*, on_time_rate: float, mean_estimation_error: float) -> float:
    """Return a reliability estimate from delivery consistency and estimate bias."""
    rate = clamp(float(on_time_rate), 0.0, 1.0)
    error = abs(float(mean_estimation_error))
    reliability = rate * (1.0 - clamp(error, 0.0, 1.0))
    return round(clamp(reliability, 0.0, 1.0), 6)
