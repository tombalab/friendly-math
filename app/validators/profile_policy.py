"""Profile-aware validation thresholds seeded from reference worksheets (P2.1)."""
from __future__ import annotations

from app.domain.structured_criteria import StructuredQualityCriteria

# Wspólne frazy zadań tekstowych (mniej dekodowania przy profilach wspierających).
_WORD_PROBLEM_PHRASES: tuple[str, ...] = (
    "Ania",
    "Marek",
    "Tomek",
    "kupił",
    "kupiła",
    "miał",
    "miała",
    "zostało",
    "zjadła",
    "zjadł",
    "ciasta",
    "w sklepie",
    "ile jabłek",
)


def policy_for_profile(
    profile_id: str,
    *,
    grade: int,
    topic_id: str | None = None,
) -> StructuredQualityCriteria:
    """
    Domyślne progi walidacji dla profilu (bez nadpisywania zadań).
    Karty referencyjne mogą doprecyzować przez `structured_criteria` w JSON.
    """
    pid = (profile_id or "standardowy").lower()
    topic = (topic_id or "").lower()

    if "liczenie_po" in topic:
        return _counting_sequence_policy(pid, grade)

    if pid == "adhd":
        cap = 10 if grade <= 2 else 15 if grade <= 4 else 20
        return StructuredQualityCriteria(
            max_operand=cap,
            max_result=cap,
            allowed_operations=_ops_for_topic(topic, grade),
            max_operations_per_task=1,
            max_task_length=48 if grade <= 3 else 60,
            forbidden_phrases=_WORD_PROBLEM_PHRASES,
            require_format_prefix="Policz:",
            require_format_consistent=True,
            max_word_problem_sentences=1,
        )

    if pid == "dyskalkulia":
        cap = 12 if grade <= 2 else 20 if grade <= 4 else 30
        return StructuredQualityCriteria(
            max_operand=cap,
            max_result=cap * 2 if grade <= 3 else cap + 20,
            allowed_operations=_ops_for_topic(topic, grade),
            max_operations_per_task=1,
            max_task_length=55,
            forbidden_phrases=_WORD_PROBLEM_PHRASES,
            require_format_prefix="Policz:",
            require_format_consistent=True,
            max_word_problem_sentences=1,
        )

    if pid == "dysleksja":
        return StructuredQualityCriteria(
            max_operations_per_task=1 if "ułam" in topic else 2,
            max_task_length=52,
            forbidden_phrases=_WORD_PROBLEM_PHRASES,
            require_format_prefix="Policz:",
            require_format_consistent=True,
            allow_fractions="ułam" in topic,
            max_denominator=8 if "ułam" in topic else None,
            max_word_problem_sentences=1,
        )

    if pid == "zdolny":
        return StructuredQualityCriteria(
            max_operand=50 if grade >= 4 else 30,
            max_result=200,
            max_operations_per_task=3,
            max_task_length=90,
            max_word_problem_sentences=2,
        )

    if pid in ("trudności w nauce", "trudnosci w nauce"):
        return StructuredQualityCriteria(
            max_operand=15 if grade <= 3 else 25,
            max_result=30 if grade <= 3 else 50,
            max_operations_per_task=1,
            max_task_length=60,
            forbidden_phrases=_WORD_PROBLEM_PHRASES,
            require_format_prefix="Policz:",
            max_word_problem_sentences=1,
        )

    # standardowy — łagodne progi, głównie skrajne przypadki
    return StructuredQualityCriteria(
        max_operand=100 if grade >= 5 else 50,
        max_result=200 if grade >= 5 else 100,
        allowed_operations=_ops_for_topic(topic, grade) or (),
        max_operations_per_task=2 if grade >= 5 else 1,
        max_task_length=80 if grade >= 5 else 65,
    )


def _counting_sequence_policy(profile_id: str, grade: int) -> StructuredQualityCriteria:
    """Temat `liczenie po` pracuje na ciągach, nie na operacji `a op b`."""
    max_num = 20 if grade == 1 else 200 if grade == 2 else 1000
    max_len = 56 if profile_id in ("adhd", "dyskalkulia") else 70
    return StructuredQualityCriteria(
        max_operand=max_num,
        max_result=max_num,
        max_operations_per_task=0,
        max_task_length=max_len,
        forbidden_phrases=_WORD_PROBLEM_PHRASES,
        require_format_prefix="Uzupełnij:",
        require_format_consistent=True,
        max_word_problem_sentences=1,
    )


def _ops_for_topic(topic_id: str, grade: int) -> tuple[str, ...]:
    if "ułam" in topic_id or "ulam" in topic_id:
        return ("+", "−", "-")
    if "mnoż" in topic_id or "mnoz" in topic_id:
        return ("×", "*", "x", "X")
    if "dziel" in topic_id:
        return ("÷", "/", ":")
    if "odejm" in topic_id:
        return ("−", "-")
    if grade <= 3:
        return ("+", "−", "-")
    return ()
