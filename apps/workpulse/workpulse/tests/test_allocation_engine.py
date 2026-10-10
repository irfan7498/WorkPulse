from workpulse.engines.allocation import rank_candidates


def test_allocation_filters_out_overloaded_candidates():
    candidates = [
        {
            "employee": "A",
            "current_workload_pct": 91,
            "level_by_skill": {"python": 5.0},
            "history_score": 0.9,
            "reliability_score": 0.8,
            "available_hours": 10,
            "supports": {"python": 5.0},
        },
        {
            "employee": "B",
            "current_workload_pct": 52,
            "level_by_skill": {"python": 4.0},
            "history_score": 0.8,
            "reliability_score": 0.7,
            "available_hours": 10,
            "supports": {"python": 4.0},
        },
    ]

    ranked = rank_candidates(
        task_skills={"python": 4.0},
        candidates=candidates,
        workload_ceiling_pct=80,
    )

    assert [entry["employee"] for entry in ranked] == ["B"]


def test_allocation_ranks_best_skill_and_capacity_match():
    candidates = [
        {
            "employee": "A",
            "current_workload_pct": 91,
            "level_by_skill": {"python": 5.0, "postgres": 4.0},
            "history_score": 0.9,
            "reliability_score": 0.8,
            "available_hours": 10,
            "supports": {"python": 5.0, "postgres": 4.0},
        },
        {
            "employee": "B",
            "current_workload_pct": 52,
            "level_by_skill": {"python": 4.0, "postgres": 3.0},
            "history_score": 0.45,
            "reliability_score": 0.35,
            "available_hours": 10,
            "supports": {"python": 4.0, "postgres": 3.0},
        },
        {
            "employee": "C",
            "current_workload_pct": 67,
            "level_by_skill": {"python": 5.0, "postgres": 5.0},
            "history_score": 0.8,
            "reliability_score": 0.7,
            "available_hours": 10,
            "supports": {"python": 5.0, "postgres": 5.0},
        },
    ]

    ranked = rank_candidates(
        task_skills={"python": 4.0, "postgres": 4.0},
        candidates=candidates,
        workload_ceiling_pct=85,
    )

    assert ranked[0]["employee"] == "C"
    assert ranked[0]["score"] >= ranked[1]["score"]


def test_allocation_reports_reason_when_filtered_out():
    ranked = rank_candidates(
        task_skills={"python": 4.5},
        candidates=[
            {
                "employee": "A",
                "current_workload_pct": 95,
                "level_by_skill": {"python": 5.0},
                "history_score": 0.9,
                "reliability_score": 0.8,
                "available_hours": 10,
                "supports": {"python": 5.0},
            }
        ],
        workload_ceiling_pct=80,
    )

    assert ranked == []
