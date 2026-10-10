"""Shared dataclasses for WorkPulse engine logic."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EmployeeSkillEvidence:
    declared: float | None = None
    resume_level: float | None = None
    history_level: float | None = None
    history_samples: int = 0


@dataclass
class TaskDataHealth:
    name: str
    expected_time: float | None = None
    exp_start_date: str | None = None
    exp_end_date: str | None = None
    owner: str | None = None
