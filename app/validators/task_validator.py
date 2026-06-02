"""Validate generated tasks against structured criteria (P2.1 / P2.2)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from app.domain.structured_criteria import StructuredQualityCriteria
from app.validators.profile_policy import policy_for_profile

_OP_CHARS = set("+−-×÷*/xX")
_FRACTION_RE = re.compile(r"\b(\d+)\s*/\s*(\d+)\b")
_INTEGER_RE = re.compile(r"\b(\d+)\b")
_ARITH_CHUNK_RE = re.compile(
    r"(\d+)\s*([+\u2212\-×÷*/xX])\s*(\d+)",
    re.UNICODE,
)

Severity = Literal["warning", "error"]


@dataclass(frozen=True)
class TaskValidationIssue:
    task_index: int
    code: str
    message: str
    severity: Severity = "warning"


@dataclass
class TaskValidationResult:
    issues: list[TaskValidationIssue]

    @property
    def ok(self) -> bool:
        return not self.issues

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    def summary_pl(self) -> str:
        if self.ok:
            return "OK — zadania spełniają progi profilu"
        n = len(self.issues)
        return f"{n} uwag(i) jakości zadań"


def merge_criteria(
    profile_policy: StructuredQualityCriteria,
    reference: StructuredQualityCriteria | None,
) -> StructuredQualityCriteria:
    """Łączy politykę profilu z doprecyzowaniem z karty referencyjnej (reference wygrywa)."""
    if reference is None:
        return profile_policy
    ref = reference
    prof = profile_policy

    def pick(ref_val, prof_val):
        return ref_val if ref_val is not None else prof_val

    forbidden = ref.forbidden_phrases or prof.forbidden_phrases
    allowed_ops = ref.allowed_operations or prof.allowed_operations

    return StructuredQualityCriteria(
        max_operand=pick(ref.max_operand, prof.max_operand),
        max_result=pick(ref.max_result, prof.max_result),
        allowed_operations=allowed_ops,
        forbidden_phrases=forbidden,
        max_task_length=pick(ref.max_task_length, prof.max_task_length),
        max_operations_per_task=pick(ref.max_operations_per_task, prof.max_operations_per_task),
        require_format_prefix=pick(ref.require_format_prefix, prof.require_format_prefix),
        require_format_consistent=ref.require_format_consistent or prof.require_format_consistent,
        allow_fractions=ref.allow_fractions or prof.allow_fractions,
        max_denominator=pick(ref.max_denominator, prof.max_denominator),
        max_word_problem_sentences=pick(
            ref.max_word_problem_sentences, prof.max_word_problem_sentences
        ),
    )


def validate_tasks(
    tasks: list[str],
    criteria: StructuredQualityCriteria,
) -> TaskValidationResult:
    """
    Sprawdza mierzalne właściwości zadań. Zwraca ostrzeżenia — bez cichej zamiany treści.
    """
    issues: list[TaskValidationIssue] = []
    prefixes: list[str] = []

    for idx, raw in enumerate(tasks):
        task = raw.strip()
        if not task:
            issues.append(
                TaskValidationIssue(idx, "empty_task", "Puste zadanie.", "warning")
            )
            continue

        if criteria.max_task_length is not None and len(task) > criteria.max_task_length:
            issues.append(
                TaskValidationIssue(
                    idx,
                    "task_too_long",
                    f"Zadanie ma {len(task)} znaków (max {criteria.max_task_length}).",
                )
            )

        if ":" in task:
            instr_prefix = task.split(":", 1)[0] + ":"
            if criteria.require_format_consistent:
                prefixes.append(instr_prefix)

        if criteria.require_format_prefix:
            if not task.startswith(criteria.require_format_prefix):
                issues.append(
                    TaskValidationIssue(
                        idx,
                        "format_prefix",
                        f"Oczekiwano prefiksu „{criteria.require_format_prefix}”.",
                    )
                )

        lowered = task.casefold()
        for phrase in criteria.forbidden_phrases:
            if phrase.casefold() in lowered:
                issues.append(
                    TaskValidationIssue(
                        idx,
                        "forbidden_phrase",
                        f"Niedozwolona fraza „{phrase}” (zadanie tekstowe / narracja).",
                    )
                )

        if criteria.max_word_problem_sentences is not None:
            sentence_text = re.sub(r"_+", "", task).strip()
            sentences = [s for s in re.split(r"[.!?]+", sentence_text) if s.strip()]
            if len(sentences) > criteria.max_word_problem_sentences:
                issues.append(
                    TaskValidationIssue(
                        idx,
                        "word_problem_load",
                        f"Zbyt długie polecenie ({len(sentences)} zdań, "
                        f"max {criteria.max_word_problem_sentences}).",
                    )
                )

        if criteria.allow_fractions and _FRACTION_RE.search(task):
            _check_fractions(idx, task, criteria, issues)
        else:
            _check_arithmetic(idx, task, criteria, issues)

    if criteria.require_format_consistent and prefixes:
        unique = sorted(set(prefixes))
        if len(unique) > 1:
            issues.append(
                TaskValidationIssue(
                    -1,
                    "format_inconsistent",
                    f"Niespójne prefiksy poleceń: {', '.join(unique)}.",
                )
            )

    return TaskValidationResult(issues=issues)


def validate_tasks_for_profile(
    tasks: list[str],
    *,
    profile_id: str,
    grade: int,
    topic_id: str | None = None,
    reference_criteria: StructuredQualityCriteria | None = None,
) -> TaskValidationResult:
    policy = policy_for_profile(profile_id, grade=grade, topic_id=topic_id)
    criteria = merge_criteria(policy, reference_criteria)
    return validate_tasks(tasks, criteria)


def _check_fractions(
    idx: int,
    task: str,
    criteria: StructuredQualityCriteria,
    issues: list[TaskValidationIssue],
) -> None:
    ops = _count_operations(task)
    if criteria.max_operations_per_task is not None and ops > criteria.max_operations_per_task:
        issues.append(
            TaskValidationIssue(
                idx,
                "too_many_operations",
                f"Wykryto {ops} operacji (max {criteria.max_operations_per_task}).",
            )
        )
    if criteria.allowed_operations:
        found = _operations_in_task(task)
        bad = found - _normalize_ops(criteria.allowed_operations)
        if bad:
            issues.append(
                TaskValidationIssue(
                    idx,
                    "operation_not_allowed",
                    f"Niedozwolone operacje: {', '.join(sorted(bad))}.",
                )
            )

    for _num, den in _FRACTION_RE.findall(task):
        d = int(den)
        if criteria.max_denominator is not None and d > criteria.max_denominator:
            issues.append(
                TaskValidationIssue(
                    idx,
                    "denominator_too_large",
                    f"Mianownik {d} przekracza max {criteria.max_denominator}.",
                )
            )


def _check_arithmetic(
    idx: int,
    task: str,
    criteria: StructuredQualityCriteria,
    issues: list[TaskValidationIssue],
) -> None:
    ops = _count_operations(task)
    if criteria.max_operations_per_task is not None and ops > criteria.max_operations_per_task:
        issues.append(
            TaskValidationIssue(
                idx,
                "too_many_operations",
                f"Wykryto {ops} operacji (max {criteria.max_operations_per_task}).",
            )
        )

    if criteria.allowed_operations:
        found = _operations_in_task(task)
        bad = found - _normalize_ops(criteria.allowed_operations)
        if bad:
            issues.append(
                TaskValidationIssue(
                    idx,
                    "operation_not_allowed",
                    f"Niedozwolone operacje: {', '.join(sorted(bad))}.",
                )
            )

    operands: list[int] = []
    for a, _op, b in _ARITH_CHUNK_RE.findall(task):
        operands.extend((int(a), int(b)))
    if not operands:
        operands = [int(n) for n in _INTEGER_RE.findall(task)]

    for value in operands:
        if criteria.max_operand is not None and value > criteria.max_operand:
            issues.append(
                TaskValidationIssue(
                    idx,
                    "operand_too_large",
                    f"Liczba {value} przekracza max_operand={criteria.max_operand}.",
                )
            )

    if criteria.max_result is not None and operands and ops >= 1:
        result = _estimate_result(task, operands)
        if result is not None and result > criteria.max_result:
            issues.append(
                TaskValidationIssue(
                    idx,
                    "result_too_large",
                    f"Szacowany wynik {result} > max_result={criteria.max_result}.",
                )
            )


def _strip_fraction_literals(task: str) -> str:
    """Usuwa ułamki z tekstu, żeby `/` w 1/2 nie liczył się jako dzielenie."""
    return _FRACTION_RE.sub(" U ", task)


def _strip_list_prefix(task: str) -> str:
    """Pomija numerację/bullety modelu, żeby `- Policz...` nie liczyć jako odejmowania."""
    return re.sub(r"^\s*(?:[-*•]\s+|\d+[.)]\s+)", "", task)


def _count_operations(task: str) -> int:
    stripped = _strip_fraction_literals(_strip_list_prefix(task))
    return sum(1 for ch in stripped if ch in _OP_CHARS)


def _operations_in_task(task: str) -> set[str]:
    found: set[str] = set()
    for ch in _strip_fraction_literals(_strip_list_prefix(task)):
        if ch in _OP_CHARS:
            found.add(_normalize_op_char(ch))
    return found


def _normalize_ops(ops: tuple[str, ...]) -> set[str]:
    return {_normalize_op_char(o) for o in ops}


def _normalize_op_char(op: str) -> str:
    mapping = {
        "+": "+",
        "−": "-",
        "-": "-",
        "×": "*",
        "x": "*",
        "X": "*",
        "*": "*",
        "÷": "/",
        "/": "/",
        ":": "/",
    }
    return mapping.get(op, op)


def _estimate_result(task: str, operands: list[int]) -> int | None:
    m = _ARITH_CHUNK_RE.search(task)
    if not m:
        return None
    a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
    sym = _normalize_op_char(op)
    if sym == "+":
        return a + b
    if sym == "-":
        return a - b
    if sym == "*":
        return a * b
    if sym == "/" and b:
        return a // b
    return None
