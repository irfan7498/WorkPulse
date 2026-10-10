"""Tool-call based assistant helpers for WorkPulse."""

from __future__ import annotations


def build_assistant_response(
    question: str, *, tools: list[str] | None = None, context: list[str] | None = None
) -> str:
    """Return a deterministic assistant-style response built from allowed tool calls."""
    question_lower = (question or "").lower()
    allowed = list(tools or [])
    tool_text = ", ".join(allowed) if allowed else "read-only APIs"
    context_text = "; ".join(context or []) or "No additional facts were available."
    if "next week" in question_lower:
        window = "next week"
    elif "today" in question_lower:
        window = "today"
    else:
        window = "the requested timeframe"

    return (
        f"I should use the available tools ({tool_text}) to answer: '{question}'. "
        f"For this request, I would call the planner for {window}. Visible facts: {context_text}."
    )
