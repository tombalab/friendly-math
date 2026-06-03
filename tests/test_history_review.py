"""History review persistence (Phase 3)."""
from __future__ import annotations

import tempfile
from pathlib import Path

from app.history.store import WorksheetHistoryStore
from tests.test_history_store import _minimal_result


def test_save_and_load_review(tmp_path):
    store = WorksheetHistoryStore(tmp_path)
    result = _minimal_result(tmp_path, "review-req-1")
    store.save(result)
    store.save_review("review-req-1", rating=4, notes="format OK", reference_file="x.json")
    loaded = store.load_review("review-req-1")
    assert loaded is not None
    assert loaded["rating"] == 4
    assert loaded["notes"] == "format OK"
    assert store.has_review("review-req-1")
