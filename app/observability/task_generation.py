"""Safe metadata from task generation payload (no prompts/tasks)."""
from __future__ import annotations

from typing import Any


def metadata_from_task_payload(payload: dict[str, Any]) -> dict[str, Any]:
    warning_codes: list[str] = []
    for w in payload.get("_warnings", []):
        if isinstance(w, dict) and w.get("code"):
            warning_codes.append(str(w["code"]))

    used_fallback = bool(payload.get("_used_fallback"))
    blocked = bool(payload.get("_blocked"))
    had_error = bool(payload.get("_error"))

    if blocked:
        source = "blocked"
    elif used_fallback and had_error:
        source = "fallback_after_api_error"
    elif used_fallback:
        source = "fallback"
    else:
        source = "openai"

    return {
        "source": source,
        "blocked": blocked,
        "used_fallback": used_fallback,
        "had_api_error": had_error,
        "task_count": len(payload.get("tasks") or []),
        "topic_id": payload.get("topic_id"),
        "warning_codes": warning_codes,
        "has_padding": "fallback_padded_tasks" in warning_codes,
        "has_trimmed": "tasks_trimmed" in warning_codes,
        "has_dropped": "tasks_dropped" in warning_codes,
    }
