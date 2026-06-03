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

    # --- Nagłówek ---
    _draw_bold(c, margin, y, meta.title, base_font, L["title_font_size"])
    y -= L["title_spacing"]

    # --- Metadane (mniejsza czcionka, kolor stonowany) ---
    try:
        c.setFillColor(HexColor(muted_color))
    except Exception:
        pass
    c.setFont(base_font, L["metadata_font_size"])
    c.drawString(
        margin, y,
        f"Klasa: {meta.grade}   |   Zakres: {meta.topic_range}   |   Profil: {meta.student_profile}",
    )
    try:
        c.setFillColor(HexColor(text_color))
    except Exception:
        pass
    y -= L["metadata_spacing"]

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

    # --- Sekcja „ZADANIA" ---
    section_w = width - 2 * margin
    _draw_section_header(c, margin, y, "Zadania",
                         base_font, L["section_font_size"],
                         section_w, text_color)
    y -= L["section_spacing"]

    # --- Lista zadań ---
    task_font = L["task_font_size"]
    line_spacing = L["line_spacing"]
    task_spacing = L["task_spacing"]
    workspace_lines = L["workspace_lines"]
    workspace_gap = L["workspace_line_gap"]

    available_width = width - 2 * margin

    task_img_width_pt = available_width
    task_aspect = L.get("task_image_aspect", 100 / 480)
    task_img_height_pt = max(60, int(task_img_width_pt * task_aspect))

    footer_reserved = 40
    page_body_h = height - 2 * margin - footer_reserved

    def _start_new_page() -> float:
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

    def _new_page_if_block_will_not_fit(y_now: float, block_h: float) -> float:
        if y_now - block_h < margin + footer_reserved and block_h <= page_body_h:
            return _start_new_page()
        if y_now < margin + footer_reserved:
            return _start_new_page()
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
        has_current_image = bool(has_task_images and task_images[i - 1])
        image_block_h = task_img_height_pt + 8 if has_current_image else 0
        workspace_block_h = 4 + workspace_lines * workspace_gap if workspace_lines > 0 else 0
        block_h = image_block_h + len(lines) * line_spacing + workspace_block_h + task_spacing
        y = _new_page_if_block_will_not_fit(y, block_h)

        # 1) Ilustracja per zadanie (jeśli mamy)
        if has_current_image:
            try:
                img_reader = ImageReader(BytesIO(task_images[i - 1]))
                c.drawImage(
                    img_reader,
                    margin, y - task_img_height_pt,
                    width=task_img_width_pt, height=task_img_height_pt,
                    preserveAspectRatio=True,
                    mask="auto",
                )
                y -= task_img_height_pt + 8
            except Exception:
                pass

        # 2) Linia zadania: pogrubiony numer „1." + zwykła treść.
        for line_idx, line in enumerate(lines):
            if y < margin + footer_reserved:
                y = _start_new_page()
            if line_idx == 0:
                _draw_bold(c, margin, y, prefix, base_font, task_font)
                _draw_task_content(c, margin + prefix_w, y, line, base_font, task_font)
            else:
                # Wcięcie kontynuacji – wyrównane do treści, nie do numeru.
                _draw_task_content(c, margin + indent, y, line, base_font, task_font)
            y -= line_spacing

        # 3) Miejsce na obliczenia (kropkowane linijki)
        if workspace_lines > 0:
            if y - workspace_block_h < margin + footer_reserved:
                y = _start_new_page()
            y -= 4  # mały oddech między tekstem zadania a linijkami
            y = _draw_workspace_lines(
                c,
                x_start=margin + 12, x_end=width - margin,
                y_top=y, n_lines=workspace_lines, gap=workspace_gap,
                color=muted_color,
            )

        y -= task_spacing

    _draw_footer(c, width, margin, page_num, base_font, text_color)
    c.showPage()

    # --- Strona „ODPOWIEDZI" ---
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
