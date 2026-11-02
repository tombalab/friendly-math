"""Q4: szablon karty wynika z klasy, profil go modyfikuje."""
from __future__ import annotations

import pytest

from app.domain.educational_strategy import build_worksheet_plan, grade_band, resolve_template
from app.domain.profile_catalog import resolve_profile
from app.domain.topic_catalog import resolve_topic
from app.domain.worksheet_layout import resolve_worksheet_layout
from app.pdf.generator import WorksheetMeta, build_worksheet_pdf_bytes

TASKS = ["Policz: 12 × 4 = ____", "Policz: 15 × 6 = ____", "Policz: 25 × 4 = ____", "Policz: 18 × 5 = ____"]


def test_grade_band_boundaries():
    assert [grade_band(g) for g in range(1, 9)] == ["early"] * 3 + ["middle"] * 3 + ["upper"] * 2


def test_auto_template_follows_grade_then_profile():
    assert resolve_template(None, profile_group="adhd", grade=2).template_id == "adventure"
    assert resolve_template(None, profile_group="adhd", grade=5).template_id == "classic"
    assert resolve_template(None, profile_group="dyskalkulia", grade=5).template_id == "friendly_minimal"
    for group in ("adhd", "dyskalkulia", "standard", "grafomotoryka"):
        assert resolve_template(None, profile_group=group, grade=8).template_id == "school"
    # Wybór nauczyciela ma pierwszeństwo.
    assert resolve_template("space", profile_group="standard", grade=8).template_id == "space"


def _plan(profile: str, grade: int):
    return build_worksheet_plan(
        tasks=TASKS,
        resolved_profile=resolve_profile(profile),
        resolved_topic=resolve_topic("mnożenie", grade),
    )


def test_older_grades_drop_playful_section_names():
    early = [s.title for s in _plan("ADHD", 2).sections]
    assert any("Misje" in t for t in early)
    for grade in (5, 8):
        titles = " ".join(s.title for s in _plan("ADHD", grade).sections)
        assert "Misje" not in titles and "Bonus" not in titles, grade
    upper = _plan("standardowy", 8)
    assert upper.grade_band == "upper"
    assert upper.sections[0].title.startswith("Część A")
    assert upper.sections[-1].blocks[0].options == ("rozumiem", "częściowo", "potrzebuję pomocy")


def test_upper_grades_get_smaller_titles_but_keep_profile_task_font():
    dys2 = resolve_worksheet_layout(resolve_profile("dyskalkulia"), grade=2, number_of_tasks=4)
    dys8 = resolve_worksheet_layout(resolve_profile("dyskalkulia"), grade=8, number_of_tasks=4)
    std8 = resolve_worksheet_layout(resolve_profile("standardowy"), grade=8, number_of_tasks=4)
    assert dys8.title_font_size <= 18 < dys2.title_font_size
    assert dys8.section_font_size <= 13
    # Profil nadal decyduje o czcionce zadań.
    assert dys8.task_font_size == dys2.task_font_size > std8.task_font_size


fitz = pytest.importorskip("fitz")


def _first_page_text(grade: int) -> str:
    plan = _plan("standardowy", grade)
    layout = resolve_worksheet_layout(resolve_profile("standardowy"), grade=grade, number_of_tasks=4, worksheet_plan=plan)
    meta = WorksheetMeta(title=f"Karta pracy – klasa {grade}", grade=str(grade), topic_range="mnożenie", student_profile="standardowy")
    pdf = build_worksheet_pdf_bytes(meta=meta, tasks=(t for t in TASKS), layout=layout, worksheet_plan=plan)
    doc = fitz.open(stream=pdf.pdf_bytes, filetype="pdf")
    try:
        return doc[0].get_text()
    finally:
        doc.close()


def test_score_field_and_section_case_by_band():
    early = _first_page_text(2)
    assert "Wynik" not in early
    assert "A. ROZGRZEWKA" in early
    upper = _first_page_text(8)
    assert "Wynik" in upper and "/ 4" in upper
    assert "Część A. Rozgrzewka" in upper
    # Zadania podane jako generator nie znikają z karty.
    assert "12 × 4" in upper


def test_ui_template_selector_defaults_to_automatic():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file("app/ui/app.py", default_timeout=30).run()
    selectbox = next(sb for sb in at.selectbox if sb.label == "Szablon wizualny")
    assert selectbox.value == ""
    assert selectbox.options[0] == "Automatycznie (wg klasy i profilu)"
