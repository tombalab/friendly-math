"""Structured observability events for worksheet generation (P2.4)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

# Nazwy zdarzeń (stabilne dla logów i przyszłego eksportu).
EVENT_REQUEST_START = "request_start"
EVENT_TOPIC_RESOLVED = "topic_resolved"
EVENT_PROFILE_RESOLVED = "profile_resolved"
EVENT_GENERATION_BLOCKED = "generation_blocked"
EVENT_MODEL_CALL = "model_call"
EVENT_FALLBACK_PADDING = "fallback_padding"
EVENT_TASK_VALIDATION = "task_validation"
EVENT_LAYOUT_RESOLVED = "layout_resolved"
EVENT_ANSWER_COVERAGE = "answer_coverage"
EVENT_IMAGE_COVERAGE = "image_coverage"
EVENT_PDF_BUILT = "pdf_built"
EVENT_GENERATION_COMPLETE = "generation_complete"
EVENT_DOWNLOAD = "download"

_SENSITIVE_KEYS = frozenset(
    {
        "optional_context",
        "prompt",
        "messages",
        "tasks",
        "task_text",
        "notes",
        "student_data",
    }
)


def new_request_id() -> str:
    return str(uuid4())


def redact_event_data(data: dict[str, Any]) -> dict[str, Any]:
    """Usuwa pola mogące zawierać pełne prompty, notatki lub treść zadań."""
    out: dict[str, Any] = {}
    for key, value in data.items():
        if key in _SENSITIVE_KEYS:
            continue
        if key == "api_error" and isinstance(value, str):
            out[key] = value[:120] + ("…" if len(value) > 120 else "")
            continue
        out[key] = value
    return out


@dataclass(frozen=True)
class WorksheetEvent:
    request_id: str
    event: str
    data: dict[str, Any] = field(default_factory=dict)
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "event": self.event,
            "ts": self.ts,
            "data": self.data,
        }

    def to_json_line(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class GenerationTrace:
    """Zbiera zdarzenia jednej generacji; `request_id` łączy ostrzeżenia i logi."""

    request_id: str
    events: list[WorksheetEvent] = field(default_factory=list)
    log_to_stdout: bool = True

    @classmethod
    def start(cls, *, log_to_stdout: bool | None = None) -> GenerationTrace:
        from app.observability.sink import is_observability_enabled

        enabled = is_observability_enabled() if log_to_stdout is None else log_to_stdout
        return cls(request_id=new_request_id(), log_to_stdout=enabled)

    def emit(self, event: str, **data: Any) -> WorksheetEvent:
        safe = redact_event_data(data)
        ev = WorksheetEvent(request_id=self.request_id, event=event, data=safe)
        self.events.append(ev)
        if self.log_to_stdout:
            from app.observability.sink import emit_to_log

            emit_to_log(ev)
        return ev
