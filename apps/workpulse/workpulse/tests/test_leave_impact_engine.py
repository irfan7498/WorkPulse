from workpulse.engines.leave_impact import classify_leave_impact, score_leave_impact


def test_empty_leave_has_low_impact():
    score = score_leave_impact(
        team_capacity_drop=0.0,
        critical_tasks=0,
        overlap=0.0,
        backup_coverage=1.0,
    )
    assert score == 0.0
    assert classify_leave_impact(score) == "Low"


def test_critical_tasks_and_capacity_drop_raise_impact():
    score = score_leave_impact(
        team_capacity_drop=0.5,
        critical_tasks=3,
        overlap=0.25,
        backup_coverage=0.4,
    )
    assert 60 <= score <= 80
    assert classify_leave_impact(score) == "High"


def test_medium_leave_is_medium_risk():
    score = score_leave_impact(
        team_capacity_drop=0.3,
        critical_tasks=1,
        overlap=0.2,
        backup_coverage=0.5,
    )
    assert 30 <= score <= 60
    assert classify_leave_impact(score) == "Medium"
