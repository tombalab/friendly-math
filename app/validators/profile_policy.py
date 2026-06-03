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
        max_operand, max_result = _numeric_caps_for_topic(topic, grade, pid)
        prefix = _format_prefix_for_topic(topic, grade)
        forbidden = _forbidden_phrases_for_topic(topic)
        max_sentences = _max_word_problem_sentences_for_topic(topic, grade)
        max_len = _max_task_length_for_topic(topic, grade, pid, default=48 if grade <= 3 else 60)
        return StructuredQualityCriteria(
            max_operand=max_operand,
            max_result=max_result,
            allowed_operations=_ops_for_topic(topic, grade),
            max_operations_per_task=1,
            max_task_length=max_len,
            forbidden_phrases=forbidden,
            require_format_prefix=prefix,
            require_format_consistent=prefix is not None,
            max_word_problem_sentences=max_sentences,
        )

    if pid == "dyskalkulia":
        max_operand, max_result = _numeric_caps_for_topic(topic, grade, pid)
        prefix = _format_prefix_for_topic(topic, grade)
        forbidden = _forbidden_phrases_for_topic(topic)
        max_sentences = _max_word_problem_sentences_for_topic(topic, grade)
        max_len = _max_task_length_for_topic(topic, grade, pid, default=55)
        has_fractions = "ulam" in topic or "ułam" in topic
        return StructuredQualityCriteria(
            max_operand=max_operand,
            max_result=max_result,
            allowed_operations=_ops_for_topic(topic, grade),
            max_operations_per_task=1,
            max_task_length=max_len,
            forbidden_phrases=forbidden,
            require_format_prefix=prefix,
            require_format_consistent=prefix is not None,
            allow_fractions=has_fractions,
            max_denominator=6 if has_fractions else None,
            max_word_problem_sentences=max_sentences,
        )

    if pid == "dysleksja":
        prefix = _format_prefix_for_topic(topic, grade)
        forbidden = _forbidden_phrases_for_topic(topic)
        max_sentences = _max_word_problem_sentences_for_topic(topic, grade)
        max_len = _max_task_length_for_topic(topic, grade, pid, default=52)
        return StructuredQualityCriteria(
            max_operations_per_task=1 if "ułam" in topic else 2,
            max_task_length=max_len,
            forbidden_phrases=forbidden,
            require_format_prefix=prefix,
            require_format_consistent=prefix is not None,
            allow_fractions="ułam" in topic,
            max_denominator=8 if "ułam" in topic else None,
            max_word_problem_sentences=max_sentences,
        )

    if pid == "zdolny":
        max_operand, max_result = _numeric_caps_for_topic(topic, grade, pid)
        max_len = _max_task_length_for_topic(topic, grade, pid, default=90)
        max_sentences = _max_word_problem_sentences_for_topic(topic, grade)
        return StructuredQualityCriteria(
            max_operand=max_operand,
            max_result=max_result,
            max_operations_per_task=3,
            max_task_length=max_len,
            max_word_problem_sentences=max_sentences,
        )

    if pid in ("trudności w nauce", "trudnosci w nauce"):
        max_operand, max_result = _numeric_caps_for_topic(topic, grade, pid)
        prefix = _format_prefix_for_topic(topic, grade)
        forbidden = _forbidden_phrases_for_topic(topic)
        max_sentences = _max_word_problem_sentences_for_topic(topic, grade)
        max_len = _max_task_length_for_topic(topic, grade, pid, default=60)
        return StructuredQualityCriteria(
            max_operand=max_operand,
            max_result=max_result,
            max_operations_per_task=1,
            max_task_length=max_len,
            forbidden_phrases=forbidden,
            require_format_prefix=prefix,
            require_format_consistent=prefix is not None,
            max_word_problem_sentences=max_sentences,
        )

    # standardowy — łagodne progi, głównie skrajne przypadki
    max_operand, max_result = _numeric_caps_for_topic(topic, grade, pid)
    max_len = _max_task_length_for_topic(topic, grade, pid, default=80 if grade >= 5 else 65)
    max_sentences = _max_word_problem_sentences_for_topic(topic, grade)
    has_fractions = "ulam" in topic or "ułam" in topic
    return StructuredQualityCriteria(
        max_operand=max_operand,
        max_result=max_result,
        allowed_operations=_ops_for_topic(topic, grade) or (),
        max_operations_per_task=2 if grade >= 5 else 1,
        max_task_length=max_len,
        max_word_problem_sentences=max_sentences,
        allow_fractions=has_fractions,
        max_denominator=8 if has_fractions and grade <= 6 else None,
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


def _numeric_caps_for_topic(topic_id: str, grade: int, profile_id: str) -> tuple[int, int]:
    """Zakresy walidacji zależne od tematu; profile PPP nadal mają ciaśniejsze limity."""
    low_support = profile_id in ("adhd", "dyskalkulia", "trudności w nauce", "trudnosci w nauce")
    topic = topic_id.casefold()

    if grade <= 3:
        if "porown" in topic or "porówn" in topic:
            max_num = 20 if grade == 1 else 100 if grade == 2 else 1000
            return (max_num, max_num)
        if "do_1000" in topic:
            return (1000, 1000)
        if "do_100" in topic:
            return (100, 100)
        if "rownania_z_okienkiem" in topic:
            return (20 if grade == 1 else 100, 20 if grade == 1 else 100)
        if "tabliczka" in topic:
            return (10, 100)
        if "mnozenie_przez_10" in topic:
            return (20, 200)
        if "dzielenie" in topic:
            return (100, 100)
        if "do_20" in topic:
            return (20, 20)
        if topic in ("czas", "pomiary_dlugosci", "pieniadze", "obwody", "zadania_tekstowe"):
            max_num = 30 if grade == 1 else 100 if grade == 2 else 1000
            return (max_num, max_num)
        if "ulam" in topic or "ułam" in topic:
            return (50, 50)
        base = 10 if profile_id == "adhd" and grade <= 2 else 12 if profile_id == "dyskalkulia" and grade <= 2 else 20
        return (base, 20 if grade <= 2 else 40)

    if "mnoz" in topic or "mnoż" in topic:
        return (60, 500) if low_support else (100, 1000)
    if "dziel" in topic:
        return (5000, 1000) if low_support else (5000, 10000)
    if "rown" in topic or "rów" in topic:
        return (150, 150) if low_support else (500, 500)
    if "dodaw" in topic or "odejm" in topic:
        return (500, 1000) if low_support else (5000, 10000)
    if "ulam" in topic or "ułam" in topic:
        return (20, 20)
    if "procent" in topic:
        return (1000, 10000)
    if "poteg" in topic or "potęg" in topic:
        return (100, 10000)
    if "pitagoras" in topic or "pitagor" in topic:
        return (30, 30)

    return (30, 60) if low_support else (100, 200)


def _format_prefix_for_topic(topic_id: str, grade: int) -> str | None:
    """Wymagany prefiks tylko tam, gdzie temat ma jednoznaczny format."""
    topic = topic_id.casefold()
    if "liczenie_po" in topic:
        return "Uzupełnij:"
    if "porown" in topic or "porówn" in topic:
        return "Wstaw znak"
    if "rownania_z_okienkiem" in topic:
        return "Uzupełnij okienko:"
    if "rown" in topic or "rów" in topic:
        return "Rozwiąż:"
    if "ulam" in topic or "ułam" in topic:
        return "Policz:" if grade >= 4 else None
    if topic in (
        "pieniadze",
        "czas",
        "pomiary_dlugosci",
        "obwody",
        "zadania_tekstowe",
        "procenty",
        "pitagoras",
    ):
        return None
    return "Policz:"


def _forbidden_phrases_for_topic(topic_id: str) -> tuple[str, ...]:
    if topic_id.casefold() == "zadania_tekstowe":
        return ()
    return _WORD_PROBLEM_PHRASES


def _max_word_problem_sentences_for_topic(topic_id: str, grade: int) -> int | None:
    if topic_id.casefold() in (
        "zadania_tekstowe",
        "procenty",
        "pitagoras",
        "potegi",
    ):
        return None
    if topic_id.casefold() in ("czas", "pomiary_dlugosci", "pieniadze", "obwody"):
        return 2
    return 1


def _max_task_length_for_topic(
    topic_id: str,
    grade: int,
    profile_id: str,
    *,
    default: int,
) -> int:
    topic = topic_id.casefold()
    if topic == "zadania_tekstowe":
        return 140 if profile_id == "adhd" else 160
    if topic in ("procenty", "pitagoras"):
        return 120 if profile_id == "adhd" else 140
    if topic == "potegi":
        return 55 if profile_id == "adhd" else 65
    if topic in ("czas", "pomiary_dlugosci", "pieniadze", "obwody"):
        return 85 if profile_id == "adhd" else 95
    if "ulam" in topic or "ułam" in topic:
        return max(default, 65 if grade <= 3 else 55)
    return default


def _ops_for_topic(topic_id: str, grade: int) -> tuple[str, ...]:
    if "ułam" in topic_id or "ulam" in topic_id:
        if grade >= 7:
            return ("+", "−", "-", "×", "*")
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
