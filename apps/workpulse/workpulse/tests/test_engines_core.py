from math import isclose

from workpulse.engines.capacity import calculate_capacity
from workpulse.engines.workload import calculate_workload_pct, calculate_remaining_hours


def test_capacity_clamps_at_zero():
    capacity = calculate_capacity(
        working_days=3,
        leave_days=5,
        daily_hours=8,
        meeting_overhead_pct=10,
        project_allocation_share=1.0,
    )
    assert capacity == 0.0


def test_capacity_uses_allocation_share():
    capacity = calculate_capacity(
        working_days=5,
        leave_days=1,
        daily_hours=8,
        meeting_overhead_pct=10,
        project_allocation_share=0.5,
    )
    assert isclose(capacity, 14.4, abs_tol=1e-9)

    full_capacity = calculate_capacity(
        working_days=5,
        leave_days=1,
        daily_hours=8,
        meeting_overhead_pct=10,
        project_allocation_share=1.0,
    )
    assert isclose(full_capacity, 28.8, abs_tol=1e-9)


def test_remaining_hours_does_not_go_negative():
    assert calculate_remaining_hours(expected_time=10, logged_hours=12) == 0.0


def test_workload_percentage_uses_capacity_ratio():
    workload_pct = calculate_workload_pct(planned_hours=20, capacity_hours=40)
    assert isclose(workload_pct, 50.0, abs_tol=1e-9)


def test_workload_handles_zero_capacity():
    workload_pct = calculate_workload_pct(planned_hours=20, capacity_hours=0)
    assert workload_pct == 999.0
