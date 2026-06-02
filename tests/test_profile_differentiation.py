"""Regression: profiles must produce measurably different worksheets."""
from __future__ import annotations

from app.ai.fallback_tasks import fallback_tasks_for_topic
from app.domain.profile_pedagogy import get_pedagogy_spec
from app.domain.worksheet_layout import resolve_worksheet_layout
from app.domain.profile_catalog import resolve_profile
from app.generators.images import _skip_reason_for_task, generate_worksheet_images_for_tasks_with_diagnostics
from app.validators.profile_enforcement import count_enriched_tasks


PROFILES = (
    "standardowy",
    "ADHD",
    "dyskalkulia",
    "dysleksja",
    "trudności w nauce",
    "zdolny",
)


def _fallback_lists(topic: str, grade: int, n: int = 5) -> dict[str, list[str]]:
    return {
        pid: list(fallback_tasks_for_topic(topic, grade, n, profile_id=pid) or [])
        for pid in PROFILES
    }


def test_dodawanie_do_20_fallbacks_differ_between_profiles():
    banks = _fallback_lists("dodawanie_do_20", grade=1)
    std = banks["standardowy"]
    assert banks["ADHD"] != std
    assert banks["dyskalkulia"] != std
    assert banks["zdolny"] != std
    assert banks["ADHD"] != banks["dyskalkulia"]
    assert frozenset(banks["ADHD"]) != frozenset(banks["dyskalkulia"])


def test_tabliczka_mnozenia_fallbacks_differ():
    banks = _fallback_lists("tabliczka_mnozenia", grade=2)
    assert banks["ADHD"] != banks["standardowy"]
    assert banks["zdolny"] != banks["standardowy"]


def test_adhd_fallback_has_small_operands():
    tasks = fallback_tasks_for_topic("dodawanie_do_20", 1, 5, profile_id="ADHD") or []
    assert tasks
    for t in tasks:
        assert "Policz:" in t
        assert "Ania" not in t and "Tomek" not in t


def test_zdolny_has_enriched_tasks():
    tasks = fallback_tasks_for_topic("dodawanie_do_20", 1, 5, profile_id="zdolny") or []
    assert count_enriched_tasks(tasks) >= 1


def test_dysleksia_fallback_not_artificially_lowered():
    dys = fallback_tasks_for_topic("dodawanie_do_20", 1, 5, profile_id="dysleksja") or []
    assert any("9" in t or "7" in t for t in dys)


def test_layout_differs_for_support_profiles():
    layouts = {}
    for pid in ("ADHD", "dyskalkulia", "trudności w nauce"):
        rp = resolve_profile(pid)
        layouts[pid] = resolve_worksheet_layout(rp, grade=2, number_of_tasks=5)
    assert layouts["ADHD"].task_spacing != layouts["dyskalkulia"].task_spacing
    assert layouts["dyskalkulia"].workspace_lines >= layouts["ADHD"].workspace_lines


def test_pedagogy_specs_unique_groups():
    groups = {get_pedagogy_spec(p).profile_group for p in PROFILES}
    assert "adhd" in groups
    assert "dyskalkulia" in groups
    assert "zdolny" in groups


def test_ulamki_grade4_fallbacks_differ():
    banks = _fallback_lists("ulamki", grade=4)
    assert banks["standardowy"] != banks["ADHD"]
    assert banks["dyskalkulia"] != banks["zdolny"]
    assert all("/8" not in t for t in banks["dyskalkulia"] if "Policz:" in t)


def test_pieniadze_fallbacks_differ():
    banks = _fallback_lists("pieniadze", grade=2)
    assert banks["ADHD"] != banks["standardowy"]
    assert banks["zdolny"] != banks["standardowy"]


def test_czas_adhd_short_tasks():
    tasks = fallback_tasks_for_topic("czas", 1, 4, profile_id="ADHD") or []
    assert tasks
    assert all(len(t) <= 90 for t in tasks)


def test_zadania_tekstowe_dysleksia_shorter_than_standard():
    std = fallback_tasks_for_topic("zadania_tekstowe", 2, 3, profile_id="standardowy") or []
    dys = fallback_tasks_for_topic("zadania_tekstowe", 2, 3, profile_id="dysleksja") or []
    assert std and dys
    assert sum(len(t) for t in dys) < sum(len(t) for t in std)


def test_money_image_renders_for_small_amounts():
    result = generate_worksheet_images_for_tasks_with_diagnostics(
        ["Ile razem? 3 zł + 2 zł = ____ zł"],
        topic="pieniądze",
        profile="dyskalkulia",
        grade=2,
    )
    assert result.rendered_count == 1


def test_clock_image_renders_for_adhd_czas():
    result = generate_worksheet_images_for_tasks_with_diagnostics(
        ["Która godzina, gdy mała wskazówka pokazuje 3, a duża 12? ____"],
        topic="czas",
        profile="ADHD",
        grade=1,
    )
    assert result.rendered_count == 1


def test_image_diagnostics_reports_skip_reason():
    task = "Policz: 99 + 88 = ____"
    reason = _skip_reason_for_task(task, "dodawanie do 20", "ADHD")
    assert reason is not None
    result = generate_worksheet_images_for_tasks_with_diagnostics(
        [task, "Policz: 3 + 4 = ____"],
        topic="dodawanie do 20",
        profile="ADHD",
        grade=1,
    )
    assert result.rendered_count == 1
    assert result.slots[0].skip_reason
    assert result.slots[1].rendered
