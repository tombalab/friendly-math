"""Złote karty (Q6): wzorce docelowe i automatyczna część checklisty jakości.

Złota karta to plik z `data/reference_worksheets/` z polem `golden`. Generujemy ją
offline (zadania z wzorca zamiast OpenAI) i sprawdzamy to, co da się zmierzyć:
liczbę stron ucznia, brak etykiety diagnozy, obecność zadań, szablon i pomoce.
Resztę checklisty (`docs/quality-checklist.md`) ocenia człowiek na wydruku.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import patch

from app.domain.profile_catalog import get_profile
from app.domain.worksheet_contract import WorksheetRequest, WorksheetResult

REF_DIR = Path(__file__).resolve().parents[2] / "data" / "reference_worksheets"

ANSWER_PAGE_MARK = "Karta odpowiedzi"

# Słowa, które nie mogą trafić na kartę ucznia: diagnoza i teksty dla nauczyciela.
_FORBIDDEN_ON_STUDENT_PAGE = (
    "ADHD",
    "dyskalkul",
    "dysleks",
    "grafomotor",
    "PPP",
    "orzeczeni",
    "Profil",
    "Strategia",
    "Rola grafiki",
    "Jak pracujemy",
)


@dataclass(frozen=True)
class GoldenCard:
    name: str
    data: dict[str, Any]

    @property
    def meta(self) -> dict[str, Any]:
        return self.data["metadata"]

    @property
    def golden(self) -> dict[str, Any]:
        return self.data["golden"]

    @property
    def tasks(self) -> list[str]:
        return list(self.data["tasks"])


@dataclass(frozen=True)
class GoldenReport:
    card: GoldenCard
    result: WorksheetResult
    page_texts: tuple[str, ...]
    issues: tuple[str, ...]

    @property
    def student_pages(self) -> tuple[str, ...]:
        return tuple(t for t in self.page_texts if ANSWER_PAGE_MARK not in t)


def list_golden_cards(ref_dir: Path = REF_DIR) -> list[GoldenCard]:
    cards = []
    for path in sorted(ref_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if "golden" in data:
            cards.append(GoldenCard(path.stem, data))
    return cards


def generate_golden(card: GoldenCard, *, output_dir: Path, history_dir: Path) -> WorksheetResult:
    """Pełny pipeline `WorksheetService` z zadaniami wzorca zamiast wywołania OpenAI."""
    from app.worksheet.service import WorksheetService

    service = WorksheetService(output_dir=output_dir, history_dir=history_dir)
    with patch("app.worksheet.service.generate_tasks", return_value={"tasks": card.tasks}):
        return service.generate(
            WorksheetRequest(
                grade=int(card.meta["grade"]),
                topic_label=card.meta["topic"],
                profile_id=card.meta["profile"],
                number_of_tasks=len(card.tasks),
                include_illustration=True,
                include_workspace=True,
                include_answers=True,
            )
        )


def pdf_page_texts(pdf_bytes: bytes) -> tuple[str, ...]:
    import fitz

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        return tuple(page.get_text() for page in doc)
    finally:
        doc.close()


def check_golden(card: GoldenCard, result: WorksheetResult, page_texts: tuple[str, ...]) -> list[str]:
    """Automatyczna część checklisty. Pusta lista = karta spełnia wzorzec."""
    if not result.pdf_bytes:
        return ["brak PDF"]
    issues: list[str] = []
    expected = card.golden
    student = [t for t in page_texts if ANSWER_PAGE_MARK not in t]
    answers = [t for t in page_texts if ANSWER_PAGE_MARK in t]

    if result.tasks != card.tasks:
        issues.append("zadania na karcie różnią się od wzorca (fallback albo walidacja podmieniła treść)")
    if len(student) > expected["max_student_pages"]:
        issues.append(f"strony ucznia: {len(student)} > {expected['max_student_pages']}")
    if not answers or "dla nauczyciela" not in "\n".join(answers):
        issues.append("brak karty odpowiedzi oznaczonej „dla nauczyciela”")

    student_text = "\n".join(student)
    profile = get_profile(card.meta["profile"])
    forbidden = list(_FORBIDDEN_ON_STUDENT_PAGE)
    if profile.id != "standardowy":
        forbidden.append(profile.label_for_ui)
    for word in forbidden:
        if word.lower() in student_text.lower():
            issues.append(f"etykieta „{word}” na karcie ucznia")
    if "Imię i nazwisko" not in (student[0] if student else ""):
        issues.append("brak pola „Imię i nazwisko” na pierwszej stronie")

    for i in range(1, len(card.tasks) + 1):
        if not re.search(rf"(?m)^{i}\.", student_text):
            issues.append(f"brak zadania {i} na karcie ucznia")
    for page_no, text in enumerate(student, start=1):
        if not re.search(r"(?m)^\d+\.", text):
            issues.append(f"strona {page_no} ucznia bez żadnego zadania (np. sama samoocena)")

    plan = result.worksheet_plan
    if plan is not None and plan.template.template_id != expected["template"]:
        issues.append(f"szablon {plan.template.template_id} zamiast {expected['template']}")
    if "visual_kinds" in expected:
        kinds = [v.kind if v else None for v in (result.task_visuals or [])]
        if kinds != list(expected["visual_kinds"]):
            issues.append(f"pomoce wizualne {kinds} zamiast {expected['visual_kinds']}")
    return issues


def run_golden(card: GoldenCard, *, output_dir: Path, history_dir: Path) -> GoldenReport:
    result = generate_golden(card, output_dir=output_dir, history_dir=history_dir)
    texts = pdf_page_texts(result.pdf_bytes) if result.pdf_bytes else ()
    return GoldenReport(card, result, texts, tuple(check_golden(card, result, texts)))
