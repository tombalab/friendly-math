"""Reference matching for teacher review (Phase 3)."""
from __future__ import annotations

from pathlib import Path

from app.review.reference_loader import find_best_reference, list_reference_cards

ROOT = Path(__file__).resolve().parents[1]


def test_list_reference_cards_loads_repo_files():
    cards = list_reference_cards(ROOT)
    assert len(cards) >= 22
    assert all(c.quality_criteria for c in cards)


def test_find_dyskalkulia_dodawanie():
    ref = find_best_reference(
        grade=2,
        topic_label="dodawanie do 20",
        profile_id="dyskalkulia",
        project_root=ROOT,
    )
    assert ref is not None
    assert "dyskalkulia" in ref.path.name


def test_find_liczenie_po_standardowy():
    ref = find_best_reference(
        grade=1,
        topic_label="liczenie po",
        profile_id="standardowy",
        project_root=ROOT,
    )
    assert ref is not None
    assert "liczenie_po" in ref.path.name
    assert "standardowy" in ref.path.name
