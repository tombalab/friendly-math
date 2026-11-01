"""Q1: karta ucznia bez treści dla nauczyciela, klucz odpowiedzi z treścią zadań."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.domain.educational_strategy import WorksheetBlock
from app.domain.profile_catalog import get_profile
from app.domain.worksheet_contract import WorksheetRequest
from app.pdf.generator import _answer_area_height, _uses_inline_answer
from app.worksheet.service import WorksheetService

fitz = pytest.importorskip("fitz")

TASKS = ["Policz: 3 + 4 = ____", "Policz: 5 + 2 = ____", "Policz: 6 + 1 = ____"]


def _page_texts(profile_id: str, tmp_path) -> list[str]:
    service = WorksheetService(output_dir=tmp_path / "out", history_dir=tmp_path / "history")
    with patch("app.worksheet.service.generate_tasks", return_value={"tasks": list(TASKS)}):
        result = service.generate(
            WorksheetRequest(
                grade=2,
                topic_label="dodawanie",
                profile_id=profile_id,
                number_of_tasks=len(TASKS),
                include_illustration=False,
                include_workspace=True,
                include_answers=True,
            )
        )
    assert result.pdf_bytes
    doc = fitz.open(stream=result.pdf_bytes, filetype="pdf")
    try:
        return [page.get_text() for page in doc]
    finally:
        doc.close()


@pytest.mark.parametrize("profile_id", ["dyskalkulia", "ADHD", "dysleksja", "standardowy"])
def test_student_pages_hide_profile_and_teacher_notes(profile_id, tmp_path):
    pages = _page_texts(profile_id, tmp_path)
    student_pages = [t for t in pages if "Karta odpowiedzi" not in t]
    answer_pages = [t for t in pages if "Karta odpowiedzi" in t]
    assert student_pages and answer_pages

    label = get_profile(profile_id).ui_label
    student_text = "\n".join(student_pages)
    for forbidden in ("Profil", "Jak pracujemy", "Rola grafiki", "Strategia"):
        assert forbidden not in student_text, f"{profile_id}: „{forbidden}” na karcie ucznia"
    if profile_id != "standardowy":
        assert label not in student_text, f"{profile_id}: nazwa profilu na karcie ucznia"
    assert "Imię i nazwisko" in student_pages[0]
    assert "Data" in student_pages[0]

    answer_text = "\n".join(answer_pages)
    assert "dla nauczyciela" in answer_text
    assert "Profil" in answer_text
    assert "3 + 4" in answer_text, "klucz odpowiedzi bez treści zadania"


def _block(text: str, mode: str = "write") -> WorksheetBlock:
    return WorksheetBlock("t", 0, "Policz", text, "compute", mode, "core", "", 2)


def test_inline_blank_replaces_answer_box():
    layout = {"workspace_lines": 0, "workspace_line_gap": 18, "answer_box_height": 34}
    assert _uses_inline_answer(_block("2 + 3 = ____"))
    assert _answer_area_height(_block("2 + 3 = ____"), layout) == 0
    assert not _uses_inline_answer(_block("Ile jabłek ma Ola?"))
    assert _answer_area_height(_block("Ile jabłek ma Ola?"), layout) >= 34
    # Inne tryby odpowiedzi (np. zaznaczanie) zachowują własne pole.
    assert not _uses_inline_answer(_block("2 + 3 = ____", mode="checkbox"))


def test_inline_blank_keeps_workspace_lines_when_enabled():
    layout = {"workspace_lines": 2, "workspace_line_gap": 18, "answer_box_height": 34}
    assert _answer_area_height(_block("2 + 3 = ____"), layout) == 36
