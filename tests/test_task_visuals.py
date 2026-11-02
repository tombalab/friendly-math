"""Q5: wektorowe pomoce dydaktyczne zgodne z treścią zadania."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.domain.worksheet_contract import WorksheetRequest
from app.generators.task_visuals import TaskVisual, coins_for_amount, task_visual_for
from app.pdf.generator import WorksheetMeta, build_worksheet_pdf_bytes
from app.worksheet.service import WorksheetService


def test_addition_and_subtraction_use_ten_frames_with_task_numbers():
    v = task_visual_for("Policz: 3 + 4 = ____", "dodawanie", "dyskalkulia")
    assert v == TaskVisual("ten_frame", a=3, b=4, op="+")
    v = task_visual_for("Policz: 9 − 3 = ____", "odejmowanie", "dyskalkulia")
    assert v is not None and (v.kind, v.a, v.b, v.op) == ("ten_frame", 9, 3, "-")


def test_number_line_when_too_many_dots_for_profile():
    # 9 + 8 przekracza limit kropek dla ADHD — zostaje oś 0–20 zamiast braku pomocy.
    v = task_visual_for("Policz: 9 + 8 = ____", "dodawanie", "ADHD")
    assert v is not None and v.kind == "number_line"
    assert task_visual_for("Policz: 15 + 9 = ____", "dodawanie", "ADHD") is None


def test_money_uses_polish_coin_denominations():
    assert coins_for_amount(8) == (5, 2, 1)
    assert coins_for_amount(4) == (2, 2)
    v = task_visual_for("Ile to razem? 5 zł + 2 zł = ____ zł", "pieniądze", "standardowy")
    assert v is not None and v.coin_groups == ((5,), (2,))


def test_clock_hides_hands_when_student_draws_them():
    shown = task_visual_for("Która godzina, gdy mała wskazówka pokazuje 3, a duża 12? ____", "czas", "ADHD", grade=1)
    assert shown is not None and shown.kind == "clock" and shown.hour == 3 and shown.show_hands
    hidden = task_visual_for("Narysuj wskazówki: zegar pokazuje 4:00", "czas", "ADHD", grade=1)
    assert hidden is not None and not hidden.show_hands


def test_division_does_not_reveal_group_size():
    v = task_visual_for("Podziel: 6 : 3 = ____", "dzielenie", "standardowy", grade=3)
    assert v is not None and v.kind == "sharing" and (v.a, v.b) == (6, 3)


def test_topics_without_images_get_no_visual():
    assert task_visual_for("Rozwiąż: x + 3 = 7", "równania", "standardowy", grade=5) is None


fitz = pytest.importorskip("fitz")


def test_pdf_draws_visuals_as_vectors_without_bitmaps():
    tasks = [
        "Policz: 3 + 4 = ____",
        "Policz: 9 + 8 = ____",
        "Ile to razem? 5 zł + 2 zł = ____ zł",
        "Która godzina, gdy mała wskazówka pokazuje 3, a duża 12? ____",
        "Policz: 1/4 + 2/4 = ____",
        "Oblicz obwód prostokąta o bokach 3 cm i 5 cm. Obwód = ____ cm",
        "Policz: 3 × 4 = ____",
        "Podziel: 6 : 3 = ____",
    ]
    visuals = [
        TaskVisual("ten_frame", a=3, b=4),
        TaskVisual("number_line", a=9, b=8),
        TaskVisual("coins", coin_groups=((5,), (2,))),
        TaskVisual("clock", hour=3),
        TaskVisual("fraction", fractions=((1, 4), (2, 4))),
        TaskVisual("rectangle", a=3, b=5),
        TaskVisual("array", a=3, b=4, op="×"),
        TaskVisual("sharing", a=6, b=3, op=":"),
    ]
    from app.domain.educational_strategy import build_worksheet_plan
    from app.domain.profile_catalog import resolve_profile
    from app.domain.topic_catalog import resolve_topic

    plan = build_worksheet_plan(
        tasks=tasks,
        resolved_profile=resolve_profile("dyskalkulia"),
        resolved_topic=resolve_topic("dodawanie", 2),
    )
    meta = WorksheetMeta(title="Test", grade="2", topic_range="mix", student_profile="Dyskalkulia")
    result = build_worksheet_pdf_bytes(meta=meta, tasks=tasks, worksheet_plan=plan, task_visuals=visuals)
    doc = fitz.open(stream=result.pdf_bytes, filetype="pdf")
    try:
        assert all(page.get_images() == [] for page in doc)
        assert "5 zł" in doc[0].get_text() + doc[1].get_text()
    finally:
        doc.close()


def _generate(profile_id: str, tasks: list[str], tmp_path):
    service = WorksheetService(output_dir=tmp_path / "out", history_dir=tmp_path / "history")
    with patch("app.worksheet.service.generate_tasks", return_value={"tasks": list(tasks)}):
        return service.generate(
            WorksheetRequest(
                grade=2,
                topic_label="dodawanie",
                profile_id=profile_id,
                number_of_tasks=len(tasks),
                include_illustration=True,
                include_workspace=True,
                include_answers=False,
            )
        )


TASKS = ["Policz: 3 + 4 = ____", "Policz: 5 + 2 = ____", "Policz: 6 + 1 = ____"]


def test_header_profiles_get_one_matching_visual_instead_of_generic_header(tmp_path):
    result = _generate("standardowy", TASKS, tmp_path)
    assert result.header_image is None
    assert result.task_visuals == [TaskVisual("ten_frame", a=3, b=4), None, None]
    assert result.image_coverage.rendered_count == 1


def test_per_task_profiles_get_visual_for_each_task(tmp_path):
    result = _generate("dyskalkulia", TASKS, tmp_path)
    assert result.header_image is None
    assert [v.kind for v in result.task_visuals] == ["ten_frame"] * 3
    assert result.image_coverage.rendered_count == 3
    assert all(e.rendered for e in result.image_coverage.per_task)
