"""Allocation and candidate-ranking logic for WorkPulse."""

from __future__ import annotations


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _skill_match(task_skills: dict[str, float], candidate_skills: dict[str, float]) -> float:
    if not task_skills:
        return 1.0

    ratios = []
    for skill, minimum_level in task_skills.items():
        current = float(candidate_skills.get(skill, 0.0))
        if minimum_level <= 0:
            continue
        ratios.append(min(current / minimum_level, 1.0))

    if not ratios:
        return 0.0
    return sum(ratios) / len(ratios)


def rank_candidates(
    *,
    task_skills: dict[str, float],
    candidates: list[dict],
    workload_ceiling_pct: float = 85.0,
    weights: dict[str, float] | None = None,
) -> list[dict]:
    """Return a ranked list of candidates for a task.

    Each candidate may include:
    - employee: unique id
    - current_workload_pct: current workload percentage
    - level_by_skill: dict[str, float]
    - history_score: float in [0, 1]
    - reliability_score: float in [0, 1]
    - available_hours: float
    - supports: optional dict[str, float] alias for skill levels
    """
    if weights is None:
        weights = {
            "skill": 0.40,
            "capacity": 0.25,
            "history": 0.20,
            "reliability": 0.15,
        }

    ranked = []
    for candidate in candidates:
        employee = candidate.get("employee")
        current_workload_pct = float(candidate.get("current_workload_pct", 0.0))
        if current_workload_pct > float(workload_ceiling_pct):
            continue

        levels = candidate.get("level_by_skill") or candidate.get("supports") or {}
        skill_match = _skill_match(task_skills, {str(key): float(value) for key, value in levels.items()})
        free_capacity = clamp(1.0 - (current_workload_pct / 100.0), 0.0, 1.0)
        history_score = float(candidate.get("history_score", 0.0))
        reliability_score = float(candidate.get("reliability_score", 0.0))

        score = (
            weights["skill"] * skill_match
            + weights["capacity"] * free_capacity
            + weights["history"] * clamp(history_score, 0.0, 1.0)
            + weights["reliability"] * clamp(reliability_score, 0.0, 1.0)
        )

        ranked.append(
            {
                "employee": employee,
                "score": round(score, 6),
                "skill_match": round(skill_match, 6),
                "free_capacity": round(free_capacity, 6),
                "history_score": round(clamp(history_score, 0.0, 1.0), 6),
                "reliability_score": round(clamp(reliability_score, 0.0, 1.0), 6),
                "workload_after_pct": round(current_workload_pct, 6),
            }
        )

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked
