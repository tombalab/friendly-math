"""Replace tasks that violate profile policy with profile-aware fallbacks."""
from __future__ import annotations

import re

from app.ai.fallback_tasks import fallback_tasks_for_topic
from app.domain.profile_pedagogy import get_pedagogy_spec
from app.validators.task_validator import TaskValidationIssue, validate_tasks_for_profile

_ENRICHED_MARKERS = re.compile(
    r"(wynik\s+(pomnóż|dodaj|odejmij)|wyjaśnij\s+sposób|,\s*wynik\s+)",
    re.IGNORECASE,
)


def count_enriched_tasks(tasks: list[str]) -> int:
    """Zadania wieloetapowe lub z prośbą o uzasadnienie (profil zdolny)."""
    return sum(1 for t in tasks if _ENRICHED_MARKERS.search(t))


def enforce_tasks_for_profile(
    tasks: list[str],
    *,
    profile_id: str,
    grade: int,
    topic_id: str,
) -> tuple[list[str], int, list[str]]:
    """
    Dla profili z `enforce_with_fallback` zamienia zadania z naruszeniami
    na pozycje z banku fallback profilowego.

    Zwraca: (zadania, liczba_zamian, komunikaty).
    """
    spec = get_pedagogy_spec(profile_id)
    if spec.validation_mode != "enforce_with_fallback":
        return list(tasks), 0, []

    validation = validate_tasks_for_profile(
        tasks,
        profile_id=profile_id,
        grade=grade,
        topic_id=topic_id,
    )
    if not validation.issues:
        return list(tasks), 0, []

    bad_indices = sorted({i.task_index for i in validation.issues if i.task_index >= 0})
    if not bad_indices:
        return list(tasks), 0, []

    pool = fallback_tasks_for_topic(
        topic_id,
        grade,
        max(len(tasks) * 2, len(bad_indices) + 3),
        profile_id=profile_id,
    )
    if not pool:
        return list(tasks), 0, [
            "Profil wymaga dopasowania zadań, ale brak banku fallback dla tematu."
        ]

    out = list(tasks)
    pool_idx = 0
    replaced = 0
    used = set(out)

    for idx in bad_indices:
        candidate = None
        attempts = 0
        while attempts < len(pool):
            cand = pool[pool_idx % len(pool)]
            pool_idx += 1
            attempts += 1
            if cand not in used:
                candidate = cand
                break
        if candidate is None:
            continue
        out[idx] = candidate
        used.add(candidate)
        replaced += 1

    messages: list[str] = []
    if replaced:
        messages.append(
            f"Dopasowano {replaced} zad(ań) do profilu „{spec.display_name}” "
            f"(zastąpiono po walidacji)."
        )
    return out, replaced, messages


def critical_issue_indices(issues: list[TaskValidationIssue]) -> set[int]:
    return {i.task_index for i in issues if i.task_index >= 0 and i.severity == "error"}
