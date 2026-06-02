"""Tests for worksheet contracts and service (P1.3–P1.4)."""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from app.domain.worksheet_contract import WorksheetRequest
from app.worksheet.service import WorksheetService, generate_worksheet

ROOT = Path(__file__).resolve().parents[1]


def test_unknown_topic_blocked_without_api_key():
    old = os.environ.pop("OPENAI_API_KEY", None)
    try:
        req = WorksheetRequest(
            grade=2,
            topic_label="nieistniejący temat xyz",
            profile_id="standardowy",
            number_of_tasks=3,
        )
        result = generate_worksheet(req)
        assert result.blocked is True
        assert result.tasks == []
        assert any(w.code == "topic_unknown" for w in result.warnings)
    finally:
        if old is not None:
            os.environ["OPENAI_API_KEY"] = old


def test_grade_limit_blocked():
    req = WorksheetRequest(
        grade=2,
        topic_label="dodawanie do 20",
        profile_id="standardowy",
        number_of_tasks=20,
    )
    result = generate_worksheet(req)
    assert result.blocked is True
    assert any(w.code == "validation" for w in result.warnings)


def test_missing_api_key_blocked():
    old = os.environ.pop("OPENAI_API_KEY", None)
    try:
        req = WorksheetRequest(
            grade=2,
            topic_label="dodawanie do 20",
            profile_id="standardowy",
            number_of_tasks=3,
        )
        result = generate_worksheet(req)
        assert result.blocked is True
        assert any(w.code == "api_key_missing" for w in result.warnings)
    finally:
        if old is not None:
            os.environ["OPENAI_API_KEY"] = old


def test_quality_summary_has_expected_keys():
    req = WorksheetRequest(
        grade=2,
        topic_label="nieznany",
        profile_id="standardowy",
        number_of_tasks=3,
    )
    result = generate_worksheet(req)
    keys = set(result.quality_summary_pl().keys())
    assert keys == {
        "Temat",
        "Profil",
        "Źródło zadań",
        "Klucz odpowiedzi",
        "Ilustracje",
        "Układ PDF",
        "PDF",
    }


@patch("app.worksheet.service.generate_tasks")
def test_service_success_path_mocked(mock_tasks):
    mock_tasks.return_value = {
        "tasks": ["Policz: 2 + 3 = ____", "Policz: 4 + 1 = ____"],
        "profile": "standardowy",
        "grade": "2",
        "topic": "dodawanie do 20",
        "topic_id": "dodawanie_do_20",
    }
    os.environ["OPENAI_API_KEY"] = "test-key"
    req = WorksheetRequest(
        grade=2,
        topic_label="dodawanie do 20",
        profile_id="standardowy",
        number_of_tasks=2,
        include_answers=True,
    )
    svc = WorksheetService(output_dir=ROOT / "data" / "out")
    result = svc.generate(req)
    assert result.success is True
    assert result.blocked is False
    assert len(result.tasks) == 2
    assert result.pdf_bytes is not None
    assert len(result.pdf_bytes) > 500
    assert result.answer_key is not None
    assert result.can_download_pdf is True
