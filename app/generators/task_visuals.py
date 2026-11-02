"""
Pomoce wizualne do zadań jako opis danych (Q5).

Zamiast bitmapy budujemy `TaskVisual` — co narysować i z jakimi liczbami.
Rysuje go wektorowo `app/pdf/visuals.py` bezpośrednio w PDF (ostro przy druku,
jeden rodzaj obiektów w działaniu, prawdziwe pomoce dydaktyczne).

Zasada z `images.py` zostaje: lepiej brak pomocy niż pomoc, która kłamie.
O tym, czy zadanie da się uczciwie pokazać, decydują te same limity profilu.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from app.domain.topic_catalog import resolve_topic, visual_family_for_topic
from app.generators.images import (
    _is_task_safely_illustratable,
    _parse_all_fractions_from_task,
    _parse_clock_hour,
    _parse_money_amounts,
    _parse_raw_numbers,
    _parse_shape_sides,
    _skip_reason_for_task,
)

VisualKind = Literal[
    "ten_frame",  # dodawanie / odejmowanie do 20: kropki w ramkach dziesiątkowych
    "number_line",  # dodawanie / odejmowanie do 20, gdy kropek byłoby za dużo
    "array",  # mnożenie: prostokątny układ kropek
    "sharing",  # dzielenie: kropki do rozdzielenia na talerze
    "fraction",  # ułamki: koło podzielone na równe części
    "coins",  # pieniądze: polskie monety z nominałami
    "clock",  # czas: tarcza z cyframi
    "rectangle",  # obwody: prostokąt z opisanymi bokami
]

POLISH_COINS_ZL = (5, 2, 1)
NUMBER_LINE_MAX = 20


@dataclass(frozen=True)
class TaskVisual:
    kind: VisualKind
    a: int = 0
    b: int = 0
    op: str = "+"
    fractions: tuple[tuple[int, int], ...] = ()
    coin_groups: tuple[tuple[int, ...], ...] = ()
    hour: int = 0
    show_hands: bool = True

    @property
    def label_pl(self) -> str:
        """Krótki opis dla panelu jakości."""
        return {
            "ten_frame": "ramka dziesiątkowa",
            "number_line": "oś liczbowa",
            "array": "układ kropek",
            "sharing": "podział na talerze",
            "fraction": "koło ułamkowe",
            "coins": "monety",
            "clock": "zegar",
            "rectangle": "prostokąt z wymiarami",
        }[self.kind]


def coins_for_amount(amount_zl: int) -> tuple[int, ...]:
    """Najmniej monet 5 / 2 / 1 zł składających się na kwotę."""
    coins: list[int] = []
    rest = amount_zl
    for coin in POLISH_COINS_ZL:
        while rest >= coin:
            coins.append(coin)
            rest -= coin
    return tuple(coins)


_DRAW_HANDS_RE = re.compile(r"\b(narysuj|dorysuj|zaznacz)\b.*\bwskaz", re.IGNORECASE)


def task_visual_for(task: str, topic: str, profile: str, *, grade: int = 2) -> TaskVisual | None:
    """Pomoc wizualna dla zadania albo `None`, gdy nie da się jej pokazać uczciwie."""
    resolved = resolve_topic(topic, grade=grade)
    if resolved.capabilities.skip_images:
        return None
    family = visual_family_for_topic(topic) or ""

    if _skip_reason_for_task(task, topic, profile) is None and _is_task_safely_illustratable(task, topic, profile):
        visual = _visual_for_family(task, family)
        if visual is not None:
            return visual
    return _number_line_fallback(task, family)


def _visual_for_family(task: str, family: str) -> TaskVisual | None:
    if family == "ułamki":
        return TaskVisual("fraction", fractions=tuple(_parse_all_fractions_from_task(task)[:2]))
    if family == "pieniądze":
        amounts = _parse_money_amounts(task)
        return TaskVisual("coins", coin_groups=tuple(coins_for_amount(a) for a in amounts[:2]))
    if family == "czas":
        hour = _parse_clock_hour(task)
        if hour is None:
            return None
        hour = hour % 12 or 12
        return TaskVisual("clock", hour=hour, show_hands=not _DRAW_HANDS_RE.search(task))
    if family == "obwody":
        sides = _parse_shape_sides(task)
        width = sides[0]
        height = sides[1] if len(sides) > 1 else sides[0]
        return TaskVisual("rectangle", a=width, b=height)

    nums = _parse_raw_numbers(task)
    if len(nums) < 2:
        return None
    a, b = nums[0], nums[1]
    if family == "dodawanie" and a + b <= 20:
        return TaskVisual("ten_frame", a=a, b=b, op="+")
    if family == "odejmowanie" and b < a <= 20:
        return TaskVisual("ten_frame", a=a, b=b, op="-")
    if family == "mnożenie":
        return TaskVisual("array", a=a, b=b, op="×")
    if family == "dzielenie" and b > 0 and a % b == 0:
        return TaskVisual("sharing", a=a, b=b, op=":")
    return None


def _number_line_fallback(task: str, family: str) -> TaskVisual | None:
    """Oś 0–20 dla dodawania i odejmowania, gdy kropek byłoby za dużo dla profilu."""
    if family not in ("dodawanie", "odejmowanie"):
        return None
    nums = _parse_raw_numbers(task)
    if len(nums) < 2:
        return None
    a, b = nums[0], nums[1]
    if family == "dodawanie" and a + b <= NUMBER_LINE_MAX:
        return TaskVisual("number_line", a=a, b=b, op="+")
    if family == "odejmowanie" and b <= a <= NUMBER_LINE_MAX:
        return TaskVisual("number_line", a=a, b=b, op="-")
    return None


def task_visuals_for(tasks: list[str], topic: str, profile: str, *, grade: int = 2) -> list[TaskVisual | None]:
    return [task_visual_for(t, topic, profile, grade=grade) for t in tasks]
