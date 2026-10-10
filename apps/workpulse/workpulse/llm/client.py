"""Safety and validation helpers for LLM-backed features."""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROMPT_INJECTION_HINTS = (
    "ignore previous instructions",
    "ignore all instructions",
    "system prompt",
    "developer prompt",
    "reveal secrets",
    "override",
    "bypass",
    "you are now",
)


def detect_prompt_injection(text: str) -> bool:
    """Return True when the provided text looks like a prompt-injection attempt."""
    normalized = (text or "").lower()
    return any(hint in normalized for hint in PROMPT_INJECTION_HINTS)


def validate_output(payload: dict, *, required_fields: list[str] | None = None) -> bool:
    """Validate that the payload contains the required high-level fields."""
    if not isinstance(payload, dict):
        return False
    if not required_fields:
        return True
    return all(field in payload and payload[field] is not None for field in required_fields)


def get_provider_status(settings) -> dict:
    key_name = settings.llm_api_key_env or "WORKPULSE_LLM_API_KEY"
    return {
        "provider": settings.llm_provider or "OpenAI-compatible",
        "model": os.environ.get("WORKPULSE_LLM_MODEL") or settings.llm_model or "gpt-4o-mini",
        "endpoint": os.environ.get("WORKPULSE_LLM_ENDPOINT") or settings.llm_endpoint,
        "configured": bool(os.environ.get(key_name)),
        "key_env": key_name,
    }


def complete_chat(settings, messages: list[dict], *, timeout: int = 20) -> str:
    key_name = settings.llm_api_key_env or "WORKPULSE_LLM_API_KEY"
    api_key = os.environ.get(key_name)
    if not api_key:
        raise RuntimeError(f"LLM API key is not configured in {key_name}.")
    payload = json.dumps({
        "model": os.environ.get("WORKPULSE_LLM_MODEL") or settings.llm_model or "gpt-4o-mini",
        "messages": messages,
        "temperature": 0,
    }).encode()
    request = Request(
        os.environ.get("WORKPULSE_LLM_ENDPOINT") or settings.llm_endpoint,
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode())
    except (HTTPError, URLError, TimeoutError) as error:
        raise RuntimeError("The configured LLM provider request failed.") from error
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError("The LLM provider returned an invalid response.") from error
