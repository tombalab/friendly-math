"""Testy klucza odpowiedzi (P0.3)."""
from __future__ import annotations

from app.generators.answers import (
    AnswerKeyResult,
    compute_answer_key,
    compute_answers,
)


def test_topic_none_skips_automatic_answers():
    key = compute_answer_key(
        ["Policz: 2 + 3 = ____"],
        topic_label="nieznany temat testowy",
        grade=2,
    )
    assert key.items[0].status == "unsupported"
    assert key.items[0].reason is not None
    assert "temat bez" in key.items[0].reason.lower()


def test_exam_topic_answers():
    key = compute_answer_key(
        ["Policz: 10% z 200 = ____", "Policz: 2³ = ____"],
        topic_id="procenty",
        grade=7,
    )
    assert key.items[0].value == "20"

    key2 = compute_answer_key(["Policz: 2³ = ____"], topic_id="potegi", grade=7)
    assert key2.items[0].value == "8"

    key3 = compute_answer_key(
        ["Przyprostokątne 3 cm i 4 cm. Przeciwprostokątna c = ____ cm"],
        topic_id="pitagoras",
        grade=7,
    )
    assert key3.items[0].value == "5"


def test_practical_topic_answers():
    key = compute_answer_key(
        ["Ile to razem? 5 zł + 2 zł = ____ zł", "Zamień: 3 zł = ____ gr"],
        topic_id="pieniadze",
        grade=2,
    )
    assert key.supported_count == 2
    assert key.items[0].value == "7"
    assert key.items[1].value == "300"

    key2 = compute_answer_key(
        ["Zamień: 2 m = ____ cm"],
        topic_id="pomiary_dlugosci",
        grade=2,
    )
    assert key2.items[0].value == "200"

    key3 = compute_answer_key(
        ["Ania miała 5 jabłek. Kupiła 4 jabłka. Ile ma jabłek? Odpowiedź: ____"],
        topic_id="zadania_tekstowe",
        grade=2,
    )
    assert key3.items[0].value == "9"


def test_display_text_explains_unsupported():
    key = compute_answer_key(["Ania miała 5 jabłek. Ile zostało? ____"], topic_id="dodawanie_do_20", grade=1)
    text = key.items[0].display_text()
    assert text.startswith("— (")
    assert "ręcznie" in text or "niejednoznaczne" in text


def test_compute_answers_backward_compat_strings():
    tasks = ["Policz: 3 + 4 = ____"]
    assert compute_answers(tasks) == ["7"]


def test_summary_pl_counts():
    from app.generators.answers import TaskAnswer

    key = AnswerKeyResult(
        items=(
            TaskAnswer(status="supported", value="1"),
            TaskAnswer(status="unsupported"),
        )
    )
    assert "1/2" in key.summary_pl()
    assert "ręcznej" in key.summary_pl()


def test_rownania_box_equations_supported():
    tasks = [
        "Rozwiąż: ☐ + 18 = 45",
        "Rozwiąż: 6 × ☐ = 54",
        "Rozwiąż: 72 : ☐ = 8",
    ]
    key = compute_answer_key(tasks, topic_label="równania", grade=5)
    assert key.supported_count == len(tasks)
    assert [i.value for i in key.items] == ["27", "9", "9"]


def test_liczenie_po_sequence_supported():
    key = compute_answer_key(
        ["Uzupełnij: 2, 4, 6, __, __"],
        topic_label="liczenie po",
        grade=1,
    )
    assert key.supported_count == 1
    assert key.items[0].value == "8, 10"
