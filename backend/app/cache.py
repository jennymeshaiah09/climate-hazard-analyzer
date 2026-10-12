"""Process-local analysis cache used when MongoDB is unavailable."""

from __future__ import annotations

from typing import Any

_memory: dict[str, dict[str, Any]] = {}


def memory_get(cache_key: str) -> dict[str, Any] | None:
    value = _memory.get(cache_key)
    return dict(value) if value is not None else None


def memory_set(cache_key: str, result: dict[str, Any]) -> None:
    _memory[cache_key] = dict(result)
