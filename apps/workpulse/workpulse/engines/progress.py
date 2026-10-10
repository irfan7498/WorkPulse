"""Pure Python project-progress calculations for WorkPulse."""

from __future__ import annotations


def calculate_weighted_progress(*, tasks: list[dict] | None = None, weights: list[float] | None = None, progress_values: list[float] | None = None) -> float:
    """Return weighted task completion as a fraction from 0..1.

    Accepts either a list of task dicts with ``weight`` and ``progress`` keys,
    or explicit numeric lists for lightweight tests.
    """
    if tasks is not None:
        total_weight = 0.0
        weighted_total = 0.0
        for task in tasks:
            weight = float(task.get("weight", 0.0))
            completion = float(task.get("progress", 0.0)) / 100.0
            total_weight += weight
            weighted_total += weight * completion
        if total_weight == 0:
            return 0.0
        return weighted_total / total_weight

    if weights is None or progress_values is None:
        return 0.0

    total_weight = sum(float(w) for w in weights)
    if total_weight == 0:
        return 0.0
    return sum(float(w) * float(p) / 100.0 for w, p in zip(weights, progress_values)) / total_weight


def calculate_spi(*, progress: float, planned_progress: float) -> float:
    """Return the schedule performance index as progress / planned_progress."""
    if planned_progress == 0:
        return 1.0 if progress > 0 else 0.0
    return float(progress) / float(planned_progress)
