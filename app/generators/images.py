"""
Generator grafiki dla karty pracy.

v1.x: Ikony zamiast prymitywnych kółek (jabłka, ciastka, gwiazdki, ryby, pizza)
+ widoczne znaki działań między grupami. Funkcje publiczne (`generate_worksheet_image`
oraz `generate_worksheet_images_for_tasks`) zachowują dotychczasową sygnaturę.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO
from typing import List, Tuple

from PIL import Image, ImageDraw  # pyright: ignore[reportMissingModuleSource]

from app.domain.profile_pedagogy import get_pedagogy_spec, visual_max_objects
from app.domain.educational_strategy import visual_theme_for_topic
from app.domain.topic_catalog import resolve_topic, visual_family_for_topic
from app.generators import icons


@dataclass(frozen=True)
class TaskImageSlot:
    """Diagnostyka ilustracji per zadanie (plan naprawczy profili)."""

    task_index: int
    rendered: bool
    image_bytes: bytes
    skip_reason: str | None = None


@dataclass(frozen=True)
class TaskImagesResult:
    slots: tuple[TaskImageSlot, ...]

    @property
    def image_bytes_list(self) -> list[bytes]:
        return [s.image_bytes for s in self.slots]

    @property
    def rendered_count(self) -> int:
        return sum(1 for s in self.slots if s.rendered)


# Tło stron i ikon (jasne, neutralne – nie konkuruje z ikonami).
_BG = "#fbfbf8"
_GROUP_BG = "#ffffff"
_GROUP_EDGE = "#d6d6d0"
_ACTION_EDGE = "#78909c"
_TAKEN_BG = "#fff3e0"


def visual_prompt_for_topic(topic: str, *, grade: int = 2) -> dict[str, str]:
    """Topic -> visual motif -> image prompt, for diagnostics and future image APIs."""
    resolved = resolve_topic(topic, grade=grade)
    theme = visual_theme_for_topic(resolved)
    return {
        "topic_id": resolved.topic_id,
        "visual_family": theme.family,
        "motif": theme.motif,
        "learning_role_pl": theme.learning_role_pl,
        "prompt_pl": theme.prompt_pl,
    }


def generate_worksheet_image(
    topic: str,
    profile: str,
    size: Tuple[int, int] = (320, 160),
    grade: int = 2,
) -> bytes:
    """
    Jedna ilustracja tematyczna pod metadanymi karty (dla profili standardowy/zdolny/dysleksja,
    gdy włączone w UI). Pokazuje przykładowy „kanonik" działania: 3 jabłka + 2 jabłka, itp.

    Dla tematów bez wsparcia wizualnego zwraca pusty `bytes` –
    PDF generator pominie rysowanie ilustracji.
    """
    resolved = resolve_topic(topic, grade=grade)
    if resolved.capabilities.skip_images:
        return b""
    topic_lower = visual_family_for_topic(topic) or (topic or "").strip().lower()

    w, h = size
    img = Image.new("RGB", (w, h), _BG)
    draw = ImageDraw.Draw(img)

    margin = 20
    aw = w - 2 * margin
    ah = h - 2 * margin
    bx, by = margin, margin

    if topic_lower == "ułamki":
        _draw_pizza_centered(draw, bx, by, aw, ah, num=1, den=2)
    elif topic_lower == "pieniądze":
        _draw_money_scene(draw, bx, by, aw, ah, 3, 2)
    elif topic_lower == "czas":
        _draw_clock_scene(draw, bx, by, aw, ah, hour=3)
    elif topic_lower == "obwody":
        _draw_perimeter_scene(draw, bx, by, aw, ah, width=4, height=4)
    elif topic_lower == "mnożenie":
        _draw_grid(draw, bx, by, aw, ah, rows=2, cols=3, kind="star_gold", op_kind="×")
    else:
        # Domyślnie: dwie grupy z operatorem (np. dodawanie/odejmowanie/dzielenie).
        theme = icons.get_theme(topic_lower)
        if "left" in theme and "right" in theme:
            _draw_two_groups(
                draw, bx, by, aw, ah,
                n1=3, n2=2,
                left_kind=theme["left"], right_kind=theme["right"],
                op=theme["op"],
            )
        else:
            _draw_two_groups(draw, bx, by, aw, ah, n1=3, n2=2,
                             left_kind="apple_red", right_kind="apple_green", op="+")

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# --------------------------------------------------------------------
# Ilustracja per zadanie (pełna szerokość treści PDF)
# --------------------------------------------------------------------


# --------------------------------------------------------------------
# „Czy to zadanie da się uczciwie zilustrować?"
# --------------------------------------------------------------------
#
# Ilustracja per zadanie ma sens tylko dla małych liczb, bo manipulujemy
# fizycznymi obiektami (jabłka, ciastka, gwiazdki). Powyżej tych progów
# obrazek zaczyna kłamać (np. 5×5 zamiast 15×6) – wtedy świadomie nic
# nie generujemy. „Lepiej brak niż błędna ilustracja".
_SAFE_LIMITS = {
    "dodawanie":   {"a_max": 8,  "b_max": 8,  "sum_max": 16},
    "odejmowanie": {"a_max": 10, "b_max": 10},          # b musi być < a
    "mnożenie":    {"a_max": 5,  "b_max": 5},
    "dzielenie":   {"a_max": 12, "b_max": 3},           # a/b musi być całkowite
    "ułamki":      {"den_max": 6},
    "pieniądze":   {"coin_max": 8},
    "czas":        {"hour_max": 12},
    "obwody":      {"side_max": 12},
}


def _profile_safe_limits(profile: str, family: str) -> dict | None:
    """Profile-aware limity obiektów w ilustracji (gęstsze dla dyskalkulii)."""
    base = _SAFE_LIMITS.get(family)
    if not base:
        return None
    limits = dict(base)
    spec = get_pedagogy_spec(profile)
    cap = visual_max_objects(profile)
    if family == "dodawanie":
        limits["a_max"] = min(limits["a_max"], cap)
        limits["b_max"] = min(limits["b_max"], cap)
        limits["sum_max"] = min(limits.get("sum_max", 16), cap * 2)
    elif family == "mnożenie":
        side = max(2, int(cap**0.5))
        limits["a_max"] = min(limits["a_max"], side)
        limits["b_max"] = min(limits["b_max"], side)
    elif family == "odejmowanie":
        limits["a_max"] = min(limits["a_max"], cap + 2)
        limits["b_max"] = min(limits["b_max"], cap)
    elif family == "pieniądze":
        limits["coin_max"] = min(limits["coin_max"], cap)
    if spec.profile_group == "dyskalkulia":
        limits["den_max"] = min(limits.get("den_max", 6), 6)
    elif spec.profile_group == "adhd":
        limits["den_max"] = min(limits.get("den_max", 6), 4)
        if family == "pieniądze":
            limits["coin_max"] = min(limits.get("coin_max", 8), cap)
        if family == "obwody":
            limits["side_max"] = min(limits.get("side_max", 12), 8)
    return limits


def _skip_reason_for_task(task: str, topic: str, profile: str) -> str | None:
    """Powód pominięcia ilustracji — do panelu nauczyciela."""
    resolved = resolve_topic(topic, grade=2)
    if resolved.capabilities.skip_images:
        return "temat bez ilustracji"
    family = visual_family_for_topic(topic)
    if not family:
        return "brak rodziny wizualnej dla tematu"
    limits = _profile_safe_limits(profile, family)
    if not limits:
        return "nieobsługiwany typ zadania wizualnie"

    if family == "ułamki":
        fractions = _parse_all_fractions_from_task(task)
        if not fractions:
            return "brak ułamka w treści zadania"
        if any(den > limits.get("den_max", 6) for _, den in fractions):
            return "mianownik za duży do uczciwej reprezentacji"
        return None

    if family == "pieniądze":
        amounts = _parse_money_amounts(task)
        cap = limits.get("coin_max", 8)
        if len(amounts) < 1:
            return "brak kwot do zilustrowania monetami"
        if any(a > cap for a in amounts):
            return "kwota za duża do ikon monet (profil)"
        return None

    if family == "czas":
        hour = _parse_clock_hour(task)
        if hour is None:
            return "brak jednoznacznej godziny w zadaniu"
        if hour > limits.get("hour_max", 12):
            return "godzina poza zakresem zegara"
        return None

    if family == "obwody":
        sides = _parse_shape_sides(task)
        cap = limits.get("side_max", 12)
        if not sides:
            return "brak wymiarów figury w zadaniu"
        if any(s > cap for s in sides):
            return "bok za duży do rysunku pomocniczego"
        return None

    nums = _parse_raw_numbers(task)
    if len(nums) < 2:
        return "za mało liczb do zilustrowania"

    a, b = nums[0], nums[1]
    if family == "dodawanie":
        if a > limits["a_max"] or b > limits["b_max"]:
            return "liczby za duże do ikon (profil)"
        if (a + b) > limits.get("sum_max", 16):
            return "suma za duża do uczciwej reprezentacji"
    elif family == "odejmowanie":
        if a > limits["a_max"] or b > limits["b_max"] or b >= a:
            return "liczby poza bezpiecznym zakresem odejmowania"
    elif family == "mnożenie":
        if a > limits["a_max"] or b > limits["b_max"]:
            return "czynniki za duże do siatki ikon"
    elif family == "dzielenie":
        if a > limits["a_max"] or b > limits["b_max"] or b == 0 or a % b != 0:
            return "dzielenie nie da się uczciwie pokazać ikonami"
    return None


def _is_task_safely_illustratable(task: str, topic: str, profile: str = "standardowy") -> bool:
    """
    Zwraca True, jeśli zadanie da się uczciwie zilustrować ikonami.
    Logika świadomie konserwatywna – wolimy odrzucić zadanie ilustrowalne,
    niż pokazać mylący obrazek.
    """
    family = visual_family_for_topic(topic)
    if not family:
        return False

    limits = _profile_safe_limits(profile, family)
    if not limits:
        return False

    if family == "ułamki":
        fractions = _parse_all_fractions_from_task(task)
        if not fractions:
            return False
        return all(2 <= den <= limits["den_max"] and 0 <= num <= den for num, den in fractions)

    if family == "pieniądze":
        amounts = _parse_money_amounts(task)
        cap = limits.get("coin_max", 8)
        return bool(amounts) and all(0 < a <= cap for a in amounts)

    if family == "czas":
        hour = _parse_clock_hour(task)
        return hour is not None and 1 <= hour <= limits.get("hour_max", 12)

    if family == "obwody":
        sides = _parse_shape_sides(task)
        cap = limits.get("side_max", 12)
        return bool(sides) and all(0 < s <= cap for s in sides)

    nums = _parse_raw_numbers(task)
    if len(nums) < 2:
        return False
    a, b = nums[0], nums[1]

    if family == "dodawanie":
        return a <= limits["a_max"] and b <= limits["b_max"] and (a + b) <= limits["sum_max"]
    if family == "odejmowanie":
        return a <= limits["a_max"] and b <= limits["b_max"] and b < a
    if family == "mnożenie":
        return a <= limits["a_max"] and b <= limits["b_max"]
    if family == "dzielenie":
        return a <= limits["a_max"] and 0 < b <= limits["b_max"] and a % b == 0

    return False


def generate_worksheet_images_for_tasks_with_diagnostics(
    tasks: List[str],
    topic: str,
    profile: str,
    size: Tuple[int, int] = (480, 110),
    grade: int = 2,
) -> TaskImagesResult:
    """
    Ilustracje per zadanie z diagnostyką (rendered / skip_reason).
    """
    resolved = resolve_topic(topic, grade=grade)
    if resolved.capabilities.skip_images:
        return TaskImagesResult(
            slots=tuple(
                TaskImageSlot(i, False, b"", "temat bez ilustracji")
                for i in range(len(tasks))
            )
        )

    family = visual_family_for_topic(topic) or ""
    slots: list[TaskImageSlot] = []
    w, h = size
    margin = 16
    pad = 8
    aw = w - 2 * margin - 2 * pad
    ah = h - 2 * margin - 2 * pad
    bx, by = margin + pad, margin + pad

    for idx, task in enumerate(tasks):
        reason = _skip_reason_for_task(task, topic, profile)
        if reason or not _is_task_safely_illustratable(task, topic, profile):
            slots.append(
                TaskImageSlot(idx, False, b"", reason or "poza bezpiecznym zakresem")
            )
            continue

        img = Image.new("RGB", (w, h), _BG)
        draw = ImageDraw.Draw(img)

        if family == "ułamki":
            fractions = _parse_all_fractions_from_task(task)
            _draw_fraction_pizzas(draw, bx, by, aw, ah, fractions[:2])
        elif family == "pieniądze":
            amounts = _parse_money_amounts(task)
            if len(amounts) >= 2:
                _draw_money_scene(draw, bx, by, aw, ah, amounts[0], amounts[1])
            elif len(amounts) == 1:
                _draw_money_scene(draw, bx, by, aw, ah, amounts[0], 0)
        elif family == "czas":
            hour = _parse_clock_hour(task) or 12
            _draw_clock_scene(draw, bx, by, aw, ah, hour=hour)
        elif family == "obwody":
            sides = _parse_shape_sides(task)
            if len(sides) >= 2:
                _draw_perimeter_scene(draw, bx, by, aw, ah, width=sides[0], height=sides[1])
            elif len(sides) == 1:
                _draw_perimeter_scene(draw, bx, by, aw, ah, width=sides[0], height=sides[0])
        elif family == "mnożenie":
            nums = _parse_raw_numbers(task)
            rows, cols = nums[0], nums[1]
            _draw_grid(draw, bx, by, aw, ah, rows=rows, cols=cols, kind="star_gold", op_kind="×")
        elif family == "odejmowanie":
            nums = _parse_raw_numbers(task)
            n_total, n_gone = nums[0], nums[1]
            _draw_subtraction_row(draw, bx, by, aw, ah, n_total=n_total, n_gone=n_gone)
        elif family == "dzielenie":
            nums = _parse_raw_numbers(task)
            a, b = nums[0], nums[1]
            per_group = a // b
            _draw_division_groups(
                draw, bx, by, aw, ah,
                n_groups=b, per_group=per_group,
                kind="fish_blue",
            )
        else:
            nums = _parse_raw_numbers(task)
            n1, n2 = nums[0], nums[1]
            theme = icons.get_theme(family)
            _draw_two_groups(
                draw, bx, by, aw, ah,
                n1=n1, n2=n2,
                left_kind=theme.get("left", "apple_red"),
                right_kind=theme.get("right", "apple_green"),
                op=theme.get("op", "+"),
            )

        buf = BytesIO()
        img.save(buf, format="PNG")
        slots.append(TaskImageSlot(idx, True, buf.getvalue(), None))

    return TaskImagesResult(slots=tuple(slots))


def generate_worksheet_images_for_tasks(
    tasks: List[str],
    topic: str,
    profile: str,
    size: Tuple[int, int] = (480, 110),
    grade: int = 2,
) -> List[bytes]:
    """
    Ilustracja per zadanie – TYLKO dla zadań w bezpiecznym zakresie (`_SAFE_LIMITS`).
    Dla pozostałych zwracamy pusty `b""` – PDF generator pominie rysowanie.

    Mapowanie tematów:
    - dodawanie  → 2 grupy jabłek z „+" między nimi
    - odejmowanie → ciastka, ostatnie z odgryzieniami (bitten)
    - mnożenie    → siatka gwiazdek wiersze × kolumny
    - dzielenie   → ryby pogrupowane w równe stada
    - ułamki      → pizza (num/den z treści)
    - równania    → świadomie pomijane całkowicie

    Zwraca listę długości `len(tasks)` (puste bytes dla nieilustrowalnych zadań).
    """
    return generate_worksheet_images_for_tasks_with_diagnostics(
        tasks, topic, profile, size=size, grade=grade
    ).image_bytes_list


# --------------------------------------------------------------------
# Helpery rysowania scen
# --------------------------------------------------------------------


def _icon_size_for_row(area_w: int, area_h: int, n: int, gap: int = 6, max_size: int = 44) -> int:
    """Rozmiar ikony, żeby `n` mieściło się w `area_w` (1 wiersz)."""
    if n <= 0:
        return min(area_w, area_h, max_size)
    ss_w = (area_w - (n - 1) * gap) // n
    return max(8, min(ss_w, area_h, max_size))


def _draw_two_groups(
    draw,
    bx: int,
    by: int,
    aw: int,
    ah: int,
    n1: int,
    n2: int,
    left_kind: str,
    right_kind: str,
    op: str,
) -> None:
    """Rysuje 2 grupy ikon + znak działania między nimi (np. 3 jabłka + 2 jabłka)."""
    # Rezerwujemy ~10% szerokości na operator, ale min 28px / max 56px.
    op_w = max(28, min(int(aw * 0.10), 56))
    side_w = (aw - op_w) // 2
    cy = by + ah // 2
    box_pad = 4
    label_h = 14

    _draw_group_panel(draw, bx, by, side_w - box_pad, ah, "pierwsza grupa")
    _draw_group_panel(draw, bx + side_w + op_w + box_pad, by, side_w - box_pad, ah, "dodajemy")

    # Pojedyncza ikona: max ze strony niech zmieści n1 lub n2 (ten większy)
    n_max = max(n1, n2, 1)
    ss = _icon_size_for_row(side_w - 2 * box_pad, ah - label_h, n_max, gap=6, max_size=42)

    if n1 > 0:
        _draw_icon_row(draw, bx + box_pad, by + label_h, side_w - 2 * box_pad, ah - label_h, count=n1, kind=left_kind, ss=ss, gap=6)
    if op:
        icons.draw_op(draw, bx + side_w + op_w // 2, cy, op_w - 8, op)
    if n2 > 0:
        _draw_icon_row(draw, bx + side_w + op_w + box_pad, by + label_h, side_w - 2 * box_pad, ah - label_h, count=n2, kind=right_kind, ss=ss, gap=6)


def _draw_division_groups(
    draw,
    bx: int,
    by: int,
    aw: int,
    ah: int,
    n_groups: int,
    per_group: int,
    kind: str,
) -> None:
    """Rysuje `n_groups` rozdzielonych grup po `per_group` ikon każda (uczciwa
    wizualizacja dzielenia: 8 ryb podzielone na 2 stada = 2 grupy po 4 ryby)."""
    if n_groups <= 0 or per_group <= 0:
        return
    group_gap = max(16, aw // (n_groups * 6))
    group_w = (aw - group_gap * (n_groups - 1)) // n_groups
    cy = by + ah // 2
    ss = _icon_size_for_row(group_w, ah, per_group, gap=4, max_size=40)
    for g in range(n_groups):
        gx = bx + g * (group_w + group_gap)
        total_w = per_group * ss + (per_group - 1) * 4
        start_x = gx + (group_w - total_w) // 2 + ss // 2
        for i in range(per_group):
            x = start_x + i * (ss + 4)
            icons.draw_icon(draw, kind, x, cy, ss)


def _draw_subtraction_row(
    draw,
    bx: int,
    by: int,
    aw: int,
    ah: int,
    n_total: int,
    n_gone: int,
) -> None:
    """Wizualizacja odejmowania: zostaje / zabieramy, z przekreśleniem zabranych."""
    label_h = 14
    remaining = max(0, n_total - n_gone)
    op_w = max(28, min(int(aw * 0.10), 52))
    left_w = int((aw - op_w) * 0.62)
    right_w = aw - op_w - left_w
    _draw_group_panel(draw, bx, by, left_w, ah, "zostaje")
    _draw_group_panel(draw, bx + left_w + op_w, by, right_w, ah, "zabieramy", fill=_TAKEN_BG)
    icons.draw_op(draw, bx + left_w + op_w // 2, by + ah // 2, op_w - 8, "−")

    cy = by + label_h + (ah - label_h) // 2
    if remaining > 0:
        ss_left = _icon_size_for_row(left_w - 10, ah - label_h, remaining, gap=8, max_size=42)
        _draw_icon_row(draw, bx + 5, by + label_h, left_w - 10, ah - label_h, count=remaining, kind="cookie", ss=ss_left, gap=8)
    if n_gone <= 0:
        return
    ss = _icon_size_for_row(right_w - 10, ah - label_h, n_gone, gap=8, max_size=42)
    total_w = n_gone * ss + (n_gone - 1) * 8
    start_x = bx + left_w + op_w + 5 + ((right_w - 10) - total_w) // 2 + ss // 2
    n_visible = n_total - n_gone
    for i in range(n_gone):
        x = start_x + i * (ss + 8)
        icons.draw_icon(draw, "cookie_bitten", x, cy, ss)
        r = ss // 2 + 3
        draw.line([(x - r, cy - r), (x + r, cy + r)], fill="#c62828", width=2)
        draw.line([(x - r, cy + r), (x + r, cy - r)], fill="#c62828", width=2)


def _draw_group_panel(
    draw,
    x: int,
    y: int,
    w: int,
    h: int,
    label: str,
    *,
    fill: str = _GROUP_BG,
) -> None:
    draw.rounded_rectangle(
        [x, y, x + max(1, w), y + max(1, h)],
        radius=10,
        fill=fill,
        outline=_GROUP_EDGE,
        width=1,
    )
    draw.text((x + 8, y + 3), label, fill="#455a64")


def _draw_grid(
    draw,
    bx: int,
    by: int,
    aw: int,
    ah: int,
    rows: int,
    cols: int,
    kind: str,
    op_kind: str = "",
) -> None:
    """Siatka ikon `rows × cols`. Operator kind ignorowany (zostawiony dla spójności API)."""
    gap = 6
    # Rozmiar ikony tak, by całość mieściła się w aw × ah
    ss_w = (aw - (cols - 1) * gap) // max(cols, 1)
    ss_h = (ah - (rows - 1) * gap) // max(rows, 1)
    ss = max(8, min(ss_w, ss_h, 40))
    total_w = cols * ss + (cols - 1) * gap
    total_h = rows * ss + (rows - 1) * gap
    ox = bx + (aw - total_w) // 2 + ss // 2
    oy = by + (ah - total_h) // 2 + ss // 2
    for r in range(rows):
        for c in range(cols):
            x = ox + c * (ss + gap)
            y = oy + r * (ss + gap)
            icons.draw_icon(draw, kind, x, y, ss)


def _draw_money_scene(
    draw,
    bx: int,
    by: int,
    aw: int,
    ah: int,
    n1: int,
    n2: int,
) -> None:
    """Dwie grupy monet (suma / reszta w zł)."""
    op_w = max(24, min(int(aw * 0.08), 40))
    side_w = (aw - op_w) // 2
    cy = by + ah // 2
    n_max = max(n1, n2, 1)
    ss = _icon_size_for_row(side_w, ah, n_max, gap=4, max_size=36)
    if n1 > 0:
        _draw_coin_row(draw, bx, by, side_w, ah, count=n1, ss=ss)
    if n2 > 0:
        icons.draw_op(draw, bx + side_w + op_w // 2, cy, op_w - 6, "+")
        _draw_coin_row(draw, bx + side_w + op_w, by, side_w, ah, count=n2, ss=ss)


def _draw_coin_row(
    draw,
    bx: int,
    by: int,
    aw: int,
    ah: int,
    count: int,
    ss: int,
) -> None:
    gap = 4
    total_w = count * ss + (count - 1) * gap
    start_x = bx + (aw - total_w) // 2 + ss // 2
    cy = by + ah // 2
    for i in range(count):
        x = start_x + i * (ss + gap)
        icons.draw_coin(draw, x, cy, ss)


def _draw_clock_scene(draw, bx: int, by: int, aw: int, ah: int, hour: int) -> None:
    r = max(20, min(aw, ah) // 2 - 8)
    icons.draw_clock_face(draw, bx + aw // 2, by + ah // 2, r * 2, hour=hour)


def _draw_perimeter_scene(
    draw,
    bx: int,
    by: int,
    aw: int,
    ah: int,
    width: int,
    height: int,
) -> None:
    """Prostokąt wycentrowany — boki w jednostkach logicznych (skala do obszaru)."""
    scale = min((aw - 20) // max(width, 1), (ah - 20) // max(height, 1), 18)
    w_px = max(24, width * scale)
    h_px = max(24, height * scale)
    icons.draw_labeled_rect(draw, bx + aw // 2, by + ah // 2, w_px, h_px)


def _draw_pizza_centered(draw, bx: int, by: int, aw: int, ah: int, num: int, den: int) -> None:
    """Pojedyncza pizza wycentrowana w obszarze."""
    radius = max(20, min(aw // 2 - 6, ah // 2 - 6, 60))
    cx = bx + aw // 2
    cy = by + ah // 2
    icons.draw_pizza(draw, cx, cy, radius, num=num, den=den)


def _draw_fraction_pizzas(
    draw,
    bx: int,
    by: int,
    aw: int,
    ah: int,
    fractions: List[Tuple[int, int]],
) -> None:
    """Do 2 pizz obok siebie (np. 1/2 i 1/4)."""
    n = max(1, len(fractions))
    cell_w = aw // n
    radius = max(18, min(cell_w // 2 - 8, ah // 2 - 6, 50))
    for idx, (num, den) in enumerate(fractions):
        cx = bx + cell_w * idx + cell_w // 2
        cy = by + ah // 2
        icons.draw_pizza(draw, cx, cy, radius, num=num, den=den)


def _draw_icon_row(
    draw,
    bx: int,
    by: int,
    aw: int,
    ah: int,
    count: int,
    kind: str,
    ss: int,
    gap: int = 6,
) -> None:
    """Rysuje `count` ikon w jednym poziomym rzędzie wycentrowanym w (bx,by,aw,ah)."""
    if count <= 0:
        return
    total_w = count * ss + (count - 1) * gap
    start_x = bx + (aw - total_w) // 2 + ss // 2
    cy = by + ah // 2
    for i in range(count):
        x = start_x + i * (ss + gap)
        icons.draw_icon(draw, kind, x, cy, ss)


# --------------------------------------------------------------------
# Parsery treści zadania (pomocnicze)
# --------------------------------------------------------------------


def _parse_numbers_from_task(task: str) -> List[int]:
    """Wyciąga liczby z treści zadania, każda przycięta do 12 (legacy – używane przez
    `generate_worksheet_image` dla tematycznego nagłówka)."""
    cleaned = re.sub(r"\d+\s*/\s*\d+", " ", task)
    numbers = re.findall(r"\d+", cleaned)
    return [min(int(n), 12) for n in numbers[:4]]


def _parse_raw_numbers(task: str) -> List[int]:
    """
    Wyciąga liczby z treści zadania BEZ przycinania (używane do bezpiecznej
    walidacji ilustrowalności – tam decydujemy, czy w ogóle rysujemy).
    Ułamki a/b są usuwane przed parsowaniem.
    """
    cleaned = re.sub(r"\d+\s*/\s*\d+", " ", task)
    return [int(n) for n in re.findall(r"\d+", cleaned)[:4]]


def _parse_fraction_from_task(task: str) -> Tuple[int, int] | None:
    """Wyciąga pierwszy ułamek z treści (np. 'Zaznacz 1/2 koła' -> (1, 2))."""
    m = re.search(r"(\d+)\s*/\s*(\d+)", task)
    if not m:
        return None
    num, den = int(m.group(1)), int(m.group(2))
    if den <= 0 or num < 0 or num > den:
        return None
    den = min(den, 8)
    num = min(num, den)
    return (num, den)


def _parse_money_amounts(task: str) -> List[int]:
    """Kwoty w zł z treści (np. „5 zł + 2 zł”)."""
    found = re.findall(r"(\d+)\s*zł", task.casefold().replace("zl", "zł"))
    return [int(x) for x in found[:2]]


def _parse_clock_hour(task: str) -> int | None:
    """Godzina z zegara analogowego lub 14:00."""
    m = re.search(r"pokazuje\s+(\d{1,2})", task, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d{1,2}):(\d{2})", task)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d{1,2}):00", task)
    if m:
        return int(m.group(1))
    return None


def _parse_shape_sides(task: str) -> List[int]:
    """Boki z cm (kwadrat: jeden bok; prostokąt: dwa)."""
    nums = [int(n) for n in re.findall(r"(\d+)\s*cm", task)]
    if "kwadrat" in task.casefold() and nums:
        return [nums[0]]
    if len(nums) >= 2:
        return nums[:2]
    return nums[:1] if nums else []


def _parse_all_fractions_from_task(task: str) -> List[Tuple[int, int]]:
    """Wyciąga wszystkie ułamki z treści (np. '1/2 + 1/4' -> [(1,2), (1,4)]). Max 2 ułamki."""
    out: List[Tuple[int, int]] = []
    for m in re.finditer(r"(\d+)\s*/\s*(\d+)", task):
        if len(out) >= 2:
            break
        num, den = int(m.group(1)), int(m.group(2))
        if den <= 0 or num < 0 or num > den:
            continue
        den = min(den, 8)
        num = min(num, den)
        out.append((num, den))
    return out
