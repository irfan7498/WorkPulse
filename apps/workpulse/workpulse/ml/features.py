"""Feature-building utilities for project delay prediction."""

from __future__ import annotations


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def build_delay_features(
    *,
    spi: float,
    blocked_share: float,
    overdue_share: float,
    team_overload: float,
    critical_path_length: float,
    leave_days_ahead: float,
    velocity_trend: float,
    past_delay_rate: float,
) -> dict[str, float]:
    """Build a normalized feature dictionary for delay risk prediction."""
    schedule_slip = max(0.0, 1.0 - float(spi))
    return {
        "spi": float(spi),
        "schedule_slip": round(clamp(schedule_slip, 0.0, 1.0), 3),
        "blocked_share": round(clamp(float(blocked_share), 0.0, 1.0), 3),
        "overdue_share": round(clamp(float(overdue_share), 0.0, 1.0), 3),
        "team_overload": round(clamp(float(team_overload), 0.0, 1.0), 3),
        "critical_path_length": float(critical_path_length),
        "leave_days_ahead": float(leave_days_ahead),
        "velocity_trend": float(velocity_trend),
        "past_delay_rate": round(clamp(float(past_delay_rate), 0.0, 1.0), 3),
    }


def predict_delay_probability(features: dict[str, float]) -> float:
    """Return a deterministic delay probability in the 0..1 range."""
    schedule_slip = clamp(float(features.get("schedule_slip", 0.0)), 0.0, 1.0)
    blocked_share = clamp(float(features.get("blocked_share", 0.0)), 0.0, 1.0)
    overdue_share = clamp(float(features.get("overdue_share", 0.0)), 0.0, 1.0)
    team_overload = clamp(float(features.get("team_overload", 0.0)), 0.0, 1.0)
    past_delay_rate = clamp(float(features.get("past_delay_rate", 0.0)), 0.0, 1.0)
    critical_pressure = clamp(float(features.get("critical_path_length", 0.0)) / 25.0, 0.0, 1.0)
    leave_pressure = clamp(float(features.get("leave_days_ahead", 0.0)) / 10.0, 0.0, 1.0)
    velocity = clamp(abs(float(features.get("velocity_trend", 0.0))), 0.0, 1.0)

    score = (
        0.35 * schedule_slip
        + 0.25 * blocked_share
        + 0.20 * overdue_share
        + 0.10 * team_overload
        + 0.05 * critical_pressure
        + 0.03 * leave_pressure
        + 0.02 * past_delay_rate
        + 0.02 * velocity
    )
    return round(clamp(score, 0.0, 1.0), 4)
