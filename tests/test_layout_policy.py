"""Tests for P1.1 visual policy and P1.5 layout resolver."""
from __future__ import annotations

from app.domain.profile_catalog import resolve_profile
from app.domain.visual_policy import (
    is_low_stimuli_profile,
    policy_for_resolved,
    uses_per_task_illustrations_from_catalog,
)
from app.pdf.generator import build_worksheet_pdf_bytes, WorksheetMeta
from app.domain.worksheet_layout import (
    LOW_STIMULI_PDF_BOOST,
    resolve_worksheet_layout,
)


def test_low_stimuli_profiles_from_catalog_not_hardcoded_sets():
    assert is_low_stimuli_profile("dyskalkulia") is True
    assert is_low_stimuli_profile("ADHD") is True
    assert is_low_stimuli_profile("trudności w nauce") is True
    assert is_low_stimuli_profile("standardowy") is False
    assert is_low_stimuli_profile("dysleksja") is False


def test_illustration_mode_per_profile():
    assert uses_per_task_illustrations_from_catalog("dyskalkulia") is True
    assert uses_per_task_illustrations_from_catalog("ADHD") is True
    assert uses_per_task_illustrations_from_catalog("trudności w nauce") is True
    assert uses_per_task_illustrations_from_catalog("standardowy") is False
    assert uses_per_task_illustrations_from_catalog("dysleksja") is False


def test_low_stimuli_layout_larger_than_standard():
    std = resolve_worksheet_layout(
        resolve_profile("standardowy"), grade=2, number_of_tasks=5
    )
    dys = resolve_worksheet_layout(
        resolve_profile("dyskalkulia"), grade=2, number_of_tasks=5
    )
    assert dys.task_font_size >= std.task_font_size
    assert dys.margin >= std.margin
    assert dys.is_low_stimuli is True
    assert dys.source == "low_stimuli_boost"


def test_grade_1_3_minimum_task_font():
    layout = resolve_worksheet_layout(
        resolve_profile("standardowy"), grade=1, number_of_tasks=5
    )
    assert layout.task_font_size >= 12
    assert layout.margin >= 55


def test_zdolny_compact_task_font():
    std = resolve_worksheet_layout(
        resolve_profile("standardowy"), grade=5, number_of_tasks=5
    )
    zdolny = resolve_worksheet_layout(
        resolve_profile("zdolny"), grade=5, number_of_tasks=5
    )
    assert zdolny.task_font_size <= std.task_font_size


def test_pdf_does_not_reapply_profile_overlay():
    """Ten sam layout dict — zmiana profilu w meta nie zmienia rozmiaru czcionki w PDF."""
    layout = resolve_worksheet_layout(
        resolve_profile("dyskalkulia"), grade=2, number_of_tasks=2
    )
    meta_std = WorksheetMeta(
        title="Test",
        grade="2",
        topic_range="dodawanie",
        student_profile="standardowy",
        student_profile_id="standardowy",
    )
    meta_dys = WorksheetMeta(
        title="Test",
        grade="2",
        topic_range="dodawanie",
        student_profile="Dyskalkulia",
        student_profile_id="dyskalkulia",
    )
    tasks = ["Policz: 2 + 3 = ____"]
    pdf_a = build_worksheet_pdf_bytes(meta=meta_std, tasks=tasks, layout=layout)
    pdf_b = build_worksheet_pdf_bytes(meta=meta_dys, tasks=tasks, layout=layout)
    assert len(pdf_a.pdf_bytes) > 200
    assert abs(len(pdf_a.pdf_bytes) - len(pdf_b.pdf_bytes)) < 50


def test_policy_snapshot():
    p = policy_for_resolved(resolve_profile("ADHD"))
    assert p["illustration_mode"] == "per_task"
    assert p["is_low_stimuli"] is True


def test_workspace_disabled():
    layout = resolve_worksheet_layout(
        resolve_profile("standardowy"),
        grade=2,
        number_of_tasks=3,
        include_workspace=False,
    )
    assert layout.workspace_lines == 0


def test_low_stimuli_boost_keys_present():
    layout = resolve_worksheet_layout(
        resolve_profile("ADHD"), grade=3, number_of_tasks=4
    )
    assert layout.background_color == LOW_STIMULI_PDF_BOOST["background_color"]
