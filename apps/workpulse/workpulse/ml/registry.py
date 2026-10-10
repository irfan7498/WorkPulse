"""Model registry helpers for versioned WorkPulse ML artifacts."""

from __future__ import annotations


_MODEL_STORE: dict[str, dict] = {}


def register_model_version(model_name: str, version: str, *, metrics: dict | None = None, is_active: bool = False) -> str:
    """Register a model version and return the version string."""
    _MODEL_STORE[model_name] = {
        "version": version,
        "metrics": metrics or {},
        "is_active": bool(is_active),
    }
    return version


def get_latest_model(model_name: str) -> dict:
    """Return the latest known model metadata for a given model name."""
    return dict(_MODEL_STORE.get(model_name, {}))
