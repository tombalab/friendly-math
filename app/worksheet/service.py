"""Orchestrates worksheet generation outside Streamlit (P1.4)."""
from __future__ import annotations

import os
from pathlib import Path

from app.domain.worksheet_layout import ResolvedWorksheetLayout, resolve_worksheet_layout
from app.ai.text_generator import generate_tasks, warning_messages
from app.domain.profile_catalog import resolve_profile
from app.domain.topic_catalog import resolve_topic
from app.domain.worksheet_contract import (
    ImageCoverageSummary,
    TaskImageCoverageEntry,
    WorksheetRequest,
    WorksheetResult,
    WorksheetWarning,
    warning_from_dict,
)
from app.generators.answers import compute_answer_key
from app.generators.images import (
    generate_worksheet_image,
    generate_worksheet_images_for_tasks_with_diagnostics,
)
from app.validators.profile_enforcement import enforce_tasks_for_profile
from app.observability.events import (
    EVENT_ANSWER_COVERAGE,
    EVENT_FALLBACK_PADDING,
    EVENT_GENERATION_BLOCKED,
    EVENT_GENERATION_COMPLETE,
    EVENT_IMAGE_COVERAGE,
    EVENT_LAYOUT_RESOLVED,
    EVENT_MODEL_CALL,
    EVENT_PDF_BUILT,
    EVENT_PROFILE_RESOLVED,
    EVENT_REQUEST_START,
    EVENT_TASK_VALIDATION,
    EVENT_TOPIC_RESOLVED,
    GenerationTrace,
)
from app.observability.task_generation import metadata_from_task_payload
from app.pdf.fonts import resolve_polish_font_path
from app.pdf.generator import WorksheetMeta, build_worksheet_pdf_bytes
from app.validators.task_validator import validate_tasks_for_profile


class WorksheetService:
    """Callable service for worksheet generation (testable without Streamlit)."""

    def __init__(
        self,
        output_dir: Path | None = None,
        history_dir: Path | None = None,
    ) -> None:
        self.output_dir = output_dir
        self.history_dir = history_dir

    def generate(self, request: WorksheetRequest) -> WorksheetResult:
        return generate_worksheet(
            request,
            output_dir=self.output_dir,
            history_dir=self.history_dir,
        )


def generate_worksheet(
    request: WorksheetRequest,
    *,
    output_dir: Path | None = None,
    history_dir: Path | None = None,
    trace: GenerationTrace | None = None,
) -> WorksheetResult:
    warnings: list[WorksheetWarning] = []
    trace = trace or GenerationTrace.start()

    trace.emit(
        EVENT_REQUEST_START,
        grade=request.grade,
        topic_label=request.topic_label,
        profile_id=request.profile_id,
        number_of_tasks=request.number_of_tasks,
        include_illustration=request.include_illustration,
        include_workspace=request.include_workspace,
        include_answers=request.include_answers,
        has_optional_context=bool(request.optional_context),
        has_worksheet_label=bool(request.worksheet_label),
    )

    resolved_topic = resolve_topic(request.topic_label, request.grade)
    trace.emit(
        EVENT_TOPIC_RESOLVED,
        topic_id=resolved_topic.topic_id,
        label_pl=resolved_topic.label_pl,
        blueprint_key=resolved_topic.blueprint_key,
        blueprint_status=resolved_topic.blueprint_status,
        warning_count=len(resolved_topic.warnings),
    )

    resolved_profile = resolve_profile(request.profile_id)
    trace.emit(
        EVENT_PROFILE_RESOLVED,
        profile_id=resolved_profile.profile_id,
        ui_label=resolved_profile.ui_label,
        is_low_stimuli=resolved_profile.is_low_stimuli,
        illustration_mode=str(resolved_profile.illustration_mode),
        warning_count=len(resolved_profile.warnings),
    )

    for msg in resolved_topic.warnings:
        warnings.append(WorksheetWarning("topic_catalog", msg, "warning"))
    for msg in resolved_profile.warnings:
        warnings.append(WorksheetWarning("profile_catalog", msg, "warning"))

    font_path, font_source = resolve_polish_font_path()
    font_available = font_path is not None
    if not font_available:
        warnings.append(
            WorksheetWarning(
                "pdf_font_missing",
                "Brak czcionki DejaVu Sans — PDF może nie wyświetlać polskich znaków.",
                "warning",
            )
        )

    def _blocked(code: str, **extra) -> WorksheetResult:
        trace.emit(EVENT_GENERATION_BLOCKED, code=code, **extra)
        clean_warnings = _dedupe_warnings(warnings)
        return WorksheetResult(
            request=request,
            success=False,
            blocked=True,
            resolved_topic=resolved_topic,
            resolved_profile=resolved_profile,
            warnings=clean_warnings,
            font_available=font_available,
            request_id=trace.request_id,
            events=trace.events,
        )

    if resolved_topic.topic_id == "unknown":
        warnings.append(
            WorksheetWarning(
                "topic_unknown",
                f"Nieznany temat „{request.topic_label}” — wybierz pozycję z listy.",
                "error",
            )
        )
        return _blocked("topic_unknown")

    if request.grade <= 3 and request.number_of_tasks > 15:
        warnings.append(
            WorksheetWarning(
                "validation",
                "Dla klas 1–3 maksymalna liczba zadań to 15.",
                "error",
            )
        )
        return _blocked("grade_task_limit", grade=request.grade, requested=request.number_of_tasks)

    if not os.getenv("OPENAI_API_KEY"):
        warnings.append(
            WorksheetWarning(
                "api_key_missing",
                "Brak klucza OPENAI_API_KEY w środowisku.",
                "error",
            )
        )
        return _blocked("api_key_missing")

    task_payload = generate_tasks(
        profile=resolved_profile.profile_id,
        grade=str(request.grade),
        topic=resolved_topic.blueprint_key,
        n=request.number_of_tasks,
    )
    meta = metadata_from_task_payload(task_payload)
    trace.emit(EVENT_MODEL_CALL, **meta)

    for msg in warning_messages(task_payload):
        warnings.append(WorksheetWarning("task_generation", msg, "warning"))
    for raw in task_payload.get("_warnings", []):
        if isinstance(raw, dict):
            warnings.append(warning_from_dict(raw))

    if meta.get("has_padding"):
        trace.emit(
            EVENT_FALLBACK_PADDING,
            reason="fallback_padded_tasks",
            warning_codes=meta.get("warning_codes", []),
        )

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
        return _blocked(
            "fallback_blocked",
            used_fallback=used_fallback,
            had_api_error=bool(api_error),
        )

    tasks = list(task_payload.get("tasks", []))

    tasks, replaced, enforce_msgs = enforce_tasks_for_profile(
        tasks,
        profile_id=resolved_profile.profile_id,
        grade=request.grade,
        topic_id=resolved_topic.topic_id,
    )
    for msg in enforce_msgs:
        warnings.append(
            WorksheetWarning("profile_enforcement", msg, "info"),
        )
    if replaced:
        trace.emit(EVENT_TASK_VALIDATION, profile_replaced=replaced)

    validation = validate_tasks_for_profile(
        tasks,
        profile_id=resolved_profile.profile_id,
        grade=request.grade,
        topic_id=resolved_topic.topic_id,
    )
    trace.emit(
        EVENT_TASK_VALIDATION,
        issue_count=len(validation.issues),
        codes=sorted({i.code for i in validation.issues}),
    )
    for issue in validation.issues:
        label = (
            f"Zadanie {issue.task_index + 1}: {issue.message}"
            if issue.task_index >= 0
            else issue.message
        )
        warnings.append(
            WorksheetWarning(
                f"task_quality_{issue.code}",
                label,
                issue.severity,
            )
        )

    header_image, task_images, image_coverage = _resolve_images(
        request, tasks, resolved_topic, resolved_profile, warnings
    )
    if image_coverage is not None:
        trace.emit(
            EVENT_IMAGE_COVERAGE,
            mode=image_coverage.mode,
            requested=image_coverage.requested,
            rendered_count=image_coverage.rendered_count,
            total_slots=image_coverage.total_slots,
        )

    resolved_layout: ResolvedWorksheetLayout
    layout_source = "resolver"
    per_task_images_requested = bool(
        image_coverage is not None
        and image_coverage.requested
        and image_coverage.mode == "per_task"
    )
    try:
        resolved_layout = resolve_worksheet_layout(
            resolved_profile,
            request.grade,
            request.number_of_tasks,
            include_workspace=request.include_workspace,
            per_task_images_requested=per_task_images_requested,
        )
        layout_source = resolved_layout.source
    except Exception as exc:
        warnings.append(
            WorksheetWarning(
                "layout_fallback",
                f"Nie udało się rozwiązać layoutu ({exc}) — użyto domyślnego układu.",
                "warning",
            )
        )
        from app.domain.worksheet_layout import PDF_PRINT_DEFAULTS

        fallback_values = dict(PDF_PRINT_DEFAULTS)
        if not request.include_workspace:
            fallback_values["workspace_lines"] = 0
        elif per_task_images_requested:
            fallback_values["workspace_lines"] = min(
                int(fallback_values.get("workspace_lines", 0)),
                2,
            )
        resolved_layout = ResolvedWorksheetLayout.from_mapping(
            fallback_values,
            is_low_stimuli=resolved_profile.is_low_stimuli,
            source="fallback",
        )
        layout_source = "fallback"

    trace.emit(
        EVENT_LAYOUT_RESOLVED,
        source=layout_source,
        task_font_size=resolved_layout.task_font_size,
        is_low_stimuli=resolved_layout.is_low_stimuli,
    )

    answer_key = None
    if request.include_answers:
        answer_key = compute_answer_key(
            tasks,
            topic_id=resolved_topic.topic_id,
            grade=request.grade,
        )
        trace.emit(
            EVENT_ANSWER_COVERAGE,
            supported_count=answer_key.supported_count,
            total=len(tasks),
            manual_review_count=answer_key.manual_review_count,
        )
        if answer_key.manual_review_count:
            warnings.append(
                WorksheetWarning(
                    "answers_partial",
                    answer_key.summary_pl(),
                    "info",
                )
            )
    else:
        trace.emit(EVENT_ANSWER_COVERAGE, enabled=False)

    meta_pdf = WorksheetMeta(
        title=f"Karta pracy – klasa {request.grade}",
        grade=str(request.grade),
        topic_range=resolved_topic.label_pl,
        student_profile=resolved_profile.pdf_label,
        student_profile_id=resolved_profile.profile_id,
    )

    pdf_result = build_worksheet_pdf_bytes(
        meta=meta_pdf,
        tasks=tasks,
        layout=resolved_layout,
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
    trace.emit(
        EVENT_PDF_BUILT,
        pdf_bytes=len(pdf_bytes),
        font_available=font_available,
        font_source=font_source or "missing",
        pdf_warning_codes=[w.code for w in pdf_result.warnings],
    )

    saved_path: Path | None = None
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        saved_path = output_dir / "worksheet.pdf"
        saved_path.write_bytes(pdf_bytes)

    clean_warnings = _dedupe_warnings(warnings)

    history_path: Path | None = None
    if history_dir is not None:
        from app.history.store import WorksheetHistoryStore

        store = WorksheetHistoryStore(history_dir)
        history_path = store.save(
            _result_for_history(
                request=request,
                tasks=tasks,
                resolved_topic=resolved_topic,
                resolved_profile=resolved_profile,
                answer_key=answer_key,
                image_coverage=image_coverage,
                pdf_bytes=pdf_bytes,
                warnings=clean_warnings,
                used_fallback=used_fallback,
                request_id=trace.request_id,
            ),
            trace,
            worksheet_label=request.worksheet_label,
        )

    trace.emit(
        EVENT_GENERATION_COMPLETE,
        success=True,
        blocked=False,
        task_count=len(tasks),
        used_fallback=used_fallback,
        warning_count=len(clean_warnings),
        saved_pdf=bool(saved_path),
        history_saved=bool(history_path),
    )

    return WorksheetResult(
        request=request,
        success=True,
        blocked=False,
        tasks=tasks,
        resolved_topic=resolved_topic,
        resolved_profile=resolved_profile,
        resolved_layout=resolved_layout,
        answer_key=answer_key,
        header_image=header_image,
        task_images=task_images,
        image_coverage=image_coverage,
        pdf_bytes=pdf_bytes,
        saved_pdf_path=saved_path,
        warnings=clean_warnings,
        used_fallback=used_fallback,
        api_error=str(api_error) if api_error else None,
        font_available=font_available,
        pdf_ready=True,
        request_id=trace.request_id,
        events=trace.events,
        history_path=history_path,
    )


def _dedupe_warnings(warnings: list[WorksheetWarning]) -> list[WorksheetWarning]:
    """Zachowuje kolejność, ale usuwa identyczne uwagi z różnych etapów pipeline'u."""
    seen: set[tuple[str, str]] = set()
    out: list[WorksheetWarning] = []
    for warning in warnings:
        key = (warning.message, warning.severity)
        if key in seen:
            continue
        seen.add(key)
        out.append(warning)
    return out


def _result_for_history(
    *,
    request: WorksheetRequest,
    tasks: list[str],
    resolved_topic,
    resolved_profile,
    answer_key,
    image_coverage,
    pdf_bytes: bytes,
    warnings: list[WorksheetWarning],
    used_fallback: bool,
    request_id: str,
) -> WorksheetResult:
    """Buduje WorksheetResult wyłącznie do zapisu historii (bez duplikacji pól)."""
    return WorksheetResult(
        request=request,
        success=True,
        blocked=False,
        tasks=tasks,
        resolved_topic=resolved_topic,
        resolved_profile=resolved_profile,
        answer_key=answer_key,
        image_coverage=image_coverage,
        pdf_bytes=pdf_bytes,
        warnings=warnings,
        used_fallback=used_fallback,
        pdf_ready=True,
        request_id=request_id,
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
            img_result = generate_worksheet_images_for_tasks_with_diagnostics(
                tasks=tasks,
                topic=resolved_topic.blueprint_key,
                profile=resolved_profile.profile_id,
                size=(960, 220),
                grade=request.grade,
            )
            images = img_result.image_bytes_list
            per_task_entries = tuple(
                TaskImageCoverageEntry(
                    task_index=s.task_index,
                    rendered=s.rendered,
                    skip_reason=s.skip_reason,
                )
                for s in img_result.slots
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
        skipped_n = len(tasks) - rendered
        coverage_ratio = rendered / len(tasks) if tasks else 1.0
        header: bytes | None = None
        if coverage_ratio < 0.5:
            warnings.append(
                WorksheetWarning(
                    "images_low_coverage",
                    (
                        "Mniej niż połowa zadań ma ilustrację per zadanie — "
                        "dodano małą ilustrację w nagłówku."
                    ),
                    "warning",
                )
            )
            try:
                header = generate_worksheet_image(
                    topic=resolved_topic.blueprint_key,
                    profile=resolved_profile.profile_id,
                    size=(320, 150),
                    grade=request.grade,
                )
            except Exception as exc:
                warnings.append(
                    WorksheetWarning(
                        "images_low_coverage_header_failed",
                        f"Nie udało się dodać ilustracji nagłówka ({exc}).",
                        "warning",
                    )
                )
        detail = (
            f"{rendered}/{len(tasks)} zadań z ilustracją"
            + (f"; {skipped_n} pominięto (liczby poza zakresem profilu)" if skipped_n else "")
        )
        if header:
            detail += "; dodano mały nagłówek"
        return header if header else None, images, ImageCoverageSummary(
            mode="per_task",
            requested=True,
            rendered_count=rendered,
            total_slots=len(tasks),
            detail_pl=detail,
            per_task=per_task_entries,
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
