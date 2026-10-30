"""Testy katalogu profili PPP (P0.5)."""
from app.domain.profile_catalog import (
    default_profile_id,
    profile_ids_for_ui,
    registry_ui_consistency_check,
    resolve_profile,
    uses_per_task_illustrations,
)
from app.generators.profiles.registry import all_profiles, registered_profile_ids


def test_all_registered_profiles_in_ui_order():
    assert registry_ui_consistency_check() == []


def test_dysleksja_visible_in_ui():
    ids = profile_ids_for_ui()
    assert "dysleksja" in ids
    assert len(ids) == len(registered_profile_ids())


def test_resolve_profile_by_id():
    r = resolve_profile("dyskalkulia")
    assert r.profile_id == "dyskalkulia"
    assert r.ui_label == "Dyskalkulia"
    assert r.is_low_stimuli is True
    assert r.illustration_mode == "per_task"


def test_dysleksja_header_illustrations():
    r = resolve_profile("dysleksja")
    assert r.illustration_mode == "header"
    assert uses_per_task_illustrations("dysleksja") is False


def test_case_insensitive_resolve():
    r = resolve_profile("adhd")
    assert r.profile_id == "ADHD"


def test_unknown_profile_falls_back_to_standard():
    r = resolve_profile("nieznany_profil")
    assert r.profile_id == "standardowy"
    assert r.warnings


def test_default_profile():
    assert default_profile_id() == "standardowy"


def test_every_profile_has_ui_metadata():
    for p in all_profiles():
        assert p.ui_label
        assert p.ui_summary
        assert p.illustration_mode in ("header", "per_task")


def test_every_ui_profile_has_own_pedagogy_spec():
    from app.domain.profile_pedagogy import get_pedagogy_spec

    for pid in profile_ids_for_ui():
        spec = get_pedagogy_spec(pid)
        assert spec.profile_id == pid, f"{pid!r} spada do fallbacku pedagogiki"


def test_help_text_consistent_between_catalog_and_pedagogy():
    from app.domain.profile_catalog import profile_help_text
    from app.domain.profile_pedagogy import teacher_hint_for_profile

    for pid in profile_ids_for_ui():
        assert profile_help_text(pid) == teacher_hint_for_profile(pid), pid


def test_streamlit_profile_selectbox_matches_catalog():
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    from app.domain.profile_catalog import profile_help_text, profile_selectbox_labels

    app_path = Path(__file__).resolve().parents[1] / "app" / "ui" / "app.py"
    at = AppTest.from_file(str(app_path), default_timeout=60).run()
    assert not at.exception

    selectbox = next(sb for sb in at.selectbox if sb.label == "Profil ucznia")
    labels = profile_selectbox_labels()
    assert selectbox.options == [labels[pid] for pid in profile_ids_for_ui()]
    assert "Dysleksja" in selectbox.options
    assert selectbox.value == default_profile_id()

    selectbox.set_value("dysleksja").run()
    assert not at.exception
    assert profile_help_text("dysleksja") in [c.value for c in at.caption]
