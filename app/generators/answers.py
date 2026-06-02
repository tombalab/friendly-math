"""
Generowanie klucza odpowiedzi (P0.3).

Rozpoznaje m.in.: działania `a op b`, porównywanie, równania z okienkiem,
liczenie po, ułamki o tym samym mianowniku, intuicyjne połowa/ćwierć.

Zwraca status per zadanie: supported | unsupported | ambiguous | error.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Optional

from app.domain.topic_catalog import AnswerSupport, resolve_topic

AnswerStatus = Literal["supported", "unsupported", "ambiguous", "error"]

_BOX_CHARS = ("☐", "[]", "[ ]", "□", "▢", "▭")

_REASON_UNSUPPORTED = "format poza automatycznym kluczem"
_REASON_AMBIGUOUS = "niejednoznaczne — wymaga interpretacji nauczyciela"
_REASON_ERROR = "nie udało się obliczyć wyniku"
_REASON_TOPIC_NONE = "temat bez automatycznego klucza odpowiedzi"


@dataclass(frozen=True)
class TaskAnswer:
    status: AnswerStatus
    value: str = ""
    reason: str | None = None

    def display_text(self) -> str:
        if self.status == "supported":
            return self.value
        label = {
            "unsupported": "sprawdź ręcznie",
            "ambiguous": "niejednoznaczne",
            "error": "błąd obliczeń",
        }.get(self.status, "brak odpowiedzi")
        return f"— ({label})"


@dataclass(frozen=True)
class AnswerKeyResult:
    items: tuple[TaskAnswer, ...]
    topic_answer_support: AnswerSupport | None = None

    @property
    def supported_count(self) -> int:
        return sum(1 for i in self.items if i.status == "supported")

    @property
    def manual_review_count(self) -> int:
        return len(self.items) - self.supported_count

    def summary_pl(self) -> str:
        n = len(self.items)
        if n == 0:
            return "Brak zadań w kluczu odpowiedzi."
        s = self.supported_count
        if self.manual_review_count == 0:
            return f"Klucz automatyczny: {s}/{n} odpowiedzi."
        return (
            f"Klucz automatyczny: {s}/{n} odpowiedzi; "
            f"{self.manual_review_count} wymaga ręcznej weryfikacji."
        )

    def display_values(self) -> list[str]:
        return [item.display_text() for item in self.items]

    def tasks_needing_review(self) -> list[int]:
        """Numery zadań (1-based) bez automatycznej odpowiedzi."""
        return [
            i + 1
            for i, item in enumerate(self.items)
            if item.status != "supported"
        ]


def compute_answer_key(
    tasks: list[str],
    *,
    topic_id: str | None = None,
    topic_label: str | None = None,
    grade: int | None = None,
) -> AnswerKeyResult:
    """
    Klucz odpowiedzi ze statusem per zadanie.
    `topic_id` lub `topic_label` + `grade` — poziom wsparcia z katalogu tematów.
    """
    topic_support: AnswerSupport | None = None
    if topic_id is not None or topic_label is not None:
        key = topic_id if topic_id is not None else topic_label
        assert key is not None
        topic_support = resolve_topic(key, grade or 2).capabilities.answer_support

    items = tuple(
        _answer_for_task_structured(t, topic_support=topic_support) for t in tasks
    )
    return AnswerKeyResult(items=items, topic_answer_support=topic_support)


def compute_answers(tasks: list[str]) -> list[str]:
    """Skrót: same teksty do PDF (kompatybilność wsteczna)."""
    return compute_answer_key(tasks).display_values()


# --------------------------------------------------------------------
# Główny dispatcher
# --------------------------------------------------------------------


def _answer_for_task_structured(
    task: str,
    *,
    topic_support: AnswerSupport | None,
) -> TaskAnswer:
    if topic_support == "none":
        return TaskAnswer(status="unsupported", reason=_REASON_TOPIC_NONE)

    raw = task.strip()
    low = raw.lower()

    if _looks_like_word_problem(low):
        return TaskAnswer(status="unsupported", reason=_REASON_UNSUPPORTED)

    # Porównywanie — tylko gdy wzorzec pasuje
    if "wstaw znak" in low or re.search(r"\d+\s*__+\s*\d+", raw):
        ans = _answer_compare(raw)
        if ans is not None:
            return TaskAnswer(status="supported", value=ans)

    if "uzupełnij" in low and "," in raw and "okienko" not in low:
        ans = _answer_sequence(raw)
        if ans is not None:
            return TaskAnswer(status="supported", value=ans)

    if any(b in raw for b in _BOX_CHARS) or "okienko" in low:
        ans = _answer_box_equation(raw)
        if ans is not None:
            return TaskAnswer(status="supported", value=ans)

    ans = _answer_intuitive_fraction(raw)
    if ans is not None:
        return TaskAnswer(status="supported", value=ans)

    frac = _answer_same_denom_fraction(raw)
    if frac == "__AMBIGUOUS__":
        return TaskAnswer(status="ambiguous", reason=_REASON_AMBIGUOUS)
    if frac is not None:
        return TaskAnswer(status="supported", value=frac)

    ans = _answer_arithmetic(raw)
    if ans is not None:
        return TaskAnswer(status="supported", value=ans)

    return TaskAnswer(status="unsupported", reason=_REASON_UNSUPPORTED)


def _looks_like_word_problem(low: str) -> bool:
    """Heurystyka: zadania tekstowe bez prostego wzorca liczbowego."""
    if "policz:" in low and re.search(r"(-?\d+)\s*([+*×·\-−/:÷])\s*(-?\d+)", low):
        return False
    markers = ("ania", "tomek", "koszyk", "jabł", "zostało", "kupiła", "miał", "miała")
    if any(m in low for m in markers):
        return True
    if low.count(" ") > 12 and "?" in low:
        return True
    return False


# --------------------------------------------------------------------
# Parsery / kalkulatory poszczególnych typów
# --------------------------------------------------------------------


def _answer_compare(task: str) -> str | None:
    m = re.search(r"(-?\d+)\s*_+\s*(-?\d+)", task)
    if not m:
        return None
    a, b = int(m.group(1)), int(m.group(2))
    if a < b:
        return "<"
    if a > b:
        return ">"
    return "="


def _answer_sequence(task: str) -> str | None:
    nums = re.findall(r"-?\d+", task)
    blanks = task.count("__")
    if len(nums) < 3 or blanks < 1:
        return None
    seq = [int(n) for n in nums]
    diffs = [seq[i + 1] - seq[i] for i in range(len(seq) - 1)]
    if not all(d == diffs[0] for d in diffs):
        return None
    step = diffs[0]
    nexts = []
    last = seq[-1]
    for _ in range(blanks):
        last += step
        nexts.append(str(last))
    return ", ".join(nexts)


def _answer_box_equation(task: str) -> str | None:
    for ch in _BOX_CHARS:
        if ch == "☐":
            continue
        task = task.replace(ch, "☐")

    m = re.search(r"(-?\d+)\s*([+\-−×·*:÷/])\s*☐\s*=\s*(-?\d+)", task)
    if m:
        a = int(m.group(1))
        op = m.group(2)
        c = int(m.group(3))
        return _solve_box(a, op, c, box_position="right")

    m = re.search(r"☐\s*([+\-−×·*:÷/])\s*(-?\d+)\s*=\s*(-?\d+)", task)
    if m:
        op = m.group(1)
        b = int(m.group(2))
        c = int(m.group(3))
        return _solve_box(b, op, c, box_position="left")

    return None


def _solve_box(known: int, op: str, c: int, box_position: str) -> str | None:
    op_n = _normalize_op(op)
    if op_n == "+":
        return str(c - known)
    if op_n == "-":
        return str(known - c) if box_position == "right" else str(c + known)
    if op_n == "*":
        if known == 0 or c % known != 0:
            return None
        return str(c // known)
    if op_n == "/":
        if box_position == "right":
            if c == 0 or known % c != 0:
                return None
            return str(known // c)
        return str(c * known)
    return None


def _answer_intuitive_fraction(task: str) -> str | None:
    low = task.lower()
    if "połowa" in low or "połowę" in low:
        m = re.search(r"z\s+(-?\d+)", low)
        if m:
            n = int(m.group(1))
            if n % 2 == 0:
                return str(n // 2)
            return f"{n/2:g}"
    if "ćwier" in low or "ćwierć" in low or "ćwierci" in low:
        m = re.search(r"z\s+(-?\d+)", low)
        if m:
            n = int(m.group(1))
            if n % 4 == 0:
                return str(n // 4)
            return f"{n/4:g}"
    return None


def _answer_same_denom_fraction(task: str) -> str | None:
    fractions = re.findall(r"(\d+)\s*/\s*(\d+)", task)
    if len(fractions) < 2:
        return None
    op_match = re.search(r"\d+\s*/\s*\d+\s*([+\-−])\s*\d+\s*/\s*\d+", task)
    if not op_match:
        return None
    op = _normalize_op(op_match.group(1))
    a_num, a_den = int(fractions[0][0]), int(fractions[0][1])
    b_num, b_den = int(fractions[1][0]), int(fractions[1][1])
    if a_den != b_den:
        return None
    if op == "+":
        res = a_num + b_num
    elif op == "-":
        res = a_num - b_num
    else:
        return None
    if res < 0:
        return "__AMBIGUOUS__"
    if res == a_den:
        return "1"
    return f"{res}/{a_den}"


def _answer_arithmetic(task: str) -> str | None:
    m = re.search(r"(-?\d+)\s*([+*×·\-−/:÷])\s*(-?\d+)", task)
    if not m:
        return None
    a, b = int(m.group(1)), int(m.group(3))
    op = _normalize_op(m.group(2))
    if op == "+":
        return str(a + b)
    if op == "-":
        return str(a - b)
    if op == "*":
        return str(a * b)
    if op == "/":
        if b == 0 or a % b != 0:
            return None
        return str(a // b)
    return None


def _normalize_op(op: str) -> str:
    if op in ("+",):
        return "+"
    if op in ("-", "−"):
        return "-"
    if op in ("*", "×", "·"):
        return "*"
    if op in ("/", ":", "÷"):
        return "/"
    return op
