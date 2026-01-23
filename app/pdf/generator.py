from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable

from reportlab.lib.pagesizes import A4  # pyright: ignore[reportMissingModuleSource]
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


def build_worksheet_pdf_bytes(meta: WorksheetMeta, tasks: Iterable[str]) -> bytes:
    """
    PDF v0: nagłówek + lista zadań jako tekst, A4.
    Zwraca bytes (łatwe do zapisu i do Streamlit download).
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Rejestr czcionki z polskimi znakami
    base_font, bold_font = _register_font()

    c.setTitle(meta.title)

    margin = 50
    y = height - margin

    # Nagłówek (używamy "bold_font", ale to będzie ta sama czcionka)
    c.setFont(bold_font, 16)
    c.drawString(margin, y, meta.title)
    y -= 24

    # Metadane (mały font)
    c.setFont(base_font, 10)
    c.drawString(
        margin,
        y,
        f"Klasa: {meta.grade}   Zakres: {meta.topic_range}   Profil: {meta.student_profile}",
    )
    y -= 20

    # Sekcja "Zadania:"
    c.setFont(base_font, 12)
    c.drawString(margin, y, "Zadania: (ąęłńśćźż)?")
    y -= 18

    # Lista zadań
    c.setFont(base_font, 11)

    for i, task in enumerate(list(tasks), start=1):
        # proste łamanie: tnij na linie ~95 znaków (v0)
        lines = _wrap_text(f"{i}. {task}", max_chars=95)
        for line in lines:
            if y < margin:
                c.showPage()
                y = height - margin
                c.setFont(base_font, 11)
            c.drawString(margin, y, line)
            y -= 14
        y -= 6

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