from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Iterable, Optional

import re

from reportlab.lib.pagesizes import A4  # pyright: ignore[reportMissingModuleSource]
from reportlab.lib.colors import HexColor  # pyright: ignore[reportMissingModuleSource]
from reportlab.lib.utils import ImageReader  # pyright: ignore[reportMissingModuleSource]
from reportlab.pdfbase import pdfmetrics  # pyright: ignore[reportMissingModuleSource]
from reportlab.pdfgen import canvas  # pyright: ignore[reportMissingModuleSource]

from app.generators.answers import AnswerKeyResult
from app.pdf.fonts import register_polish_font
from app.domain.educational_strategy import WorksheetBlock, WorksheetPlan
from app.domain.worksheet_layout import PDF_PRINT_DEFAULTS, ResolvedWorksheetLayout


@dataclass(frozen=True)
class PdfWarning:
    code: str
    message: str


@dataclass(frozen=True)
class PdfBuildResult:
    pdf_bytes: bytes
    warnings: tuple[PdfWarning, ...] = ()


@dataclass(frozen=True)
class WorksheetMeta:
    title: str
    grade: str
    topic_range: str
    student_profile: str
    student_profile_id: str = ""


# Bold emulowany w `_draw_bold` (podwójne rysowanie) — wystarczy DejaVu regular.
# Finalny layout pochodzi z `resolve_worksheet_layout()` (P1.5) — PDF nie decyduje o profilu.


# --------------------------------------------------------------------
# Niskie poziomy rysowania (bold emulation, tła, podkreślenia, stopka)
# --------------------------------------------------------------------


def _draw_bold(c, x: float, y: float, text: str, font_name: str, size: float) -> None:
    """
    Emulowany bold: rysujemy tekst 3 razy z mikro-offsetem (0.4 pt).
    Daje wizualnie pogrubione znaki bez konieczności posiadania osobnego TTF.
    """
    c.setFont(font_name, size)
    c.drawString(x, y, text)
    c.drawString(x + 0.4, y, text)
    c.drawString(x, y + 0.4, text)


def _string_width(text: str, font_name: str, size: float) -> float:
    try:
        return pdfmetrics.stringWidth(text, font_name, size)
    except Exception:
        # Konserwatywny fallback – ~0.6× size na znak.
        return len(text) * size * 0.6


def _draw_section_header(
    c, x: float, y: float, text: str, font_name: str, size: float,
    width_to_underline: float, text_color: str,
) -> None:
    """Nagłówek sekcji: UPPERCASE + bold + cienkie podkreślenie pod tekstem."""
    upper = text.upper()
    _draw_bold(c, x, y, upper, font_name, size)
    try:
        c.setStrokeColor(HexColor(text_color))
        c.setLineWidth(1.0)
        c.line(x, y - 4, x + width_to_underline, y - 4)
    except Exception:
        pass


def _draw_workspace_lines(
    c, x_start: float, x_end: float, y_top: float,
    n_lines: int, gap: float, color: str,
) -> float:
    """
    Rysuje `n_lines` kropkowanych linijek do obliczeń (jasnoszare).
    Zwraca nowe y (po ostatniej linijce, gotowe do kontynuacji rysowania).
    """
    if n_lines <= 0:
        return y_top
    try:
        c.setStrokeColor(HexColor(color))
        c.setLineWidth(0.5)
        c.setDash([2, 3])
        y = y_top
        for _ in range(n_lines):
            c.line(x_start, y, x_end, y)
            y -= gap
        return y
    finally:
        try:
            c.setDash()  # reset dash
        except Exception:
            pass


def _draw_page_background(canvas_obj, width: float, height: float, bg_color: str) -> None:
    """Rysuje tło strony jeśli nie białe."""
    if bg_color.upper() not in ("#FFFFFF", "WHITE", "#FFF"):
        try:
            canvas_obj.setFillColor(HexColor(bg_color))
            canvas_obj.rect(0, 0, width, height, fill=1, stroke=0)
        except Exception:
            pass


def _draw_footer(canvas_obj, width: float, margin: float, page_num: int,
                 font_name: str, text_color: str) -> None:
    """Stopka z numerem strony."""
    try:
        canvas_obj.setFillColor(HexColor(text_color))
        canvas_obj.setFont(font_name, 9)
        canvas_obj.drawRightString(width - margin, 24, f"Friendly Math — strona {page_num}")
    except Exception:
        pass


def _draw_document_header(
    c,
    *,
    meta: WorksheetMeta,
    plan: Optional[WorksheetPlan],
    x: float,
    y: float,
    width: float,
    layout: dict,
    font_name: str,
    text_color: str,
    muted_color: str,
) -> float:
    """Rysuje luźniejszy nagłówek karty z motywem szablonu."""
    header_h = 86 if plan else 58
    accent = layout.get("accent_color", "#3f51b5")
    soft = layout.get("soft_color", "#f6f7fb")
    border = layout.get("border_color", "#DDDDDD")
    try:
        c.setFillColor(HexColor(soft))
        c.setStrokeColor(HexColor(border))
        c.roundRect(x, y - header_h, width, header_h, 12, fill=1, stroke=1)
    except Exception:
        pass

    if plan:
        _draw_template_pattern(c, x, y, width, header_h, plan.template.pattern, accent, border)
        _draw_template_mark(
            c,
            x + 18,
            y - 18,
            42,
            plan.template.icon_kind,
            accent,
            soft,
        )
        text_x = x + 72
        text_w = width - 92
    else:
        text_x = x + 16
        text_w = width - 32

    try:
        c.setFillColor(HexColor(text_color))
    except Exception:
        pass
    _draw_bold(c, text_x, y - 24, meta.title, font_name, layout["title_font_size"])

    if plan:
        try:
            c.setFillColor(HexColor(accent))
        except Exception:
            pass
        c.setFont(font_name, 10)
        c.drawString(text_x, y - 42, f"{plan.template.name_pl}: {plan.template.motif_label}"[:86])
        try:
            c.setFillColor(HexColor(muted_color))
        except Exception:
            pass
        c.setFont(font_name, layout["metadata_font_size"])
        meta_line = f"Klasa {meta.grade}  |  {meta.topic_range}  |  {meta.student_profile}"
        _draw_wrapped_text(c, text_x, y - 58, meta_line, text_w, font_name, layout["metadata_font_size"], 13)
    else:
        try:
            c.setFillColor(HexColor(muted_color))
        except Exception:
            pass
        c.setFont(font_name, layout["metadata_font_size"])
        c.drawString(text_x, y - 44, f"Klasa: {meta.grade}   |   Zakres: {meta.topic_range}   |   Profil: {meta.student_profile}")

    try:
        c.setFillColor(HexColor(text_color))
    except Exception:
        pass
    return y - header_h - 18


def _draw_template_pattern(
    c,
    x: float,
    y: float,
    width: float,
    height: float,
    pattern: str,
    accent: str,
    border: str,
) -> None:
    if pattern == "none":
        return
    try:
        c.setStrokeColor(HexColor(border))
        c.setFillColor(HexColor(accent))
        c.setLineWidth(0.7)
    except Exception:
        pass
    right = x + width - 24
    top = y - 18
    if pattern == "stars":
        for i, (dx, dy) in enumerate(((0, 0), (-34, -18), (-70, 2), (-102, -28))):
            size = 3 + (i % 2)
            c.circle(right + dx, top + dy, size, fill=1, stroke=0)
    elif pattern == "trail":
        for i in range(5):
            c.circle(right - i * 24, top - (i % 2) * 16, 3, fill=0, stroke=1)
        c.line(right - 96, top - 0, right, top)
    elif pattern == "clues":
        for i in range(4):
            bx = right - i * 30
            by = top - (i % 2) * 18
            c.rect(bx - 4, by - 4, 8, 8, fill=0, stroke=1)
    elif pattern == "rule_lines":
        for i in range(4):
            c.line(right - 118, top - i * 10, right, top - i * 10)


def _draw_template_mark(
    c,
    x: float,
    y: float,
    size: float,
    icon_kind: str,
    accent: str,
    soft: str,
) -> None:
    """Mały znak szablonu: proste wektorowe logo bez plików zewnętrznych."""
    try:
        c.setFillColor(HexColor("#FFFFFF"))
        c.setStrokeColor(HexColor(accent))
        c.setLineWidth(1.2)
        c.circle(x + size / 2, y - size / 2, size / 2, fill=1, stroke=1)
        c.setStrokeColor(HexColor(accent))
        c.setFillColor(HexColor(accent))
    except Exception:
        pass
    cx = x + size / 2
    cy = y - size / 2
    r = size / 2
    if icon_kind == "rocket":
        c.line(cx, cy + r * 0.55, cx - r * 0.32, cy - r * 0.2)
        c.line(cx, cy + r * 0.55, cx + r * 0.32, cy - r * 0.2)
        c.line(cx - r * 0.32, cy - r * 0.2, cx + r * 0.32, cy - r * 0.2)
        c.circle(cx, cy + r * 0.08, r * 0.13, fill=0, stroke=1)
        c.line(cx - r * 0.16, cy - r * 0.25, cx - r * 0.32, cy - r * 0.5)
        c.line(cx + r * 0.16, cy - r * 0.25, cx + r * 0.32, cy - r * 0.5)
    elif icon_kind == "magnifier":
        c.circle(cx - r * 0.08, cy + r * 0.08, r * 0.32, fill=0, stroke=1)
        c.line(cx + r * 0.14, cy - r * 0.14, cx + r * 0.42, cy - r * 0.42)
    elif icon_kind == "compass":
        c.circle(cx, cy, r * 0.36, fill=0, stroke=1)
        c.line(cx, cy + r * 0.5, cx + r * 0.14, cy - r * 0.02)
        c.line(cx, cy + r * 0.5, cx - r * 0.14, cy - r * 0.02)
        c.line(cx - r * 0.42, cy - r * 0.34, cx + r * 0.42, cy + r * 0.34)
    elif icon_kind == "smile":
        c.circle(cx - r * 0.18, cy + r * 0.12, r * 0.04, fill=1, stroke=0)
        c.circle(cx + r * 0.18, cy + r * 0.12, r * 0.04, fill=1, stroke=0)
        c.arc(cx - r * 0.32, cy - r * 0.3, cx + r * 0.32, cy + r * 0.1, 200, 140)
    else:
        c.line(cx - r * 0.32, cy + r * 0.34, cx - r * 0.32, cy - r * 0.38)
        c.line(cx + r * 0.32, cy + r * 0.34, cx + r * 0.32, cy - r * 0.38)
        c.line(cx - r * 0.32, cy + r * 0.34, cx + r * 0.32, cy + r * 0.34)
        c.line(cx - r * 0.32, cy - r * 0.38, cx + r * 0.32, cy - r * 0.38)
        c.line(cx - r * 0.2, cy + r * 0.1, cx + r * 0.2, cy + r * 0.1)
        c.line(cx - r * 0.2, cy - r * 0.08, cx + r * 0.2, cy - r * 0.08)


def _draw_wrapped_text(
    c,
    x: float,
    y: float,
    text: str,
    max_width: float,
    font_name: str,
    font_size: float,
    line_gap: float,
    *,
    max_lines: int = 2,
) -> float:
    c.setFont(font_name, font_size)
    lines = _wrap_text_by_width(
        text,
        max_width=max_width,
        font_name=font_name,
        font_size=font_size,
    )
    y_curr = y
    for line in lines[:max_lines]:
        c.drawString(x, y_curr, line)
        y_curr -= line_gap
    return y_curr


def _draw_tasks_body(
    c,
    *,
    y: float,
    page_num: int,
    width: float,
    height: float,
    margin: float,
    layout: dict,
    tasks_list: list[str],
    task_images: Optional[list],
    has_task_images: bool,
    worksheet_plan: Optional[WorksheetPlan],
    base_font: str,
    text_color: str,
    muted_color: str,
    bg_color: str,
) -> tuple[float, int]:
    task_font = layout["task_font_size"]
    line_spacing = layout["line_spacing"]
    task_spacing = layout["task_spacing"]
    workspace_lines = layout["workspace_lines"]
    workspace_gap = layout["workspace_line_gap"]
    available_width = width - 2 * margin
    footer_reserved = 40
    page_body_h = height - 2 * margin - footer_reserved

    def start_new_page(y_current: float) -> tuple[float, int]:
        _draw_footer(c, width, margin, page_num, base_font, text_color)
        c.showPage()
        new_page = page_num + 1
        _draw_page_background(c, width, height, bg_color)
        try:
            c.setFillColor(HexColor(text_color))
        except Exception:
            pass
        return height - margin, new_page

    def new_page_if_needed(y_now: float, block_h: float) -> tuple[float, int]:
        nonlocal page_num
        if y_now - block_h < margin + footer_reserved and block_h <= page_body_h:
            y_new, page_num = start_new_page(y_now)
            return y_new, page_num
        if y_now < margin + footer_reserved:
            y_new, page_num = start_new_page(y_now)
            return y_new, page_num
        return y_now, page_num

    if worksheet_plan is None:
        return _draw_legacy_task_list(
            c,
            y=y,
            page_num=page_num,
            width=width,
            height=height,
            margin=margin,
            layout=layout,
            tasks_list=tasks_list,
            task_images=task_images,
            has_task_images=has_task_images,
            base_font=base_font,
            text_color=text_color,
            muted_color=muted_color,
            bg_color=bg_color,
        )

    y = _draw_strategy_intro(
        c,
        y,
        margin,
        available_width,
        worksheet_plan,
        layout,
        base_font,
        text_color,
        muted_color,
    )

    task_img_width_pt = available_width - 2 * int(layout.get("card_padding", 12))
    task_aspect = layout.get("task_image_aspect", 100 / 480)
    task_img_height_pt = max(54, int(task_img_width_pt * task_aspect))

    for section in worksheet_plan.sections:
        section_h = layout["section_spacing"] + 6
        y, page_num = new_page_if_needed(y, section_h)
        _draw_section_header(
            c,
            margin,
            y,
            section.title,
            base_font,
            layout["section_font_size"],
            available_width,
            text_color,
        )
        y -= layout["section_spacing"]

        for block in section.blocks:
            block_h = _estimate_plan_block_height(
                block,
                available_width,
                task_img_height_pt,
                has_image=bool(
                    has_task_images
                    and block.task_index is not None
                    and task_images
                    and task_images[block.task_index]
                ),
                layout=layout,
                base_font=base_font,
            )
            y, page_num = new_page_if_needed(y, block_h)
            y = _draw_plan_block(
                c,
                y,
                margin,
                available_width,
                block,
                layout,
                base_font,
                text_color,
                muted_color,
                task_images,
                task_img_width_pt,
                task_img_height_pt,
            )
            y -= int(layout.get("block_gap", task_spacing))
        y -= section.spacing_after

    return y, page_num


def _draw_strategy_intro(
    c,
    y: float,
    margin: float,
    available_width: float,
    plan: WorksheetPlan,
    layout: dict,
    base_font: str,
    text_color: str,
    muted_color: str,
) -> float:
    pad = int(layout.get("card_padding", 12))
    intro_h = 78
    accent = layout.get("accent_color", "#3f51b5")
    try:
        c.setFillColor(HexColor(layout.get("soft_color", "#f6f7fb")))
        c.setStrokeColor(HexColor(layout.get("border_color", "#DDDDDD")))
        c.roundRect(margin, y - intro_h, available_width, intro_h, 8, fill=1, stroke=1)
        c.setFillColor(HexColor(text_color))
    except Exception:
        pass
    try:
        c.setFillColor(HexColor(accent))
    except Exception:
        pass
    _draw_bold(c, margin + pad, y - 18, "Jak pracujemy na tej karcie", base_font, 11)
    try:
        c.setFillColor(HexColor(text_color))
    except Exception:
        pass
    _draw_wrapped_text(
        c,
        margin + pad,
        y - 34,
        plan.strategy.short_goal_pl,
        available_width - 2 * pad,
        base_font,
        9,
        12,
        max_lines=2,
    )
    try:
        c.setFillColor(HexColor("#5f6368"))
    except Exception:
        pass
    c.setFont(base_font, 9)
    c.drawString(margin + pad, y - 64, f"Rola grafiki: {plan.visual_theme.learning_role_pl}"[:112])
    try:
        c.setFillColor(HexColor(text_color))
    except Exception:
        pass
    return y - intro_h - int(layout.get("section_gap", 18))


def _estimate_plan_block_height(
    block: WorksheetBlock,
    available_width: float,
    image_h: float,
    *,
    has_image: bool,
    layout: dict,
    base_font: str,
) -> float:
    pad = int(layout.get("card_padding", 12))
    content_w = available_width - 2 * pad
    text_w = content_w - 18
    lines = _wrap_text_by_width(
        block.task_text,
        max_width=text_w,
        font_name=base_font,
        font_size=layout["task_font_size"],
    )
    instruction_h = len(block.instructions) * 15 + (8 if block.instructions else 0)
    answer_h = max(
        int(layout.get("answer_box_height", 34)),
        block.answer_box_lines * int(layout.get("workspace_line_gap", 18)),
    )
    image_block_h = image_h + 8 if has_image else 0
    return 44 + instruction_h + image_block_h + len(lines) * layout["line_spacing"] + answer_h + 2 * pad


def _draw_plan_block(
    c,
    y: float,
    margin: float,
    available_width: float,
    block: WorksheetBlock,
    layout: dict,
    base_font: str,
    text_color: str,
    muted_color: str,
    task_images: Optional[list],
    task_img_width_pt: float,
    task_img_height_pt: float,
) -> float:
    pad = int(layout.get("card_padding", 12))
    block_h = _estimate_plan_block_height(
        block,
        available_width,
        task_img_height_pt,
        has_image=bool(block.task_index is not None and task_images and task_images[block.task_index]),
        layout=layout,
        base_font=base_font,
    )
    x = margin
    try:
        c.setFillColor(HexColor("#FFFFFF"))
        c.setStrokeColor(HexColor(layout.get("border_color", "#DDDDDD")))
        c.roundRect(x, y - block_h, available_width, block_h, 10, fill=1, stroke=1)
        c.setFillColor(HexColor(layout.get("accent_color", "#3f51b5")))
        c.roundRect(x, y - 30, available_width, 30, 10, fill=1, stroke=0)
        c.setFillColor(HexColor("#FFFFFF"))
    except Exception:
        pass
    header = block.title
    _draw_bold(c, x + pad, y - 20, header, base_font, 11)
    badge = block.progress_label or block.visual_cue
    if badge:
        _draw_block_badge(c, x + available_width - pad - 72, y - 22, 72, badge, base_font)
    try:
        c.setFillColor(HexColor(text_color))
    except Exception:
        pass
    y_curr = y - 42

    if block.instructions:
        try:
            c.setFillColor(HexColor("#4f565c"))
        except Exception:
            pass
        c.setFont(base_font, 10)
        for instruction in block.instructions:
            c.drawString(x + pad, y_curr, instruction)
            y_curr -= 15
        y_curr -= 8
        try:
            c.setFillColor(HexColor(text_color))
        except Exception:
            pass

    if block.task_index is not None and task_images and task_images[block.task_index]:
        try:
            img_reader = ImageReader(BytesIO(task_images[block.task_index]))
            c.drawImage(
                img_reader,
                x + pad,
                y_curr - task_img_height_pt,
                width=task_img_width_pt,
                height=task_img_height_pt,
                preserveAspectRatio=True,
                mask="auto",
            )
            y_curr -= task_img_height_pt + 8
        except Exception:
            pass

    prefix = f"{(block.task_index or 0) + 1}." if block.task_index is not None else "✓"
    prefix_w = _string_width(prefix, base_font, layout["task_font_size"]) + 6
    lines = _wrap_text_by_width(
        block.task_text,
        max_width=available_width - 2 * pad - prefix_w,
        font_name=base_font,
        font_size=layout["task_font_size"],
    )
    for line_idx, line in enumerate(lines):
        if line_idx == 0:
            _draw_bold(c, x + pad, y_curr, prefix, base_font, layout["task_font_size"])
            _draw_task_content(c, x + pad + prefix_w, y_curr, line, base_font, layout["task_font_size"])
        else:
            _draw_task_content(c, x + pad + prefix_w, y_curr, line, base_font, layout["task_font_size"])
        y_curr -= layout["line_spacing"]

    y_curr -= 4
    _draw_answer_area(c, x + pad, y_curr, available_width - 2 * pad, block, layout, muted_color, base_font)
    return y - block_h


def _draw_block_badge(c, x: float, y: float, width: float, text: str, font_name: str) -> None:
    try:
        c.setStrokeColor(HexColor("#FFFFFF"))
        c.setFillColor(HexColor("#FFFFFF"))
        c.roundRect(x, y - 10, width, 16, 8, fill=0, stroke=1)
    except Exception:
        pass
    c.setFont(font_name, 8)
    c.drawCentredString(x + width / 2, y - 5, text[:14])


def _draw_answer_area(
    c,
    x: float,
    y: float,
    width: float,
    block: WorksheetBlock,
    layout: dict,
    muted_color: str,
    base_font: str,
) -> None:
    h = max(int(layout.get("answer_box_height", 34)), block.answer_box_lines * int(layout.get("workspace_line_gap", 18)))
    try:
        c.setStrokeColor(HexColor(muted_color))
        c.setLineWidth(0.7)
    except Exception:
        pass
    if block.answer_mode == "checkbox":
        c.rect(x, y - 18, 14, 14, fill=0, stroke=1)
        c.rect(x + 72, y - 18, 14, 14, fill=0, stroke=1)
        c.setFont(base_font, 9)
        c.drawString(x + 20, y - 14, "A")
        c.drawString(x + 92, y - 14, "B")
        return
    if block.answer_mode == "connect":
        c.line(x, y - 12, x + width, y - 12)
        c.line(x, y - 34, x + width, y - 34)
        return
    if block.answer_mode in ("circle", "color"):
        for i in range(3):
            c.circle(x + 18 + i * 58, y - 16, 10, fill=0, stroke=1)
        return
    c.roundRect(x, y - h, width, h, 6, fill=0, stroke=1)


def _draw_legacy_task_list(
    c,
    *,
    y: float,
    page_num: int,
    width: float,
    height: float,
    margin: float,
    layout: dict,
    tasks_list: list[str],
    task_images: Optional[list],
    has_task_images: bool,
    base_font: str,
    text_color: str,
    muted_color: str,
    bg_color: str,
) -> tuple[float, int]:
    section_w = width - 2 * margin
    _draw_section_header(c, margin, y, "Zadania", base_font, layout["section_font_size"], section_w, text_color)
    y -= layout["section_spacing"]
    task_font = layout["task_font_size"]
    line_spacing = layout["line_spacing"]
    task_spacing = layout["task_spacing"]
    workspace_lines = layout["workspace_lines"]
    workspace_gap = layout["workspace_line_gap"]
    available_width = width - 2 * margin
    task_img_width_pt = available_width
    task_aspect = layout.get("task_image_aspect", 100 / 480)
    task_img_height_pt = max(60, int(task_img_width_pt * task_aspect))
    footer_reserved = 40
    page_body_h = height - 2 * margin - footer_reserved

    def start_new_page() -> float:
        nonlocal page_num
        _draw_footer(c, width, margin, page_num, base_font, text_color)
        c.showPage()
        page_num += 1
        _draw_page_background(c, width, height, bg_color)
        try:
            c.setFillColor(HexColor(text_color))
        except Exception:
            pass
        return height - margin

    def new_page_if_block_will_not_fit(y_now: float, block_h: float) -> float:
        if y_now - block_h < margin + footer_reserved and block_h <= page_body_h:
            return start_new_page()
        if y_now < margin + footer_reserved:
            return start_new_page()
        return y_now

    for i, task in enumerate(tasks_list, start=1):
        prefix = f"{i}."
        prefix_w = _string_width(prefix, base_font, task_font) + 6
        indent = _string_width("99.", base_font, task_font) + 6
        lines = _wrap_text_by_width(
            task,
            max_width=available_width - prefix_w,
            font_name=base_font,
            font_size=task_font,
            continuation_width=available_width - indent,
        )
        has_current_image = bool(has_task_images and task_images and task_images[i - 1])
        image_block_h = task_img_height_pt + 8 if has_current_image else 0
        workspace_block_h = 4 + workspace_lines * workspace_gap if workspace_lines > 0 else 0
        block_h = image_block_h + len(lines) * line_spacing + workspace_block_h + task_spacing
        y = new_page_if_block_will_not_fit(y, block_h)
        if has_current_image and task_images:
            try:
                img_reader = ImageReader(BytesIO(task_images[i - 1]))
                c.drawImage(
                    img_reader,
                    margin,
                    y - task_img_height_pt,
                    width=task_img_width_pt,
                    height=task_img_height_pt,
                    preserveAspectRatio=True,
                    mask="auto",
                )
                y -= task_img_height_pt + 8
            except Exception:
                pass
        for line_idx, line in enumerate(lines):
            if y < margin + footer_reserved:
                y = start_new_page()
            if line_idx == 0:
                _draw_bold(c, margin, y, prefix, base_font, task_font)
                _draw_task_content(c, margin + prefix_w, y, line, base_font, task_font)
            else:
                _draw_task_content(c, margin + indent, y, line, base_font, task_font)
            y -= line_spacing
        if workspace_lines > 0:
            if y - workspace_block_h < margin + footer_reserved:
                y = start_new_page()
            y -= 4
            y = _draw_workspace_lines(
                c,
                x_start=margin + 12,
                x_end=width - margin,
                y_top=y,
                n_lines=workspace_lines,
                gap=workspace_gap,
                color=muted_color,
            )
        y -= task_spacing
    return y, page_num


# --------------------------------------------------------------------
# Główna funkcja – buduje PDF i zwraca bytes
# --------------------------------------------------------------------


def build_worksheet_pdf_bytes(
    meta: WorksheetMeta,
    tasks: Iterable[str],
    layout: Optional[dict | ResolvedWorksheetLayout] = None,
    image_bytes: Optional[bytes] = None,
    task_images: Optional[list] = None,
    answers: Optional[list[str]] = None,
    answer_key: Optional[AnswerKeyResult] = None,
    include_workspace: bool = True,
    worksheet_plan: Optional[WorksheetPlan] = None,
) -> PdfBuildResult:
    """
    Czytelna karta pracy A4 z większą czcionką, emulowanym pogrubieniem,
    kropkowanym miejscem na obliczenia i opcjonalną stroną „Odpowiedzi".

    Parametry:
    - layout: `ResolvedWorksheetLayout` lub pełny dict z `resolve_worksheet_layout()`.
    - image_bytes: jedna ilustracja u góry (gdy `task_images` nie podano).
    - task_images: lista PNG (bytes) – po jednej na zadanie (pusty bytes = pominięcie).
    - answer_key: strukturalny klucz (P0.3) — preferowany.
    - answers: lista tekstów odpowiedzi (legacy); jeśli podana bez `answer_key`,
      dodajemy stronę „ODPOWIEDZI".
    - include_workspace: czy rysować kropkowane linijki na obliczenia (default True).
    """
    if isinstance(layout, ResolvedWorksheetLayout):
        L = layout.to_pdf_dict()
    elif isinstance(layout, dict):
        L = dict(layout)
    else:
        L = dict(PDF_PRINT_DEFAULTS)

    if not include_workspace:
        L["workspace_lines"] = 0

    warnings: list[PdfWarning] = []
    font_reg = register_polish_font()
    if font_reg.warning:
        warnings.append(PdfWarning(code="pdf_font_missing", message=font_reg.warning))

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    base_font = font_reg.regular_name  # bold emulowany przez `_draw_bold`
    bg_color = L.get("background_color", "#FFFFFF")
    text_color = L["text_color"]
    muted_color = L["muted_color"]

    _draw_page_background(c, width, height, bg_color)
    try:
        c.setFillColor(HexColor(text_color))
    except Exception:
        pass
    c.setTitle(meta.title)

    margin = L["margin"]
    y = height - margin
    page_num = 1

    # --- Nagłówek dokumentu: tytuł + profil + szablon wizualny ---
    y = _draw_document_header(
        c,
        meta=meta,
        plan=worksheet_plan,
        x=margin,
        y=y,
        width=width - 2 * margin,
        layout=L,
        font_name=base_font,
        text_color=text_color,
        muted_color=muted_color,
    )

    tasks_list = list(tasks)
    has_task_images = bool(task_images) and len(task_images or []) == len(tasks_list)

    # --- Opcjonalna ilustracja u góry ---
    if image_bytes:
        try:
            img_reader = ImageReader(BytesIO(image_bytes))
            header_w = float(L.get("header_image_width_pt", 160))
            header_h = float(L.get("header_image_height_pt", 90))
            if has_task_images:
                header_w = min(header_w, 120)
                header_h = min(header_h, 58)
            c.drawImage(
                img_reader,
                margin,
                y - header_h,
                width=header_w,
                height=header_h,
                preserveAspectRatio=True,
                mask="auto",
            )
            y -= header_h + 14
        except Exception:
            pass

    y, page_num = _draw_tasks_body(
        c,
        y=y,
        page_num=page_num,
        width=width,
        height=height,
        margin=margin,
        layout=L,
        tasks_list=tasks_list,
        task_images=task_images,
        has_task_images=has_task_images,
        worksheet_plan=worksheet_plan,
        base_font=base_font,
        text_color=text_color,
        muted_color=muted_color,
        bg_color=bg_color,
    )

    _draw_footer(c, width, margin, page_num, base_font, text_color)
    c.showPage()

    # --- Strona „ODPOWIEDZI" ---
    section_w = width - 2 * margin
    line_spacing = L["line_spacing"]
    answer_summary: Optional[str] = None
    answer_lines: Optional[list[str]] = None
    if answer_key is not None and len(answer_key.items) == len(tasks_list):
        answer_lines = answer_key.display_values()
        answer_summary = answer_key.summary_pl()
    elif answers and len(answers) == len(tasks_list):
        answer_lines = list(answers)

    if answer_lines is not None:
        page_num += 1
        _draw_page_background(c, width, height, bg_color)
        try:
            c.setFillColor(HexColor(text_color))
        except Exception:
            pass

        y_ans = height - margin
        _draw_bold(c, margin, y_ans, "Karta odpowiedzi", base_font, L["title_font_size"])
        y_ans -= L["title_spacing"]

        try:
            c.setFillColor(HexColor(muted_color))
        except Exception:
            pass
        c.setFont(base_font, L["metadata_font_size"])
        c.drawString(margin, y_ans,
                     f"Klasa: {meta.grade}   |   Zakres: {meta.topic_range}")
        try:
            c.setFillColor(HexColor(text_color))
        except Exception:
            pass
        y_ans -= L["metadata_spacing"]

        _draw_section_header(c, margin, y_ans, "Odpowiedzi",
                             base_font, L["section_font_size"],
                             section_w, text_color)
        y_ans -= L["section_spacing"]

        if answer_summary:
            try:
                c.setFillColor(HexColor(muted_color))
            except Exception:
                pass
            c.setFont(base_font, max(9, L["metadata_font_size"] - 1))
            c.drawString(margin, y_ans, answer_summary)
            try:
                c.setFillColor(HexColor(text_color))
            except Exception:
                pass
            y_ans -= L["metadata_spacing"]

        for i, ans in enumerate(answer_lines, start=1):
            if y_ans < margin + 40:
                _draw_footer(c, width, margin, page_num, base_font, text_color)
                c.showPage()
                page_num += 1
                _draw_page_background(c, width, height, bg_color)
                try:
                    c.setFillColor(HexColor(text_color))
                except Exception:
                    pass
                y_ans = height - margin

            prefix = f"{i}."
            _draw_bold(c, margin, y_ans, prefix, base_font, L["answer_font_size"])
            prefix_w = _string_width(prefix, base_font, L["answer_font_size"]) + 6
            _draw_task_content(c, margin + prefix_w, y_ans, str(ans),
                               base_font, L["answer_font_size"])
            y_ans -= line_spacing
        _draw_footer(c, width, margin, page_num, base_font, text_color)
        c.showPage()

    c.save()
    return PdfBuildResult(pdf_bytes=buffer.getvalue(), warnings=tuple(warnings))


# --------------------------------------------------------------------
# Helpery zawartości linii (treść zadania – tekst + ułamki)
# --------------------------------------------------------------------


def _draw_task_content(c, x: float, y: float, line: str,
                       font_name: str, font_size: float) -> None:
    """Rysuje treść zadania: jeśli zawiera ułamek `a/b`, rysuje go z kreską."""
    if re.search(r"\d+/\d+", line):
        _draw_task_line_with_fractions(c, x, y, line, font_name, font_size)
    else:
        c.setFont(font_name, font_size)
        c.drawString(x, y, line)


def _wrap_text_by_width(
    text: str,
    *,
    max_width: float,
    font_name: str,
    font_size: float,
    continuation_width: float | None = None,
) -> list[str]:
    """Zawija tekst według realnej szerokości w PDF, nie liczby znaków."""
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current = ""
    continuation_width = continuation_width or max_width

    def limit_for_current_line() -> float:
        return max_width if not lines else continuation_width

    def fits(value: str) -> bool:
        return _string_width(value, font_name, font_size) <= limit_for_current_line()

    def split_long_word(word: str) -> list[str]:
        pieces: list[str] = []
        current_piece = ""
        for ch in word:
            candidate = current_piece + ch
            if current_piece and not fits(candidate):
                pieces.append(current_piece)
                current_piece = ch
            else:
                current_piece = candidate
        if current_piece:
            pieces.append(current_piece)
        return pieces or [word]

    for word in words:
        candidate = f"{current} {word}".strip()
        if fits(candidate):
            current = candidate
            continue

        if current:
            lines.append(current)
            current = ""

        if fits(word):
            current = word
        else:
            parts = split_long_word(word)
            lines.extend(parts[:-1])
            current = parts[-1]

    if current:
        lines.append(current)
    return lines


def _wrap_text(text: str, max_chars: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []

    for w in words:
        candidate = (" ".join(current + [w])).strip()
        if len(candidate) <= max_chars:
            current.append(w)
        else:
            if current:
                lines.append(" ".join(current))
                current = [w]
            else:
                lines.append(w[:max_chars])
                current = [w[max_chars:]] if len(w) > max_chars else []
    if current:
        lines.append(" ".join(current))
    return lines


def _split_line_into_segments(line: str) -> list[tuple]:
    """Dzieli linię na segmenty: `("text", str)` lub `("frac", num, den)`."""
    parts = re.split(r"(\d+/\d+)", line)
    segments: list[tuple] = []
    for p in parts:
        if re.match(r"^\d+/\d+$", p):
            num, den = p.split("/")
            segments.append(("frac", int(num), int(den)))
        elif p:
            segments.append(("text", p))
    return segments


def _draw_fraction(c, x: float, y: float, num: int, den: int,
                   font_name: str, font_size: float) -> float:
    """Ułamek szkolny: licznik nad kreską, mianownik pod. Zwraca szerokość."""
    frac_size = max(6, font_size * 0.85)
    num_str, den_str = str(num), str(den)
    w_num = pdfmetrics.stringWidth(num_str, font_name, frac_size)
    w_den = pdfmetrics.stringWidth(den_str, font_name, frac_size)
    frac_width = max(w_num, w_den) + 6
    gap = 1.0
    bar_y = y
    num_baseline = y + gap + frac_size * 0.25
    den_baseline = y - gap - frac_size * 0.8
    c.setFont(font_name, frac_size)
    c.drawString(x + (frac_width - w_num) / 2, num_baseline, num_str)
    c.drawString(x + (frac_width - w_den) / 2, den_baseline, den_str)
    c.setLineWidth(0.8)
    c.line(x + 2, bar_y, x + frac_width - 2, bar_y)
    return frac_width


def _draw_task_line_with_fractions(c, x: float, y: float, line: str,
                                   font_name: str, font_size: float) -> None:
    """Linia zadania z ułamkami a/b – każda taka liczba rysowana z kreską."""
    segments = _split_line_into_segments(line)
    if len(segments) == 1 and segments[0][0] == "text":
        c.setFont(font_name, font_size)
        c.drawString(x, y, segments[0][1])
        return
    c.setFont(font_name, font_size)
    curr_x = x
    for seg in segments:
        if seg[0] == "text":
            c.drawString(curr_x, y, seg[1])
            curr_x += pdfmetrics.stringWidth(seg[1], font_name, font_size)
        else:
            curr_x += _draw_fraction(c, curr_x, y, seg[1], seg[2], font_name, font_size)
            c.setFont(font_name, font_size)
