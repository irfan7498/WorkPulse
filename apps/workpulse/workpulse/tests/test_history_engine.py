from workpulse.engines.history import estimate_reliability, score_employee_history


def test_history_score_rewards_recent_high_performance():
    score = score_employee_history(on_time_rate=0.9, recency_days=[10, 30, 120], task_count=3)
    assert 0.7 <= score <= 1.0


def test_history_score_reduces_for_inconsistent_delivery():
    score = score_employee_history(on_time_rate=0.6, recency_days=[400, 500], task_count=2)
    assert score < 0.7


def test_estimate_reliability_decreases_with_bias():
    assert estimate_reliability(on_time_rate=0.9, mean_estimation_error=0.0) == 0.9
    assert estimate_reliability(on_time_rate=0.9, mean_estimation_error=0.4) < 0.6
