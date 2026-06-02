"""Serializable history metadata (P2.5)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class HistoryEntryMeta:
    """Metadane karty — bez treści zadań i bez danych osobowych uczniów."""

    request_id: str
    created_at: str
    grade: int
    topic_label: str
    topic_id: str
    profile_id: str
    profile_label: str
    number_of_tasks: int
    success: bool
    blocked: bool
    used_fallback: bool
    warning_count: int
    warning_codes: list[str] = field(default_factory=list)
    answers: dict[str, Any] = field(default_factory=dict)
    images: dict[str, Any] = field(default_factory=dict)
    worksheet_label: str | None = None
    pdf_relative: str = "worksheet.pdf"

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> HistoryEntryMeta:
        return cls(
            request_id=str(raw["request_id"]),
            created_at=str(raw["created_at"]),
            grade=int(raw["grade"]),
            topic_label=str(raw["topic_label"]),
            topic_id=str(raw.get("topic_id", "")),
            profile_id=str(raw["profile_id"]),
            profile_label=str(raw.get("profile_label", raw["profile_id"])),
            number_of_tasks=int(raw["number_of_tasks"]),
            success=bool(raw.get("success", True)),
            blocked=bool(raw.get("blocked", False)),
            used_fallback=bool(raw.get("used_fallback", False)),
            warning_count=int(raw.get("warning_count", 0)),
            warning_codes=list(raw.get("warning_codes", [])),
            answers=dict(raw.get("answers", {})),
            images=dict(raw.get("images", {})),
            worksheet_label=raw.get("worksheet_label"),
            pdf_relative=str(raw.get("pdf_relative", "worksheet.pdf")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def display_title_pl(self) -> str:
        """Krótka etykieta do listy w UI."""
        try:
            dt = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
            when = dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            when = self.created_at[:16]
        label = f" · {self.worksheet_label}" if self.worksheet_label else ""
        return (
            f"{when} · kl.{self.grade} · {self.topic_label} · "
            f"{self.profile_label}{label}"
        )


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
