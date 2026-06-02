"""Local worksheet history store (P2.5)."""
from __future__ import annotations

import json
from pathlib import Path

from app.domain.worksheet_contract import (
    ImageCoverageSummary,
    WorksheetRequest,
    WorksheetResult,
    WorksheetWarning,
)
from app.history.store import WorksheetHistoryStore
from app.observability.events import GenerationTrace


def _minimal_result(tmp_path: Path, request_id: str = "test-req-001") -> WorksheetResult:
    from app.domain.profile_catalog import resolve_profile
    from app.domain.topic_catalog import resolve_topic

    req = WorksheetRequest(
        grade=2,
        topic_label="dodawanie do 20",
        profile_id="standardowy",
        number_of_tasks=2,
        worksheet_label="grupa A",
    )
    topic = resolve_topic(req.topic_label, req.grade)
    profile = resolve_profile(req.profile_id)
    return WorksheetResult(
        request=req,
        success=True,
        blocked=False,
        tasks=["Policz: 1 + 1 = ____", "Policz: 2 + 2 = ____"],
        resolved_topic=topic,
        resolved_profile=profile,
        image_coverage=ImageCoverageSummary(
            mode="disabled",
            requested=False,
            rendered_count=0,
            total_slots=2,
            detail_pl="wyłączone",
        ),
        pdf_bytes=b"%PDF-1.4 minimal",
        warnings=[WorksheetWarning("task_quality_test", "test", "warning")],
        request_id=request_id,
    )


def test_save_creates_unique_directory_and_files(tmp_path):
    store = WorksheetHistoryStore(tmp_path)
    r1 = _minimal_result(tmp_path, "aaaa-1111")
    r2 = _minimal_result(tmp_path, "bbbb-2222")
    r2.pdf_bytes = b"%PDF-2"

    p1 = store.save(r1, GenerationTrace.start(log_to_stdout=False))
    p2 = store.save(r2, GenerationTrace.start(log_to_stdout=False))

    assert p1 != p2
    assert (p1 / "worksheet.pdf").read_bytes() == r1.pdf_bytes
    assert (p2 / "worksheet.pdf").read_bytes() == r2.pdf_bytes

    meta1 = json.loads((p1 / "meta.json").read_text(encoding="utf-8"))
    assert meta1["grade"] == 2
    assert meta1["worksheet_label"] == "grupa A"
    assert "task_quality_test" in meta1["warning_codes"]
    assert "Policz" not in json.dumps(meta1)


def test_list_recent_newest_first(tmp_path, monkeypatch):
    times = iter(
        [
            "2026-01-01T10:00:00+00:00",
            "2026-01-02T10:00:00+00:00",
        ]
    )
    monkeypatch.setattr("app.history.store.utc_now_iso", lambda: next(times))

    store = WorksheetHistoryStore(tmp_path)
    store.save(_minimal_result(tmp_path, "older-id"))
    store.save(_minimal_result(tmp_path, "newer-id"))

    entries = store.list_recent(limit=10)
    assert len(entries) == 2
    assert entries[0].request_id == "newer-id"


def test_load_pdf_roundtrip(tmp_path):
    store = WorksheetHistoryStore(tmp_path)
    rid = "roundtrip-1"
    result = _minimal_result(tmp_path, rid)
    store.save(result)

    loaded = store.load_pdf_bytes(rid)
    assert loaded == result.pdf_bytes
    meta = store.load_meta(rid)
    assert meta is not None
    assert meta.topic_label == "dodawanie do 20"
