"""Machine-readable quality criteria for reference worksheets (P2.2)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class StructuredQualityCriteria:
    """
    Opcjonalne kryteria wykonywalne — uzupełniają `quality_criteria` (tekst dla nauczyciela).
    """

    max_operand: int | None = None
    max_result: int | None = None
    allowed_operations: tuple[str, ...] = ()
    forbidden_phrases: tuple[str, ...] = ()
    max_task_length: int | None = None
    max_operations_per_task: int | None = None
    require_format_prefix: str | None = None
    require_format_consistent: bool = False
    allow_fractions: bool = False
    max_denominator: int | None = None
    max_word_problem_sentences: int | None = None

    @classmethod
    def from_mapping(cls, raw: dict[str, Any] | None) -> StructuredQualityCriteria | None:
        if raw is None:
            return None
        if not isinstance(raw, dict):
            raise TypeError("structured_criteria musi być obiektem JSON")

        allowed_ops = raw.get("allowed_operations")
        if allowed_ops is None:
            ops: tuple[str, ...] = ()
        elif isinstance(allowed_ops, list):
            ops = tuple(str(o) for o in allowed_ops)
        else:
            raise TypeError("allowed_operations musi być listą")

        forbidden = raw.get("forbidden_phrases")
        if forbidden is None:
            phrases: tuple[str, ...] = ()
        elif isinstance(forbidden, list):
            phrases = tuple(str(p) for p in forbidden)
        else:
            raise TypeError("forbidden_phrases musi być listą")

        return cls(
            max_operand=_optional_int(raw, "max_operand"),
            max_result=_optional_int(raw, "max_result"),
            allowed_operations=ops,
            forbidden_phrases=phrases,
            max_task_length=_optional_int(raw, "max_task_length"),
            max_operations_per_task=_optional_int(raw, "max_operations_per_task"),
            require_format_prefix=_optional_str(raw, "require_format_prefix"),
            require_format_consistent=bool(raw.get("require_format_consistent", False)),
            allow_fractions=bool(raw.get("allow_fractions", False)),
            max_denominator=_optional_int(raw, "max_denominator"),
            max_word_problem_sentences=_optional_int(raw, "max_word_problem_sentences"),
        )


def _optional_int(raw: dict[str, Any], key: str) -> int | None:
    val = raw.get(key)
    if val is None:
        return None
    if isinstance(val, bool) or not isinstance(val, int):
        raise TypeError(f"{key} musi być liczbą całkowitą lub null")
    return val


def _optional_str(raw: dict[str, Any], key: str) -> str | None:
    val = raw.get(key)
    if val is None:
        return None
    if not isinstance(val, str):
        raise TypeError(f"{key} musi być stringiem lub null")
    s = val.strip()
    return s or None
