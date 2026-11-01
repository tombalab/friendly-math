"""Q2: gęstość karty — siatka zadań i liczba stron ucznia."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.domain.educational_strategy import WorksheetBlock
from app.domain.profile_catalog import resolve_profile
from app.domain.worksheet_contract import WorksheetRequest
from app.domain.worksheet_layout import resolve_worksheet_layout
from app.pdf.fonts import register_polish_font
from app.pdf.generator import _section_columns
from app.worksheet.service import WorksheetService

fitz = pytest.importorskip("fitz")

SIMPLE_TASKS = [f"Policz: {a} + {b} = ____" for a, b in [(3, 4), (5, 2), (6, 1), (4, 4), (7, 2), (2, 8), (9, 1), (3, 6)]]


def _student_page_count(profile_id: str, tasks: list[str], tmp_path, *, grade: int = 2) -> int:
    service = WorksheetService(output_dir=tmp_path / "out", history_dir=tmp_path / "history")
    with patch("app.worksheet.service.generate_tasks", return_value={"tasks": list(tasks)}):
        result = service.generate(
            WorksheetRequest(
                grade=grade,
                topic_label="dodawanie",
                profile_id=profile_id,
                number_of_tasks=len(tasks),
                include_illustration=True,
                include_workspace=True,
                include_answers=True,
            )
        )
    assert result.pdf_bytes
    doc = fitz.open(stream=result.pdf_bytes, filetype="pdf")
    try:
        return sum(1 for page in doc if "Karta odpowiedzi" not in page.get_text())
    finally:
        doc.close()


@pytest.mark.parametrize(
    "profile_id",
    ["standardowy", "ADHD", "dyskalkulia", "dysleksja", "trudności grafomotoryczne", "zdolny"],
)
def test_eight_simple_tasks_fit_on_two_student_pages(profile_id, tmp_path):
    assert _student_page_count(profile_id, SIMPLE_TASKS, tmp_path) <= 2


def _block(text: str) -> WorksheetBlock:
    return WorksheetBlock("t", 0, "Oblicz", text, "compute", "write", "core", "", 1)


def _columns(profile_id: str, texts: list[str]) -> int:
    layout = resolve_worksheet_layout(resolve_profile(profile_id), grade=2, number_of_tasks=len(texts)).to_pdf_dict()
    font = register_polish_font().regular_name
    return _section_columns(tuple(_block(t) for t in texts), 485, 10, layout, font)


def test_simple_tasks_use_grid_and_word_problems_stay_full_width():
    assert _columns("standardowy", ["3 + 4 = ____", "5 + 2 = ____", "6 + 1 = ____"]) == 3
    word = "Na półce było 200 książek. Zabrano 75, a potem dołożono 30 nowych. Ile książek jest teraz na półce?"
    assert _columns("standardowy", [word, "3 + 4 = ____"]) == 1


def test_low_stimuli_profiles_get_at_most_two_columns():
    for pid in ("ADHD", "dyskalkulia", "trudności grafomotoryczne"):
        layout = resolve_worksheet_layout(resolve_profile(pid), grade=2, number_of_tasks=8)
        assert layout.max_columns == 2, pid
        assert _columns(pid, ["3 + 4 = ____", "5 + 2 = ____", "6 + 1 = ____"]) <= 2
    assert resolve_worksheet_layout(resolve_profile("standardowy"), grade=2, number_of_tasks=8).max_columns == 3
