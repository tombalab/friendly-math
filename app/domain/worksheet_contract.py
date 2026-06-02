"""Worksheet request/result contracts (P1.3)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from app.domain.profile_catalog import ResolvedProfile

if TYPE_CHECKING:
    from app.domain.worksheet_layout import ResolvedWorksheetLayout
from app.domain.topic_catalog import ResolvedTopic
from app.generators.answers import AnswerKeyResult

if TYPE_CHECKING:
    from app.observability.events import WorksheetEvent

WarningSeverity = Literal["info", "warning", "error"]


@dataclass(frozen=True)
class WorksheetWarning:
    code: str
    message: str
    severity: WarningSeverity = "warning"


@dataclass(frozen=True)
class WorksheetRequest:
    """Parametry karty pracy z formularza Streamlit (lub innego klienta)."""

    grade: int
    topic_label: str
    profile_id: str
    number_of_tasks: int
    include_illustration: bool = False
    include_workspace: bool = True
    include_answers: bool = False
    optional_context: str | None = None
    worksheet_label: str | None = None


@dataclass(frozen=True)
class ImageCoverageSummary:
    """Podsumowanie ilustracji dla panelu jakości."""

    mode: Literal["disabled", "topic_skipped", "header", "per_task", "unavailable"]
    requested: bool
    rendered_count: int
    total_slots: int
    detail_pl: str


@dataclass
class WorksheetResult:
    """Wynik pełnego pipeline'u generowania karty pracy."""

    request: WorksheetRequest
    success: bool
    blocked: bool
    tasks: list[str] = field(default_factory=list)
    resolved_topic: ResolvedTopic | None = None
    resolved_profile: ResolvedProfile | None = None
    resolved_layout: "ResolvedWorksheetLayout | None" = None
    answer_key: AnswerKeyResult | None = None
    header_image: bytes | None = None
    task_images: list[bytes] | None = None
    image_coverage: ImageCoverageSummary | None = None
    pdf_bytes: bytes | None = None
    saved_pdf_path: Path | None = None
    warnings: list[WorksheetWarning] = field(default_factory=list)
    used_fallback: bool = False
    api_error: str | None = None
    font_available: bool = True
    pdf_ready: bool = False
    request_id: str = ""
    events: list["WorksheetEvent"] = field(default_factory=list)
    history_path: Path | None = None

    @property
    def can_download_pdf(self) -> bool:
        return self.success and not self.blocked and bool(self.pdf_bytes)

    def warnings_by_severity(self) -> dict[WarningSeverity, list[WorksheetWarning]]:
        grouped: dict[WarningSeverity, list[WorksheetWarning]] = {
            "info": [],
            "warning": [],
            "error": [],
        }
        for w in self.warnings:
            grouped[w.severity].append(w)
        return grouped

    def quality_summary_pl(self) -> dict[str, str]:
        """Skrócone metryki do panelu jakości (P1.6)."""
        topic = self.resolved_topic
        profile = self.resolved_profile
        topic_line = (
            f"{topic.label_pl} ({topic.topic_id}, blueprint: {topic.blueprint_status})"
            if topic
            else "—"
        )
        profile_line = profile.ui_label if profile else "—"

        if self.blocked:
            fallback_line = "zablokowano — temat nie został zachowany"
        elif self.used_fallback:
            fallback_line = "użyto zadań zastępczych (offline / API)"
        elif self.api_error:
            fallback_line = "częściowo zdegradowano (API)"
        else:
            fallback_line = "generacja AI / szablon tematu"

        if self.answer_key is None:
            answers_line = "wyłączony"
        else:
            answers_line = self.answer_key.summary_pl()

        img = self.image_coverage
        if img is None:
            images_line = "—"
        else:
            images_line = img.detail_pl

        pdf_line = "gotowy do pobrania" if self.pdf_ready else "niedostępny"
        if not self.font_available:
            pdf_line += " (brak czcionki polskiej)"

        layout_line = "—"
        if self.resolved_layout is not None:
            rl = self.resolved_layout
            layout_line = (
                f"task {rl.task_font_size} pt, margines {rl.margin} pt "
                f"({'low-stimuli' if rl.is_low_stimuli else 'standard'})"
            )

        task_quality = [w for w in self.warnings if w.code.startswith("task_quality_")]
        if not self.tasks:
            validation_line = "—"
        elif not task_quality:
            validation_line = "OK"
        else:
            validation_line = f"{len(task_quality)} uwag(i)"

        events_line = (
            f"{len(self.events)} zdarzeń · `{self.request_id[:8]}…`"
            if self.request_id
            else "—"
        )

        return {
            "Temat": topic_line,
            "Profil": profile_line,
            "Źródło zadań": fallback_line,
            "Zdarzenia": events_line,
            "Walidacja zadań": validation_line,
            "Klucz odpowiedzi": answers_line,
            "Ilustracje": images_line,
            "Układ PDF": layout_line,
            "PDF": pdf_line,
        }


def warning_from_dict(raw: dict[str, str]) -> WorksheetWarning:
    sev = raw.get("severity", "warning")
    if sev not in ("info", "warning", "error"):
        sev = "warning"
    return WorksheetWarning(
        code=raw.get("code", "unknown"),
        message=raw.get("message", ""),
        severity=sev,  # type: ignore[arg-type]
    )
