"""Smoke tests for Polish PDF font (P0.4)."""
from __future__ import annotations

from app.pdf.fonts import bundled_font_path, register_polish_font, resolve_polish_font_path
from app.pdf.generator import PdfBuildResult, WorksheetMeta, build_worksheet_pdf_bytes


POLISH_SAMPLE = "Łódź — ąęść óźż ćń"


def test_font_file_available_in_repo():
    path, source = resolve_polish_font_path()
    assert path is not None, "Brak DejaVuSans.ttf — dodaj assets/fonts/DejaVuSans.ttf"
    assert source == "bundled"
    assert path.is_file()


def test_register_polish_font_ok():
    reg = register_polish_font()
    assert reg.ok is True
    assert reg.warning is None
    assert reg.regular_name == "DejaVuSans"


def test_pdf_build_polish_diacritics_no_font_warning():
    meta = WorksheetMeta(
        title=f"Karta — {POLISH_SAMPLE}",
        grade="3",
        topic_range="ułamki",
        student_profile="standardowy",
    )
    result = build_worksheet_pdf_bytes(
        meta=meta,
        tasks=[f"Zadanie: policz ąęść — odpowiedź: ____ ({POLISH_SAMPLE})"],
    )
    assert isinstance(result, PdfBuildResult)
    assert len(result.pdf_bytes) > 500
    font_warnings = [w for w in result.warnings if w.code == "pdf_font_missing"]
    assert font_warnings == [], (
        f"Oczekiwano braku ostrzeżeń o czcionce, otrzymano: {font_warnings}"
    )


def test_bundled_path_points_at_repo_assets():
    p = bundled_font_path()
    assert p.name == "DejaVuSans.ttf"
    assert "assets" in p.parts and "fonts" in p.parts
