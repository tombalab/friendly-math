from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable, Optional

import re

from reportlab.lib.pagesizes import A4  # pyright: ignore[reportMissingModuleSource]
from reportlab.lib.colors import HexColor  # pyright: ignore[reportMissingModuleSource]
from reportlab.lib.utils import ImageReader  # pyright: ignore[reportMissingModuleSource]
from reportlab.pdfbase import pdfmetrics  # pyright: ignore[reportMissingModuleSource]
from reportlab.pdfbase.ttfonts import TTFont  # pyright: ignore[reportMissingModuleSource]
from reportlab.pdfgen import canvas  # pyright: ignore[reportMissingModuleSource]


@dataclass(frozen=True)
class WorksheetMeta:
    title: str
    grade: str
    topic_range: str
    student_profile: str


# Używamy jednej czcionki z polskimi znakami
_FONT_NAME = "DejaVuSans"
_FONT_PATH = Path("assets/fonts/DejaVuSans.ttf")


def _register_font() -> tuple[str, str]:
    """
    Rejestruje czcionkę TTF z polskimi znakami.
    Zwraca tuple (font_name, font_bold_name) do użycia w setFont().
    Fallback do Helvetica jeśli plik nie istnieje.
    """
    base_font = "Helvetica"
    bold_font = "Helvetica-Bold"

    try:
        if _FONT_PATH.exists():
            pdfmetrics.registerFont(TTFont(_FONT_NAME, str(_FONT_PATH)))
            base_font = _FONT_NAME
            # Nie mamy osobnego pliku bold, więc bold = regular
            bold_font = _FONT_NAME
        else:
            # To tylko ostrzeżenie w konsoli, PDF i tak się wygeneruje
            print(
                f"⚠️ Font file not found: {_FONT_PATH}. "
                "Using Helvetica (may lack Polish characters)."
            )
    except Exception as e:
        print(f"⚠️ Error registering font: {e}. Using Helvetica fallback.")

    return base_font, bold_font


def _default_layout() -> dict:
    """Domyślny layout gdy nie przekazano layoutu z AI (Day 7)."""
    return {
        "title_font_size": 16,
        "metadata_font_size": 10,
        "section_font_size": 12,
        "task_font_size": 11,
        "margin": 50,
        "title_spacing": 24,
        "metadata_spacing": 20,
        "section_spacing": 18,
        "task_spacing": 6,
        "line_spacing": 14,
        "text_color": "#000000",
        "background_color": "#FFFFFF",
    }


def _profile_layout(profile: str) -> dict:
    """Layout dla profili wymagających większych fontów i odstępów (dyskalkulia, ADHD, trudności)."""
    return {
        "title_font_size": 20,
        "metadata_font_size": 12,
        "section_font_size": 14,
        "task_font_size": 14,
        "margin": 60,
        "title_spacing": 32,
        "metadata_spacing": 26,
        "section_spacing": 24,
        "task_spacing": 14,
        "line_spacing": 20,
        "background_color": "#fafafa",  # Bardzo jasne szare tło dla low-stimuli (Day 9)
    }


# Rozmiar ilustracji na stronie (pt; ~140 pt ≈ 5 cm)
_IMAGE_WIDTH_PT = 140
_IMAGE_HEIGHT_PT = 80

# Day 11: ilustracja przy zadaniu – pełna szerokość treści (bez ucinania)
# Wysokość proporcjonalna do generowanego obrazka 480×100 px
_TASK_IMAGE_ASPECT = 100 / 480  # height/width


def _draw_page_background(canvas_obj, width: float, height: float, bg_color: str) -> None:
    """Rysuje tło strony jeśli nie jest białe (Day 9)."""
    if bg_color.upper() not in ("#FFFFFF", "WHITE", "#FFF"):
        try:
            canvas_obj.setFillColor(HexColor(bg_color))
            canvas_obj.rect(0, 0, width, height, fill=1, stroke=0)
        except Exception:
            pass


def _draw_footer(canvas_obj, width: float, margin: float, page_num: int, font_name: str, text_color: str) -> None:
    """Rysuje stopkę z numerem strony na dole (Day 9)."""
    try:
        canvas_obj.setFillColor(HexColor(text_color))
        canvas_obj.setFont(font_name, 8)
        footer_text = f"Friendly Math — strona {page_num}"
        canvas_obj.drawRightString(width - margin, 20, footer_text)
    except Exception:
        pass


def build_worksheet_pdf_bytes(
    meta: WorksheetMeta,
    tasks: Iterable[str],
    layout: Optional[dict] = None,
    image_bytes: Optional[bytes] = None,
    task_images: Optional[list] = None,
) -> bytes:
    """
    PDF v1: czytelna karta pracy (Day 9). Day 11: ilustracja per zadanie.
    - Nagłówek + metadane + (opcjonalnie jedna ilustracja u góry LUB ilustracje przy zadaniach) + lista zadań, A4.
    - task_images: lista PNG (bytes) – jedna na zadanie; jeśli podana, rysowana przy każdym zadaniu (bez jednej u góry).
    - image_bytes: jedna ilustracja pod metadanymi (używana tylko gdy task_images nie jest podane).
    Zwraca bytes (łatwe do zapisu i do Streamlit download).
    """
    L = _default_layout()
    if layout:
        for k, v in layout.items():
            if k in L:
                L[k] = v
    # Wymuszenie większych fontów i odstępów dla dyskalkulia/ADHD/trudności (profil ma pierwszeństwo)
    if meta.student_profile in ["dyskalkulia", "ADHD", "trudności w nauce"]:
        L.update(_profile_layout(meta.student_profile))

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    base_font, bold_font = _register_font()
    bg_color = L.get("background_color", "#FFFFFF")

    # Tło strony (Day 9) – pierwsza strona
    _draw_page_background(c, width, height, bg_color)

    try:
        c.setFillColor(HexColor(L["text_color"]))
    except Exception:
        pass

    c.setTitle(meta.title)

    margin = L["margin"]
    y = height - margin
    page_num = 1

    # Nagłówek
    c.setFont(bold_font, L["title_font_size"])
    c.drawString(margin, y, meta.title)
    y -= L["title_spacing"]

    # Metadane
    c.setFont(base_font, L["metadata_font_size"])
    c.drawString(
        margin,
        y,
        f"Klasa: {meta.grade}   Zakres: {meta.topic_range}   Profil: {meta.student_profile}",
    )
    y -= L["metadata_spacing"]

    # Ilustracja (Day 8/11): jedna u góry tylko gdy NIE ma ilustracji per zadanie
    tasks_list = list(tasks)
    if (not task_images or len(task_images) != len(tasks_list)) and image_bytes:
        if image_bytes:
            try:
                img_reader = ImageReader(BytesIO(image_bytes))
                c.drawImage(img_reader, margin, y - _IMAGE_HEIGHT_PT, width=_IMAGE_WIDTH_PT, height=_IMAGE_HEIGHT_PT)
                y -= _IMAGE_HEIGHT_PT + 12
            except Exception:
                pass

    # Sekcja "Zadania:"
    c.setFont(base_font, L["section_font_size"])
    c.drawString(margin, y, "Zadania:")
    y -= 18  # Odstęp przed separatorem (padding)

    # Separator (Day 9) – cienka linia pod "Zadania:" z większym paddingiem
    try:
        c.setStrokeColor(HexColor(L["text_color"]))
        c.setLineWidth(0.5)
        c.line(margin, y, width - margin, y)
    except Exception:
        pass
    y -= 18  # Odstęp po separatorze (padding) – oddzielenie od listy zadań

    # Lista zadań
    c.setFont(base_font, L["task_font_size"])
    line_spacing = L["line_spacing"]
    task_spacing = L["task_spacing"]

    # Łamanie tekstu (Day 9) – dostosowanie do szerokości strony i rozmiaru fontu
    available_width = width - 2 * margin
    font_size = L["task_font_size"]
    chars_per_pt = 6.5 if font_size <= 12 else 8.0  # Przybliżenie
    max_chars = int(available_width / chars_per_pt) - 5  # -5 dla bezpieczeństwa
    max_chars = max(60, min(max_chars, 85))  # Ograniczenie: 60-85 znaków

    # Day 11: ilustracja przy zadaniu – pełna szerokość treści, wysokość proporcjonalna (wszystko widoczne)
    task_img_width_pt = available_width
    task_img_height_pt = max(60, int(task_img_width_pt * _TASK_IMAGE_ASPECT))

    for i, task in enumerate(tasks_list, start=1):
        # Day 11: ilustracja przy zadaniu (pełna szerokość, bez ucinania)
        if task_images and i <= len(task_images) and task_images[i - 1]:
            try:
                img_reader = ImageReader(BytesIO(task_images[i - 1]))
                c.drawImage(
                    img_reader,
                    margin,
                    y - task_img_height_pt,
                    width=task_img_width_pt,
                    height=task_img_height_pt,
                )
                y -= task_img_height_pt + 10
            except Exception:
                pass
        lines = _wrap_text(f"{i}. {task}", max_chars=max_chars)
        for line in lines:
            if y < margin + 30:  # +30 dla stopki
                _draw_footer(c, width, margin, page_num, base_font, L["text_color"])
                c.showPage()
                page_num += 1
                _draw_page_background(c, width, height, bg_color)  # Tło na kolejnych stronach
                try:
                    c.setFillColor(HexColor(L["text_color"]))
                except Exception:
                    pass
                y = height - margin
                c.setFont(base_font, L["task_font_size"])
            if re.search(r"\d+/\d+", line):
                _draw_task_line_with_fractions(c, margin, y, line, base_font, font_size)
            else:
                c.drawString(margin, y, line)
            y -= line_spacing
        y -= task_spacing

    # Stopka na ostatniej stronie
    _draw_footer(c, width, margin, page_num, base_font, L["text_color"])
    c.showPage()
    c.save()

    return buffer.getvalue()


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
                # pojedyncze bardzo długie słowo
                lines.append(w[:max_chars])
                current = [w[max_chars:]] if len(w) > max_chars else []
    if current:
        lines.append(" ".join(current))
    return lines


def _split_line_into_segments(line: str) -> list[tuple]:
    """
    Dzieli linię na segmenty: ("text", str) lub ("frac", num, den).
    Ułamki w formacie 1/2, 3/4 są rysowane szkolnie (licznik, kreska, mianownik).
    """
    parts = re.split(r"(\d+/\d+)", line)
    segments: list[tuple] = []
    for p in parts:
        if re.match(r"^\d+/\d+$", p):
            num, den = p.split("/")
            segments.append(("frac", int(num), int(den)))
        elif p:
            segments.append(("text", p))
    return segments


def _draw_fraction(
    c, x: float, y: float, num: int, den: int, font_name: str, font_size: float
) -> float:
    """
    Rysuje ułamek w stylu szkolnym: licznik nad kreską, mianownik pod.
    y = baseline linii tekstu. Zwraca szerokość ułamka w pt.
    """
    frac_size = max(6, font_size * 0.85)
    num_str, den_str = str(num), str(den)
    w_num = pdfmetrics.stringWidth(num_str, font_name, frac_size)
    w_den = pdfmetrics.stringWidth(den_str, font_name, frac_size)
    frac_width = max(w_num, w_den) + 6
    gap = 2.0
    # Kreska ułamkowa nieco poniżej baseline linii; licznik nad kreską, mianownik pod
    bar_y = y - frac_size * 0.5
    num_baseline = bar_y + gap + frac_size * 0.75
    den_baseline = bar_y - gap - frac_size * 0.25
    c.setFont(font_name, frac_size)
    c.drawString(x + (frac_width - w_num) / 2, num_baseline, num_str)
    c.drawString(x + (frac_width - w_den) / 2, den_baseline, den_str)
    c.setLineWidth(0.8)
    c.line(x + 2, bar_y, x + frac_width - 2, bar_y)
    return frac_width


def _draw_task_line_with_fractions(
    c, x: float, y: float, line: str, font_name: str, font_size: float
) -> None:
    """
    Rysuje linię zadania; jeśli zawiera ułamki (np. 1/2), rysuje je z kreską ułamkową.
    """
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