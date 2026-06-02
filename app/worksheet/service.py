"""Orchestrates worksheet generation outside Streamlit (P1.4)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from app.ai.layout_generator import generate_layout
from app.ai.text_generator import generate_tasks, warning_messages
from app.domain.profile_catalog import resolve_profile
from app.domain.topic_catalog import resolve_topic
from app.domain.worksheet_contract import (
    ImageCoverageSummary,
    WorksheetRequest,
    WorksheetResult,
    WorksheetWarning,
    warning_from_dict,
)
from app.generators.answers import compute_answer_key
from app.generators.images import (
    generate_worksheet_image,
    generate_worksheet_images_for_tasks,
)
from app.pdf.fonts import resolve_polish_font_path
from app.pdf.generator import WorksheetMeta, build_worksheet_pdf_bytes


class WorksheetService:
    """Callable service for worksheet generation (testable without Streamlit)."""

    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir

    def generate(self, request: WorksheetRequest) -> WorksheetResult:
        return generate_worksheet(request, output_dir=self.output_dir)


def generate_worksheet(
    request: WorksheetRequest,
    *,
    output_dir: Path | None = None,
) -> WorksheetResult:
    warnings: list[WorksheetWarning] = []
    resolved_topic = resolve_topic(request.topic_label, request.grade)
    resolved_profile = resolve_profile(request.profile_id)

    for msg in resolved_topic.warnings:
        warnings.append(WorksheetWarning("topic_catalog", msg, "warning"))
    for msg in resolved_profile.warnings:
        warnings.append(WorksheetWarning("profile_catalog", msg, "warning"))

    font_path, _ = resolve_polish_font_path()
    font_available = font_path is not None
    if not font_available:
        warnings.append(
            WorksheetWarning(
                "pdf_font_missing",
                "Brak czcionki DejaVu Sans — PDF może nie wyświetlać polskich znaków.",
                "warning",
            )
        )

    if resolved_topic.topic_id == "unknown":
        warnings.append(
            WorksheetWarning(
                "topic_unknown",
                f"Nieznany temat „{request.topic_label}” — wybierz pozycję z listy.",
                "error",
            )
        )
        return WorksheetResult(
            request=request,
            success=False,
            blocked=True,
            resolved_topic=resolved_topic,
            resolved_profile=resolved_profile,
            warnings=warnings,
            font_available=font_available,
        )

    if request.grade <= 3 and request.number_of_tasks > 15:
        warnings.append(
            WorksheetWarning(
                "validation",
                "Dla klas 1–3 maksymalna liczba zadań to 15.",
                "error",
            )
        )
        return WorksheetResult(
            request=request,
            success=False,
            blocked=True,
            resolved_topic=resolved_topic,
            resolved_profile=resolved_profile,
            warnings=warnings,
            font_available=font_available,
        )

    if not os.getenv("OPENAI_API_KEY"):
        warnings.append(
            WorksheetWarning(
                "api_key_missing",
                "Brak klucza OPENAI_API_KEY w środowisku.",
                "error",
            )
        )
        return WorksheetResult(
            request=request,
            success=False,
            blocked=True,
            resolved_topic=resolved_topic,
            resolved_profile=resolved_profile,
            warnings=warnings,
            font_available=font_available,
        )

    task_payload = generate_tasks(
        profile=resolved_profile.profile_id,
        grade=str(request.grade),
        topic=resolved_topic.blueprint_key,
        n=request.number_of_tasks,
    )

    for msg in warning_messages(task_payload):
        warnings.append(WorksheetWarning("task_generation", msg, "warning"))
    for raw in task_payload.get("_warnings", []):
        if isinstance(raw, dict):
            warnings.append(warning_from_dict(raw))

    used_fallback = bool(task_payload.get("_used_fallback"))
    api_error = task_payload.get("_error")
    if api_error and used_fallback:
        warnings.append(
            WorksheetWarning(
                "api_fallback_used",
                "Generowanie przez API nie powiodło się — użyto zadań zastępczych dla tematu.",
                "warning",
            )
        )

    if task_payload.get("_blocked"):
        warnings.append(
            WorksheetWarning(
                "fallback_blocked",
                task_payload.get("_warning")
                or "Nie udało się zachować wybranego tematu w trybie zastępczym.",
                "error",
            )
        )
        return WorksheetResult(
            request=request,
            success=False,
            blocked=True,
            resolved_topic=resolved_topic,
            resolved_profile=resolved_profile,
            warnings=warnings,
            used_fallback=used_fallback,
            api_error=str(api_error) if api_error else None,
            font_available=font_available,
        )

    tasks = list(task_payload.get("tasks", []))

    layout: dict[str, Any] | None = None
    try:
        layout = generate_layout(
            profile=resolved_profile.profile_id,
            grade=str(request.grade),
            number_of_tasks=request.number_of_tasks,
        )
    except Exception as exc:
        warnings.append(
            WorksheetWarning(
                "layout_fallback",
                f"Layout AI niedostępny ({exc}) — użyto domyślnego układu PDF.",
                "warning",
            )
        )

    header_image, task_images, image_coverage = _resolve_images(
        request, tasks, resolved_topic, resolved_profile, warnings
    )

    answer_key = None
    if request.include_answers:
        answer_key = compute_answer_key(
            tasks,
            topic_id=resolved_topic.topic_id,
            grade=request.grade,
        )
        if answer_key.manual_review_count:
            warnings.append(
                WorksheetWarning(
                    "answers_partial",
                    answer_key.summary_pl(),
                    "info",
                )
            )

    meta = WorksheetMeta(
        title=f"Karta pracy – klasa {request.grade}",
        grade=str(request.grade),
        topic_range=resolved_topic.label_pl,
        student_profile=resolved_profile.pdf_label,
        student_profile_id=resolved_profile.profile_id,
    )

    pdf_result = build_worksheet_pdf_bytes(
        meta=meta,
        tasks=tasks,
        layout=layout,
        image_bytes=header_image,
        task_images=task_images,
        answer_key=answer_key,
        include_workspace=request.include_workspace,
    )

    for pw in pdf_result.warnings:
        warnings.append(
            WorksheetWarning(pw.code, pw.message, "warning"),
        )

    pdf_bytes = pdf_result.pdf_bytes
    saved_path: Path | None = None
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        saved_path = output_dir / "worksheet.pdf"
        saved_path.write_bytes(pdf_bytes)

    return WorksheetResult(
        request=request,
        success=True,
        blocked=False,
        tasks=tasks,
        resolved_topic=resolved_topic,
        resolved_profile=resolved_profile,
        layout=layout,
        answer_key=answer_key,
        header_image=header_image,
        task_images=task_images,
        image_coverage=image_coverage,
        pdf_bytes=pdf_bytes,
        saved_pdf_path=saved_path,
        warnings=warnings,
        used_fallback=used_fallback,
        api_error=str(api_error) if api_error else None,
        font_available=font_available,
        pdf_ready=True,
    )


def _resolve_images(
    request: WorksheetRequest,
    tasks: list[str],
    resolved_topic,
    resolved_profile,
    warnings: list[WorksheetWarning],
) -> tuple[bytes | None, list[bytes] | None, ImageCoverageSummary]:
    if not request.include_illustration:
        return None, None, ImageCoverageSummary(
            mode="disabled",
            requested=False,
            rendered_count=0,
            total_slots=0,
            detail_pl="wyłączone w formularzu",
        )

    if resolved_topic.capabilities.skip_images:
        return None, None, ImageCoverageSummary(
            mode="topic_skipped",
            requested=True,
            rendered_count=0,
            total_slots=len(tasks),
            detail_pl="temat bez ilustracji (np. równania algebraiczne)",
        )

    per_task = resolved_profile.illustration_mode == "per_task"
    if per_task:
        try:
            images = generate_worksheet_images_for_tasks(
                tasks=tasks,
                topic=resolved_topic.blueprint_key,
                profile=resolved_profile.profile_id,
                grade=request.grade,
            )
        except Exception as exc:
            warnings.append(
                WorksheetWarning(
                    "images_per_task_failed",
                    f"Grafiki per zadanie niedostępne ({exc}).",
                    "warning",
                )
            )
            return None, None, ImageCoverageSummary(
                mode="unavailable",
                requested=True,
                rendered_count=0,
                total_slots=len(tasks),
                detail_pl="błąd generatora ilustracji per zadanie",
            )
        rendered = sum(1 for img in images if img)
        return None, images, ImageCoverageSummary(
            mode="per_task",
            requested=True,
            rendered_count=rendered,
            total_slots=len(tasks),
            detail_pl=f"{rendered}/{len(tasks)} zadań z ilustracją (bezpieczny zakres liczb)",
        )

    try:
        header = generate_worksheet_image(
            topic=resolved_topic.blueprint_key,
            profile=resolved_profile.profile_id,
            grade=request.grade,
        )
    except Exception as exc:
        warnings.append(
            WorksheetWarning(
                "images_header_failed",
                f"Grafika nagłówka niedostępna ({exc}).",
                "warning",
            )
        )
        return None, None, ImageCoverageSummary(
            mode="unavailable",
            requested=True,
            rendered_count=0,
            total_slots=1,
            detail_pl="błąd ilustracji nagłówka",
        )

    rendered = 1 if header else 0
    return header if header else None, None, ImageCoverageSummary(
        mode="header",
        requested=True,
        rendered_count=rendered,
        total_slots=1,
        detail_pl="1 ilustracja u góry karty" if rendered else "brak ilustracji nagłówka",
    )
