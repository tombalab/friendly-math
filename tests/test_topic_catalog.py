"""Testy katalogu tematów (P0.1)."""
from app.domain.topic_catalog import (
    resolve_topic,
    topic_available_for_grade,
    topic_labels_for_grade,
    visual_family_for_topic,
)


def test_resolve_dodawanie_do_20_by_label():
    r = resolve_topic("dodawanie do 20", grade=2)
    assert r.topic_id == "dodawanie_do_20"
    assert r.blueprint_key == "dodawanie do 20"
    assert r.blueprint_status == "exact"
    assert r.capabilities.visual_family == "dodawanie"


def test_scoped_topic_maps_visual_family():
    """„dodawanie do 100” musi mapować na rodzinę dodawanie, nie być nieznane."""
    assert visual_family_for_topic("dodawanie do 100") == "dodawanie"
    assert visual_family_for_topic("tabliczka mnożenia") == "mnożenie"


def test_rowania_skip_images():
    r = resolve_topic("równania", grade=5)
    assert r.capabilities.skip_images is True
    assert visual_family_for_topic("równania") is None


def test_grade_filters_topics():
    labels_g2 = topic_labels_for_grade(2)
    assert "dodawanie do 20" in labels_g2
    assert "dodawanie" not in labels_g2  # tylko klasa 4+

    labels_g5 = topic_labels_for_grade(5)
    assert "dodawanie" in labels_g5
    assert "dodawanie do 20" not in labels_g5


def test_liczenie_po_has_full_answer_support():
    r = resolve_topic("liczenie po", grade=1)
    assert r.capabilities.answer_support == "full"
    assert not any("Klucz odpowiedzi" in w for w in r.warnings)


def test_blueprint_for_legacy_dodawanie_grade_8():
    r = resolve_topic("dodawanie", grade=8)
    assert r.has_blueprint
    assert r.blueprint_status in ("exact", "downgraded")


def test_unknown_topic():
    r = resolve_topic("nieistniejący temat", grade=2)
    assert r.blueprint_status == "unknown"
    assert r.topic_id == "unknown"
