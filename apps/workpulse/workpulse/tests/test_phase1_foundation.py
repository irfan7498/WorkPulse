from workpulse.engines.data_health import summarize_data_quality
from workpulse.engines.skills import merge_skill_level


def test_merge_skill_uses_history_when_available():
    result = merge_skill_level(declared=3.0, resume_level=2.0, history_level=4.0, history_samples=6)
    assert result["level"] > 3.0
    assert 0.0 <= result["confidence"] <= 1.0


def test_merge_skill_caps_resume_only_claims():
    result = merge_skill_level(declared=1.0, resume_level=4.5, history_level=1.0, history_samples=0)
    assert result["level"] <= 3.0
    assert result["confidence"] <= 0.4


def test_data_quality_summary_counts_missing_fields():
    summary = summarize_data_quality(
        tasks=[
            {"name": "T1", "expected_time": None, "exp_start_date": None, "exp_end_date": None, "owner": None},
            {"name": "T2", "expected_time": 6, "exp_start_date": "2026-10-01", "exp_end_date": None, "owner": "E1"},
            {"name": "T3", "expected_time": 6, "exp_start_date": None, "exp_end_date": "2026-10-05", "owner": None},
        ]
    )
    assert summary["missing_estimate"] == 1
    assert summary["missing_dates"] == 3
    assert summary["missing_assignee"] == 2


def test_data_quality_uses_assignment_not_task_creator():
    summary = summarize_data_quality(
        tasks=[
            {"expected_time": 0, "exp_start_date": "2026-10-01", "exp_end_date": "2026-10-02", "owner": "creator@example.com", "assigned_to": False},
            {"expected_time": 4, "exp_start_date": "2026-10-01", "exp_end_date": "2026-10-02", "owner": "creator@example.com", "assigned_to": True},
        ]
    )
    assert summary["missing_estimate"] == 1
    assert summary["missing_assignee"] == 1
