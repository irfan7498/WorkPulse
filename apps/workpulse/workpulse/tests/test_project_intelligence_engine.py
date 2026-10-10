from workpulse.engines.bottleneck import detect_cycle, critical_path_length
from workpulse.engines.progress import calculate_spi, calculate_weighted_progress
from workpulse.engines.risk import calculate_project_risk


def test_weighted_progress_rolls_up_task_completion():
    progress = calculate_weighted_progress(
        tasks=[
            {"weight": 10, "progress": 100},
            {"weight": 20, "progress": 50},
        ]
    )
    assert round(progress, 4) == 0.6667


def test_spi_compares_progress_to_plan():
    assert calculate_spi(progress=0.8, planned_progress=0.5) == 1.6
    assert calculate_spi(progress=0.5, planned_progress=0.8) == 0.625


def test_cycle_detection_flags_loops_in_task_dependencies():
    graph = {"A": ["B"], "B": ["A"]}
    assert detect_cycle(graph) is True


def test_critical_path_uses_total_remaining_effort():
    graph = {"A": ["B"], "B": ["C"], "C": []}
    weights = {"A": 10, "B": 20, "C": 30}
    assert critical_path_length(graph, weights) == 60


def test_rule_based_project_risk_uses_all_components():
    risk = calculate_project_risk(
        schedule_slip=0.20,
        blocked_share=0.10,
        overdue_share=0.20,
        team_overload=0.30,
        unassigned_share=0.15,
    )
    assert round(risk, 2) == 18.5
