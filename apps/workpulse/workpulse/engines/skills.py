"""Skill profile calculations for WorkPulse."""

from __future__ import annotations


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def merge_skill_level(*, declared: float, resume_level: float, history_level: float, history_samples: int) -> dict[str, float]:
    """Merge declared, resume, and historical evidence into a deterministic skill score."""
    declared_val = float(declared or 0.0)
    resume_val = float(resume_level or 0.0)
    history_val = float(history_level or 0.0)

    if history_samples >= 5:
        weighted = (0.3 * declared_val) + (0.2 * resume_val) + (0.5 * history_val)
        confidence = clamp((history_samples / 10.0) * 0.8, 0.0, 1.0)
    elif resume_val and history_val == 0:
        weighted = (0.3 * declared_val) + (0.2 * resume_val)
        confidence = 0.4
    else:
        available = [value for value in (declared_val, resume_val, history_val) if value > 0]
        weighted = sum(value * (0.5 / len(available) if available else 0.5) for value in available)
        confidence = clamp((len(available) / 3.0) * 0.6, 0.0, 0.6)

    level = clamp(weighted, 1.0, 5.0)
    if resume_val > 0 and history_samples == 0 and level > 3.0:
        level = min(level, 3.0)
        confidence = min(confidence, 0.4)
    elif resume_val > 0 and history_samples == 0:
        confidence = min(confidence, 0.4)
    return {"level": round(level, 3), "confidence": round(min(max(confidence, 0.0), 1.0), 3)}
