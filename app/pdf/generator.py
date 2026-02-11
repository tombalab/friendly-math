from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable, Optional

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
) -> bytes:
    """
    PDF v1: czytelna karta pracy (Day 9).
    - Nagłówek + metadane + ilustracja + lista zadań, A4.
    - Tło strony (background_color z layoutu).
    - Separator pod "Zadania:".
    - Dynamiczne łamanie tekstu (dostosowane do szerokości strony i fontu).
    - Stopka z numerem strony.
    layout: opcjonalny dict z app.ai.layout_generator (font size, spacing, kolory).
    image_bytes: opcjonalna ilustracja PNG (Day 8) – rysowana pod metadanymi.
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

    # Ilustracja (Day 8) – jedna grafika low-stimuli pod metadanymi
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
    y -= 8  # Mały odstęp przed linią

    # Separator (Day 9) – cienka linia pod "Zadania:"
    try:
        c.setStrokeColor(HexColor(L["text_color"]))
        c.setLineWidth(0.5)
        c.line(margin, y, width - margin, y)
    except Exception:
        pass
    y -= L["section_spacing"] - 8  # Odstęp po linii (zachowujemy section_spacing)

    # Lista zadań
    c.setFont(base_font, L["task_font_size"])
    line_spacing = L["line_spacing"]
    task_spacing = L["task_spacing"]

    # Łamanie tekstu (Day 9) – dostosowanie do szerokości strony i rozmiaru fontu
    # A4 = 595 pt, margin * 2, średnio ~6-7 pt na znak (font 11pt) lub ~8-9 pt (font 14pt)
    available_width = width - 2 * margin
    font_size = L["task_font_size"]
    chars_per_pt = 6.5 if font_size <= 12 else 8.0  # Przybliżenie
    max_chars = int(available_width / chars_per_pt) - 5  # -5 dla bezpieczeństwa
    max_chars = max(60, min(max_chars, 85))  # Ograniczenie: 60-85 znaków

    for i, task in enumerate(list(tasks), start=1):
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