"""Golden scenario registry for the WorkPulse seed data."""

PLANTED_SCENARIOS = {
    "S1": "Rahul workload overload scenario",
    "S2": "Low workload benchmark for allocation ranking",
    "S3": "Allocation ceiling and ranking under pressure",
    "S4": "Weighted progress versus naive progress",
    "S5": "High-risk leave approval chain",
    "S6": "Team overlap on leave detection",
    "S7": "Critical path bottleneck and dependency chain",
    "S8": "Resume-only skill without history is capped",
    "S9": "Domain project history boosts project similarity",
    "S10": "Dependency cycle error handling",
    "S11": "60/40 team split capacity calculation",
    "S12": "Resume prompt injection is ignored",
    "S13": "Unassigned task share is reflected in risk",
    "S14": "Half-day leave with holiday capacity reduction",
    "S15": "Estimation error history and reliability impact",
    "S16": "Protected-field swapping does not affect score",
}

ALL_SCENARIO_IDS = tuple(sorted(PLANTED_SCENARIOS))
