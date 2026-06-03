"""
Generator zadań matematycznych.

v1.x: prompt budowany z `TOPIC_BLUEPRINTS` (zgodnie z podstawą programową
edukacji wczesnoszkolnej 1-3) + nakładki z profilu ucznia.

Dla profilu „standardowy" w klasach 1-3 dążymy do PEŁNEGO pokrycia tematyki PP.
Pozostałe profile dziedziczą blueprinty i nakładają na nie własne reguły
(`task_instruction`, `task_examples`).
"""
from __future__ import annotations

import os
import re

from dotenv import load_dotenv
from openai import OpenAI

from app.ai.fallback_tasks import fallback_tasks_for_topic
from app.ai.topic_blueprints import Blueprint, get_blueprint
from app.domain.profile_pedagogy import (
    build_profile_prompt_section,
    tighten_blueprint_max_result,
)
from app.domain.topic_catalog import resolve_topic
from app.generators.profiles.registry import get_profile

load_dotenv()

# v1.x: jeden model i niska temperature dla powtarzalności.
_MODEL = "gpt-4o-mini"
_TEMPERATURE = 0.3
_MAX_TOKENS = 2000
_TIMEOUT_S = 30.0

_client = None


def _warning(code: str, message: str, severity: str = "warning") -> dict[str, str]:
    return {"code": code, "message": message, "severity": severity}


def _add_warning(
    result: dict,
    code: str,
    message: str,
    severity: str = "warning",
) -> None:
    result.setdefault("_warnings", []).append(_warning(code, message, severity))


def warning_messages(result: dict) -> list[str]:
    """Return warning messages from legacy string warnings or structured warnings."""
    out: list[str] = []
    for w in result.get("_warnings", []):
        if isinstance(w, dict):
            out.append(str(w.get("message", "")))
        else:
            out.append(str(w))
    return [m for m in out if m]


def _get_client():
    """Lazy initialization OpenAI client."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY nie znaleziony w .env. "
                "Sprawdź czy masz plik .env z kluczem API."
            )
        _client = OpenAI(api_key=api_key)
    return _client


# --------------------------------------------------------------------
# Walidacja numeryczna
# --------------------------------------------------------------------

# Maksymalny wynik dopuszczalny per klasa (fallback, gdy blueprint nie podaje swojego).
_MAX_RESULT_BY_GRADE = {
    1: 20,
    2: 100,
    3: 1000,
    4: 10000,
    5: 100000,
    6: 1000000,
    7: 10000000,
    8: 100000000,
}


def _try_compute(task: str) -> int | None:
    """
    Próbuje policzyć prosty wzorzec `a op b` w treści zadania.
    Zwraca wynik jako int lub None, gdy zadania nie da się obliczyć
    (zadania tekstowe, równania z okienkiem, ułamki, porównania).
    """
    m = re.search(r"(\d+)\s*([+\-−*×·/:÷])\s*(\d+)", task)
    if not m:
        return None
    a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
    if op == "+":
        return a + b
    if op in ("-", "−"):
        return a - b
    if op in ("*", "×", "·"):
        return a * b
    if op in ("/", ":", "÷"):
        return a // b if b != 0 else None
    return None


def _is_task_in_range(task: str, grade_int: int, max_result: int) -> bool:
    """
    True, jeśli wynik mieści się w zakresie (klasa + ewentualny limit blueprintu).
    Dla zadań, których nie umiemy obliczyć – True (nie odrzucamy zadań tekstowych itp.).
    """
    result = _try_compute(task)
    if result is None:
        return True
    if grade_int <= 3 and result < 0:
        return False
    if grade_int <= 3:
        return 0 <= result <= max_result
    return result <= max_result


def _filter_tasks_by_grade(
    tasks: list[str],
    grade: str,
    blueprint: Blueprint | None,
    *,
    profile_id: str | None = None,
) -> tuple[list[str], int]:
    """
    Odrzuca zadania, których wynik wykracza poza zakres klasy/blueprintu.
    Zwraca (tasks_w_zakresie, ile_odrzucono).
    """
    try:
        grade_int = int(grade)
    except (TypeError, ValueError):
        return tasks, 0

    max_result = _MAX_RESULT_BY_GRADE.get(grade_int, 100000000)
    if blueprint and "max_result" in blueprint:
        bp_max = blueprint["max_result"]
        if profile_id:
            tightened = tighten_blueprint_max_result(
                bp_max, profile_id, grade=grade_int
            )
            if tightened is not None:
                bp_max = tightened
        max_result = min(max_result, bp_max)

    kept: list[str] = []
    dropped = 0
    for t in tasks:
        if _is_task_in_range(t, grade_int, max_result):
            kept.append(t)
        else:
            dropped += 1
    return kept, dropped


# --------------------------------------------------------------------
# Prompt
# --------------------------------------------------------------------


def _build_prompt(grade: str, topic: str, profile_id: str, n: int) -> str:
    """
    Składa prompt:
    1. Bazowa instrukcja generatora.
    2. Blueprint tematu+klasy (zakres liczb, format, przykłady).
    3. Profil ucznia (`task_instruction`).

    Jeśli brak blueprintu dla danej pary topic+grade – fallback na ogólną
    instrukcję z profilu (jak w poprzednich wersjach).
    """
    profile = get_profile(profile_id)

    try:
        grade_int = int(grade)
    except (TypeError, ValueError):
        grade_int = 2

    bp = get_blueprint(topic, grade_int)

    # Sekcja „topic & grade" – z blueprintu albo z profilu (fallback).
    if bp:
        topic_section = (
            f"Temat: {topic} (klasa {grade}).\n"
            f"Wymagania merytoryczne:\n- {bp.get('instruction', '').strip()}\n\n"
            f"Przykłady (wzoruj się na nich, ale generuj NOWE zadania):\n"
            f"{bp.get('examples', '').strip()}"
        )
    else:
        topic_section = (
            f"Temat: {topic} (klasa {grade}).\n"
            f"Wymagania merytoryczne:\n- {profile.task_instruction}\n\n"
            f"Przykłady:\n{profile.task_examples}"
        )

    profile_section = build_profile_prompt_section(profile_id)

    optional = ""
    # optional_context hook — rozszerzalne z WorksheetRequest w przyszłości

    return f"""Jesteś nauczycielem matematyki edukacji wczesnoszkolnej w polskiej szkole.
Wygeneruj DOKŁADNIE {n} zadań – po jednym w linii, BEZ numeracji, BEZ dodatkowych komentarzy.

{topic_section}{profile_section}{optional}

Reguły wspólne:
- Liczby wyłącznie z zakresu wskazanego w wymaganiach (NIE wychodź poza zakres klasy).
- Każde zadanie w JEDNEJ linii.
- Format zadań ma być spójny z przykładami powyżej.
- NIE numeruj zadań (numerację dodajemy później).
- NIE pisz wstępu, podsumowania ani uwag – tylko surowe zadania."""


def generate_tasks(profile, grade, topic, n=3):
    """
    Generuje zadania matematyczne.

    Zwraca dict: {tasks, profile, grade, topic, [_warning], [_warnings], [_error]}.
    Gdy nie da się zachować tematu w fallbacku: `_blocked=True`.
    """
    grade_str = str(grade)
    try:
        grade_int = int(grade)
    except (TypeError, ValueError):
        grade_int = 2

    resolved = resolve_topic(topic, grade_int)
    topic_key = resolved.blueprint_key
    bp = get_blueprint(topic_key, grade_int)

    if resolved.topic_id == "unknown":
        return _blocked_result(
            profile=profile,
            grade=grade,
            resolved=resolved,
            reason=(
                f"Nieznany temat „{topic}” — nie można bezpiecznie wygenerować "
                "zadań ani fallbacku zachowującego temat."
            ),
            error=None,
        )

    if not bp:
        fallback = fallback_tasks_for_topic(
            resolved.topic_id,
            grade_int,
            n,
            profile_id=str(profile),
        )
        if fallback is None:
            return _blocked_result(
                profile=profile,
                grade=grade,
                resolved=resolved,
                reason=(
                    f"Brak szablonu i bezpiecznego fallbacku dla tematu "
                    f"„{resolved.label_pl}” w klasie {grade}."
                ),
                error=None,
            )
        result = {
            "tasks": fallback,
            "profile": profile,
            "grade": grade,
            "topic": resolved.label_pl,
            "topic_id": resolved.topic_id,
            "_used_fallback": True,
        }
        for w in resolved.warnings:
            _add_warning(result, "topic_catalog", w)
        _add_warning(
            result,
            "blueprint_missing_fallback",
            (
                f"Brak szablonu dla pary „{resolved.label_pl}” / klasa {grade}. "
                "Użyto deterministycznych zadań zastępczych zachowujących temat."
            ),
        )
        result["_warning"] = " ".join(warning_messages(result))
        return result

    try:
        client = _get_client()
        prompt = _build_prompt(grade=grade_str, topic=topic_key, profile_id=str(profile), n=n)

        response = client.chat.completions.create(
            model=_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Jesteś nauczycielem edukacji wczesnoszkolnej w Polsce. "
                        "Generujesz zadania matematyczne ZGODNE z podstawą programową "
                        "dla wskazanej klasy. Trzymasz się formatu z przykładów."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=_TEMPERATURE,
            max_completion_tokens=_MAX_TOKENS,
            timeout=_TIMEOUT_S,
        )

        tasks_text = response.choices[0].message.content.strip()
        tasks = [line.strip() for line in tasks_text.split("\n") if line.strip()]
        # Często model mimo zakazu numeruje lub używa bulletów – czyścimy prefiksy.
        tasks = [re.sub(r"^\s*(?:\d+[.)]\s+|[-*•]\s+)", "", t) for t in tasks]

        # Walidacja: odrzucamy zadania wyraźnie poza zakresem klasy/blueprintu.
        tasks, dropped = _filter_tasks_by_grade(
            tasks, grade_str, bp, profile_id=str(profile)
        )
        kept_after_validation = len(tasks)
        padded_count = 0

        if len(tasks) < n:
            missing = n - len(tasks)
            fallback = fallback_tasks_for_topic(
                resolved.topic_id,
                grade_int,
                missing,
                profile_id=str(profile),
            )
            if fallback is None:
                return _blocked_result(
                    profile=profile,
                    grade=grade,
                    resolved=resolved,
                    reason=(
                        f"Nie udało się wygenerować {n} zadań i brak bezpiecznego "
                        f"fallbacku dla tematu „{resolved.label_pl}”."
                    ),
                    error=None,
                )
            tasks.extend(fallback)
            padded_count = len(tasks) - kept_after_validation

        result = {
            "tasks": tasks[:n],
            "profile": profile,
            "grade": grade,
            "topic": resolved.label_pl,
            "topic_id": resolved.topic_id,
        }
        for w in resolved.warnings:
            _add_warning(result, "topic_catalog", w)
        if dropped:
            msg = (
                f"Odrzucono {dropped} zadań – wynik wykraczał poza zakres klasy {grade} "
                f"lub tematu „{topic}”."
            )
            _add_warning(result, "tasks_dropped", msg)
        if len(tasks) > len(tasks[:n]):
            _add_warning(result, "tasks_trimmed", f"Model zwrócił więcej niż {n} zadań — nadmiar pominięto.")
        if len(tasks[:n]) < n:
            _add_warning(result, "tasks_missing", f"Wygenerowano tylko {len(tasks[:n])}/{n} zadań.")
        if padded_count:
            _add_warning(
                result,
                "fallback_padded_tasks",
                f"Dopełniono {padded_count} zadań deterministycznym fallbackiem dla tematu „{resolved.label_pl}”.",
            )
        messages = warning_messages(result)
        if len(messages) == 1:
            result["_warning"] = messages[0]
        elif messages:
            result["_warning"] = " ".join(messages)
        return result

    except Exception as e:
        fallback = fallback_tasks_for_topic(
            resolved.topic_id,
            grade_int,
            n,
            profile_id=str(profile),
        )
        if fallback is None:
            return _blocked_result(
                profile=profile,
                grade=grade,
                resolved=resolved,
                reason=(
                    f"Generowanie zadań przez API nie powiodło się i brak bezpiecznego "
                    f"fallbacku dla tematu „{resolved.label_pl}”."
                ),
                error=str(e),
            )
        result = {
            "tasks": fallback,
            "profile": profile,
            "grade": grade,
            "topic": resolved.label_pl,
            "topic_id": resolved.topic_id,
            "_error": str(e),
            "_used_fallback": True,
        }
        _add_warning(
            result,
            "api_fallback_used",
            (
                "Generowanie zadań przez API nie powiodło się. "
                f"Użyto deterministycznych zadań zastępczych dla tematu „{resolved.label_pl}”."
            ),
        )
        result["_warning"] = warning_messages(result)[0]
        return result


def _blocked_result(
    *,
    profile,
    grade,
    resolved,
    reason: str,
    error: str | None,
) -> dict:
    result = {
        "tasks": [],
        "profile": profile,
        "grade": grade,
        "topic": resolved.label_pl,
        "topic_id": resolved.topic_id,
        "_blocked": True,
        "_error": error,
    }
    _add_warning(result, "fallback_blocked", reason, severity="error")
    result["_warning"] = reason
    return result
