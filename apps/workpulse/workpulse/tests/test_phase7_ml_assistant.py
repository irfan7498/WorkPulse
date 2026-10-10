from workpulse.llm.assistant import build_assistant_response
from workpulse.ml.registry import get_latest_model, register_model_version


def test_model_registry_tracks_versions_and_metrics():
    version = register_model_version("delay-model", "v1", metrics={"auc": 0.82, "brier": 0.19}, is_active=True)
    stored = get_latest_model("delay-model")
    assert version == "v1"
    assert stored["metrics"]["auc"] == 0.82
    assert stored["is_active"] is True


def test_assistant_response_uses_tool_calls_for_task_questions():
    response = build_assistant_response(
        "Who can take this task next week?",
        tools=["recommend_allocation", "get_employee_card"],
    )
    assert "recommend_allocation" in response
    assert "next week" in response.lower()
    assert "tool" in response.lower()
