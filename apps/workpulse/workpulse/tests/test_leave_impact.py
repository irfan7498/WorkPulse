import frappe

from workpulse.leave_impact.analyzer import rules_recommendation, score_risk


def _evidence(**overrides):
    evidence = {
        "impacted_tasks": [],
        "teammates_on_leave": [],
        "team_size": 0,
        "total_leave_days": 3,
    }
    evidence.update(overrides)
    return evidence


def test_empty_evidence_is_low_risk():
    score, level = score_risk(_evidence())

    assert score == 0
    assert level == "Low"
    assert rules_recommendation({**_evidence(), "risk_level": level})["suggested_action"] == "Approve"


def test_urgent_overdue_task_is_medium_risk():
    score, level = score_risk(
        _evidence(
            impacted_tasks=[{"priority": "Urgent", "reason": "overdue"}],
        )
    )

    assert score == 30
    assert level == "Medium"


def test_team_absence_can_raise_high_risk():
    score, level = score_risk(
        _evidence(
            impacted_tasks=[{"priority": "Urgent", "reason": "overdue"}],
            teammates_on_leave=[{"employee_name": "Teammate"}],
            team_size=4,
        )
    )

    assert score == 60
    assert level == "High"
    assert rules_recommendation({**_evidence(), "risk_level": level})["suggested_action"] == "Defer"