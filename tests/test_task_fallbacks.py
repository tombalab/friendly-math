"""Tests for honest topic-preserving task fallbacks (P0.2)."""
from __future__ import annotations

from app.ai.fallback_tasks import fallback_tasks_for_topic
from app.ai import text_generator


class _BrokenClient:
    class chat:
        class completions:
            @staticmethod
            def create(**kwargs):
                raise RuntimeError("api down")


class _ShortClient:
    class chat:
        class completions:
            @staticmethod
            def create(**kwargs):
                class _Message:
                    content = "Policz: 3 + 4 = ____"

                class _Choice:
                    message = _Message()

                class _Response:
                    choices = [_Choice()]

                return _Response()


def _with_client(client, fn):
    original = text_generator._get_client
    text_generator._get_client = lambda: client
    try:
        return fn()
    finally:
        text_generator._get_client = original


def _codes(result: dict) -> set[str]:
    return {
        w.get("code", "")
        for w in result.get("_warnings", [])
        if isinstance(w, dict)
    }


def test_profile_fallbacks_differ_for_dodawanie_do_20():
    std = fallback_tasks_for_topic("dodawanie_do_20", grade=1, n=5, profile_id="standardowy")
    adhd = fallback_tasks_for_topic("dodawanie_do_20", grade=1, n=5, profile_id="ADHD")
    assert std is not None and adhd is not None
    assert std != adhd


def test_direct_ulamki_fallback_preserves_topic():
    tasks = fallback_tasks_for_topic("ulamki", grade=3, n=3)
    assert tasks is not None
    assert len(tasks) == 3
    assert any("połowa" in t or "ćwierć" in t for t in tasks)
    assert all("3 + 4" not in t for t in tasks)


def test_api_failure_uses_topic_preserving_fallback():
    result = _with_client(
        _BrokenClient(),
        lambda: text_generator.generate_tasks(
            profile="standardowy",
            grade=3,
            topic="ułamki",
            n=3,
        ),
    )
    assert result["_used_fallback"] is True
    assert result.get("_blocked") is not True
    assert "api_fallback_used" in _codes(result)
    assert all("3 + 4" not in t for t in result["tasks"])
    assert any("połowa" in t or "ćwierć" in t for t in result["tasks"])


def test_short_model_response_is_padded_with_same_topic():
    result = _with_client(
        _ShortClient(),
        lambda: text_generator.generate_tasks(
            profile="standardowy",
            grade=1,
            topic="dodawanie do 20",
            n=3,
        ),
    )
    assert len(result["tasks"]) == 3
    assert "fallback_padded_tasks" in _codes(result)
    assert all("+" in t for t in result["tasks"])


def test_unknown_topic_blocks_instead_of_generic_tasks():
    result = text_generator.generate_tasks(
        profile="standardowy",
        grade=2,
        topic="nieistniejący temat",
        n=3,
    )
    assert result["_blocked"] is True
    assert result["tasks"] == []
    assert "fallback_blocked" in _codes(result)


def test_warning_messages_accept_structured_warnings():
    result = {
        "_warnings": [
            {"code": "x", "message": "Pierwsze ostrzeżenie", "severity": "warning"},
            "Drugie ostrzeżenie",
        ]
    }
    assert text_generator.warning_messages(result) == [
        "Pierwsze ostrzeżenie",
        "Drugie ostrzeżenie",
    ]
