from workpulse.engines.recruitment import (
    calculate_gap_coverage,
    sanitize_candidate_profile,
    score_candidate,
)


def test_gap_coverage_uses_required_headcount_ratio():
    assert calculate_gap_coverage(required_headcount=4, current_headcount=2) == 0.5
    assert calculate_gap_coverage(required_headcount=0, current_headcount=2) == 1.0


def test_candidate_score_blends_all_subscores():
    score = score_candidate(
        skill_match=0.8,
        experience_match=0.9,
        project_similarity=0.7,
        availability=0.6,
        gap_coverage=0.5,
    )
    assert round(score, 4) == 0.73


def test_candidate_profile_strips_protected_attributes_before_scoring():
    profile = {
        "name": "Jane",
        "gender": "female",
        "age": 30,
        "religion": "Christian",
        "skills": ["Python", "Django"],
    }
    clean = sanitize_candidate_profile(profile)
    assert "name" not in clean
    assert "gender" not in clean
    assert "age" not in clean
    assert "religion" not in clean
    assert clean["skills"] == ["Python", "Django"]
