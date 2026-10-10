"""Pure Python approval-chain logic for leave-impact policy decisions."""

from __future__ import annotations


def build_approval_chain(*, days: float, impact_level: str) -> list[str]:
    """Return the approver chain for a leave application.

    Rules from the project plan:
    - <= 1 day and Low => [Team Lead]
    - 2..5 days or Medium => [Team Lead, Project Manager]
    - > 5 days or High => [Team Lead, Project Manager, HR]
    """
    impact = (impact_level or "Low").title()
    days_value = float(days or 0.0)

    if impact == "High" or days_value > 5:
        return ["Team Lead", "Project Manager", "HR"]
    if impact == "Medium" or 2 <= days_value <= 5:
        return ["Team Lead", "Project Manager"]
    return ["Team Lead"]


def compact_chain(chain: list[str], *, applicant_role: str | None = None) -> list[str]:
    """Remove self-approval loops and keep only valid approvers."""
    if not chain:
        return []

    normalized = [step for step in chain if step and step.strip()]
    if not applicant_role:
        return normalized

    applicant = applicant_role.strip()
    return [step for step in normalized if step != applicant]
