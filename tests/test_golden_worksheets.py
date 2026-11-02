"""Q6: złote karty — wzorce docelowe sprawdzane offline na pełnym pipeline."""
from __future__ import annotations

import pytest

from app.domain.educational_strategy import grade_band
from app.review.golden import list_golden_cards, run_golden

pytest.importorskip("fitz")

CARDS = list_golden_cards()


def test_golden_set_covers_grade_bands_and_profiles():
    assert 5 <= len(CARDS) <= 6
    assert {grade_band(int(c.meta["grade"])) for c in CARDS} == {"early", "middle", "upper"}
    profiles = {c.meta["profile"] for c in CARDS}
    assert {"ADHD", "dyskalkulia", "standardowy"} <= profiles
    for card in CARDS:
        assert card.golden["max_student_pages"] in (1, 2), card.name
        assert card.golden["why"].strip(), card.name


@pytest.mark.parametrize("card", CARDS, ids=[c.name for c in CARDS])
def test_golden_worksheet_meets_checklist(card, tmp_path):
    report = run_golden(card, output_dir=tmp_path / "out", history_dir=tmp_path / "history")
    assert report.issues == (), "\n".join(report.issues)
