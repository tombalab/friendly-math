"""Observability events (P2.4)."""
from __future__ import annotations

import json
from unittest.mock import patch

from app.domain.worksheet_contract import WorksheetRequest
from app.observability.events import (
    EVENT_DOWNLOAD,
    EVENT_GENERATION_COMPLETE,
    EVENT_MODEL_CALL,
    EVENT_REQUEST_START,
    GenerationTrace,
    redact_event_data,
)
from app.observability.task_generation import metadata_from_task_payload
from app.ui.events_panel import record_download_event
from app.worksheet.service import generate_worksheet


def test_redact_strips_sensitive_keys():
    data = redact_event_data(
        {
            "grade": 2,
            "optional_context": "tajna notatka o uczniu",
            "prompt": "pełny prompt",
            "tasks": ["Policz: 1+1"],
        }
    )
    assert data["grade"] == 2
    assert "optional_context" not in data
    assert "prompt" not in data
    assert "tasks" not in data


def test_metadata_from_payload_no_task_text():
    meta = metadata_from_task_payload(
        {
            "tasks": ["Policz: 9 + 1 = ____"],
            "_used_fallback": True,
            "_warnings": [{"code": "api_fallback_used", "message": "x", "severity": "warning"}],
        }
    )
    assert meta["used_fallback"] is True
    assert "Policz" not in json.dumps(meta)


def test_trace_emits_expected_event_types():
    trace = GenerationTrace.start(log_to_stdout=False)
    trace.emit(EVENT_REQUEST_START, grade=2)
    assert trace.events[0].event == EVENT_REQUEST_START
    assert trace.events[0].request_id == trace.request_id


@patch("app.worksheet.service.generate_tasks")
def test_generate_worksheet_attaches_trace(mock_tasks):
    mock_tasks.return_value = {
        "tasks": ["Policz: 2 + 3 = ____", "Policz: 4 + 1 = ____"],
        "profile": "standardowy",
        "grade": "2",
        "topic": "dodawanie",
        "topic_id": "dodawanie_do_20",
    }
    req = WorksheetRequest(
        grade=2,
        topic_label="dodawanie do 20",
        profile_id="standardowy",
        number_of_tasks=2,
        include_answers=True,
    )
    result = generate_worksheet(req, trace=GenerationTrace.start(log_to_stdout=False))
    assert result.request_id
    assert result.events
    names = [e.event for e in result.events]
    assert EVENT_REQUEST_START in names
    assert EVENT_MODEL_CALL in names
    assert EVENT_GENERATION_COMPLETE in names
    assert names.index(EVENT_REQUEST_START) < names.index(EVENT_GENERATION_COMPLETE)
    blob = json.dumps([e.to_dict() for e in result.events])
    assert "Policz" not in blob
    assert '"optional_context":' not in blob
    assert '"prompt":' not in blob


def test_record_download_appends_event():
    trace = GenerationTrace.start(log_to_stdout=False)
    from app.domain.worksheet_contract import WorksheetResult

    result = WorksheetResult(
        request=WorksheetRequest(
            grade=2,
            topic_label="dodawanie",
            profile_id="standardowy",
            number_of_tasks=1,
        ),
        success=True,
        blocked=False,
        pdf_bytes=b"%PDF",
        request_id=trace.request_id,
        events=trace.events,
    )
    n = len(result.events)
    record_download_event(result)
    assert len(result.events) == n + 1
    assert result.events[-1].event == EVENT_DOWNLOAD
