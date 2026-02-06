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
    }


# Rozmiar ilustracji na stronie (pt; ~140 pt ≈ 5 cm)
_IMAGE_WIDTH_PT = 140
_IMAGE_HEIGHT_PT = 80


def build_worksheet_pdf_bytes(
    meta: WorksheetMeta,
    tasks: Iterable[str],
    layout: Optional[dict] = None,
    image_bytes: Optional[bytes] = None,
) -> bytes:
    """
    PDF v0: nagłówek + lista zadań jako tekst, A4.
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

    try:
        c.setFillColor(HexColor(L["text_color"]))
    except Exception:
        pass

    c.setTitle(meta.title)

    margin = L["margin"]
    y = height - margin

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
    y -= L["section_spacing"]

    # Lista zadań
    c.setFont(base_font, L["task_font_size"])
    line_spacing = L["line_spacing"]
    task_spacing = L["task_spacing"]

    for i, task in enumerate(list(tasks), start=1):
        lines = _wrap_text(f"{i}. {task}", max_chars=95)
        for line in lines:
            if y < margin:
                c.showPage()
                y = height - margin
                c.setFont(base_font, L["task_font_size"])
            c.drawString(margin, y, line)
            y -= line_spacing
        y -= task_spacing

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