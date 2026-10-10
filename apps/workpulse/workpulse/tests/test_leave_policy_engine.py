from workpulse.engines.leave_policy import build_approval_chain, compact_chain


def test_short_low_risk_leave_requires_team_lead():
    chain = build_approval_chain(days=1, impact_level="Low")
    assert chain == ["Team Lead"]


def test_medium_leave_uses_team_lead_then_project_manager():
    chain = build_approval_chain(days=3, impact_level="Medium")
    assert chain == ["Team Lead", "Project Manager"]


def test_high_leave_or_long_leave_includes_hr():
    chain = build_approval_chain(days=7, impact_level="High")
    assert chain == ["Team Lead", "Project Manager", "HR"]


def test_self_approval_is_removed_from_chain():
    chain = compact_chain(["Team Lead", "Project Manager", "HR"], applicant_role="Project Manager")
    assert chain == ["Team Lead", "HR"]
