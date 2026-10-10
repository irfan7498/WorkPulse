"""Pure Python recruitment scoring and shortlisting logic for WorkPulse."""

from __future__ import annotations


PROTECTED_FIELDS = {
    "name",
    "gender",
    "age",
    "photo",
    "marital_status",
    "religion",
    "nationality",
    "phone",
    "email",
}


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def sanitize_candidate_profile(profile: dict) -> dict:
    """Strip protected attributes before any scoring or ranking."""
    return {key: value for key, value in profile.items() if key.lower() not in PROTECTED_FIELDS}


def calculate_skill_match(*, required_level: float, candidate_level: float) -> float:
    """Return normalized skill coverage relative to a required level."""
    if required_level <= 0:
        return 1.0
    return clamp(float(candidate_level) / float(required_level), 0.0, 1.0)


def calculate_gap_coverage(*, required_headcount: float, current_headcount: float) -> float:
    """Return coverage ratio of the team requirement filled by the candidate."""
    if required_headcount <= 0:
        return 1.0
    return clamp(float(current_headcount) / float(required_headcount), 0.0, 1.0)


def score_candidate(*, skill_match: float, experience_match: float, project_similarity: float, availability: float, gap_coverage: float) -> float:
    """Compute a deterministic shortlist score on a 0..1 scale."""
    total = (
        0.35 * clamp(float(skill_match), 0.0, 1.0)
        + 0.20 * clamp(float(experience_match), 0.0, 1.0)
        + 0.15 * clamp(float(project_similarity), 0.0, 1.0)
        + 0.15 * clamp(float(availability), 0.0, 1.0)
        + 0.15 * clamp(float(gap_coverage), 0.0, 1.0)
    )
    return round(total, 4)
