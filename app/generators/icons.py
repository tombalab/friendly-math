"""
Biblioteczka ikon do ilustracji w PDF (Pillow primitives).

Każda funkcja rysuje JEDNĄ rozpoznawalną ikonę (jabłko, gwiazdka, ryba, ciastko,
cukierek, pizza) o zadanym `size` (szerokość/wysokość) wokół punktu (cx, cy).
Plus rysowanie znaków działań (+, −, ×, ÷, =) między grupami ikon.

Filozofia:
- Bez zewnętrznych assetów (PNG/SVG) – wszystko rysowane proceduralnie z prymitywów Pillow.
  To upraszcza repo i pozwala skalować ikony bez utraty jakości.
- Paleta przyjazna dzieciom, ale nie krzykliwa (umiarkowane nasycenie).
- Cienki, jednolity obrys (#7b7b7b) dla wszystkich ikon – spójny look.
"""
from __future__ import annotations

import math
from typing import Callable, Dict


# Paleta – stonowana, ciepła, czytelna (działa również w druku czarno-białym).
APPLE_RED = "#ef5350"
APPLE_GREEN = "#aed581"
APPLE_LEAF = "#66bb6a"
APPLE_STEM = "#6d4c41"

STAR_GOLD = "#ffca28"
STAR_BLUE = "#42a5f5"

FISH_BLUE = "#4fc3f7"
FISH_ORANGE = "#ffa726"
FISH_EYE = "#212121"

COOKIE_TAN = "#d7a86e"
COOKIE_DOT = "#5d4037"

CANDY_PINK = "#f06292"
CANDY_PURPLE = "#ab47bc"

PIZZA_TOPPING = "#ef5350"
PIZZA_DOUGH = "#fff8e1"
PIZZA_CRUST = "#d7a86e"

OUTLINE = "#7b7b7b"
OP_COLOR = "#424242"


def draw_apple(draw, cx: int, cy: int, size: int, color: str = APPLE_RED) -> None:
    """Jabłko: koło z nacięciem na górze + listek + ogonek."""
    r = max(4, size // 2)
    # Korpus – delikatnie spłaszczony (lekko szerszy niż wysoki)
    body = [cx - r, cy - r + 1, cx + r, cy + r]
    draw.ellipse(body, fill=color, outline=OUTLINE, width=1)
    # Drugi mały owal symulujący nacięcie u góry (subtelne)
    notch_w, notch_h = max(2, r // 4), max(1, r // 6)
    draw.ellipse(
        [cx - notch_w, cy - r - 1, cx + notch_w, cy - r + notch_h],
        fill=color,
    )
    # Ogonek
    stem_w, stem_h = max(1, r // 8), max(2, r // 3)
    draw.rectangle(
        [cx - stem_w, cy - r - stem_h, cx + stem_w, cy - r + 1],
        fill=APPLE_STEM,
    )
    # Listek – owal po prawej skosie ogonka
    leaf_w, leaf_h = max(3, r // 2), max(2, r // 3)
    draw.ellipse(
        [cx + 1, cy - r - leaf_h, cx + 1 + leaf_w, cy - r + leaf_h // 2],
        fill=APPLE_LEAF,
        outline=OUTLINE,
        width=1,
    )


def draw_star(draw, cx: int, cy: int, size: int, color: str = STAR_GOLD) -> None:
    """Gwiazdka 5-ramienna."""
    r_outer = max(3, size // 2)
    r_inner = max(1, int(r_outer * 0.42))
    points = []
    for i in range(10):
        r = r_outer if i % 2 == 0 else r_inner
        angle = -math.pi / 2 + i * math.pi / 5
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        points.append((x, y))
    draw.polygon(points, fill=color, outline=OUTLINE)


def draw_fish(draw, cx: int, cy: int, size: int, color: str = FISH_BLUE) -> None:
    """Ryba: korpus (owal) + ogon (trójkąt) + oko."""
    r = max(4, size // 2)
    body_l = cx - r + r // 4
    body_r = cx + r - r // 3
    draw.ellipse(
        [body_l, cy - r // 2, body_r, cy + r // 2],
        fill=color,
        outline=OUTLINE,
        width=1,
    )
    # Ogon (po prawej)
    tail = [
        (body_r - 1, cy),
        (cx + r, cy - r // 2),
        (cx + r, cy + r // 2),
    ]
    draw.polygon(tail, fill=color, outline=OUTLINE)
    # Oko – mała czarna kropka
    eye_r = max(1, r // 8)
    eye_cx = body_l + r // 2
    eye_cy = cy - r // 6
    draw.ellipse(
        [eye_cx - eye_r, eye_cy - eye_r, eye_cx + eye_r, eye_cy + eye_r],
        fill=FISH_EYE,
    )


def draw_cookie(draw, cx: int, cy: int, size: int, bitten: bool = False) -> None:
    """Ciastko: brązowe koło z kropkami czekolady. Jeśli bitten=True – brakuje kawałka."""
    r = max(4, size // 2)
    bbox = [cx - r, cy - r, cx + r, cy + r]
    if bitten:
        # „Pacman" – pełne koło minus klin po prawej (45° w sumie)
        draw.pieslice(bbox, start=205, end=155, fill=COOKIE_TAN, outline=OUTLINE, width=1)
    else:
        draw.ellipse(bbox, fill=COOKIE_TAN, outline=OUTLINE, width=1)
    # Kropki czekolady – stała pozycja względem środka
    dot_r = max(1, r // 5)
    offsets = [(-0.5, -0.45), (0.4, 0.4), (-0.45, 0.45), (0.45, -0.4), (0.0, 0.0)]
    for ox, oy in offsets:
        dx = int(ox * r)
        dy = int(oy * r)
        # Pomiń kropkę w odgryzionym kawałku, żeby nie wyglądała jak unosząca się w powietrzu
        if bitten and dx > r // 3 and abs(dy) < r // 3:
            continue
        x = cx + dx
        y = cy + dy
        draw.ellipse([x - dot_r, y - dot_r, x + dot_r, y + dot_r], fill=COOKIE_DOT)


def draw_candy(draw, cx: int, cy: int, size: int, color: str = CANDY_PINK) -> None:
    """Cukierek: prostokąt korpusu + dwa trójkąty po bokach (zawijka)."""
    body_w = max(4, int(size * 0.55))
    body_h = max(4, int(size * 0.45))
    half_w = body_w // 2
    half_h = body_h // 2
    draw.rectangle(
        [cx - half_w, cy - half_h, cx + half_w, cy + half_h],
        fill=color,
        outline=OUTLINE,
        width=1,
    )
    wing = max(3, body_h)
    # Lewy zawinięty bok
    draw.polygon(
        [
            (cx - half_w, cy - half_h),
            (cx - half_w - wing, cy - half_h - wing // 2),
            (cx - half_w - wing, cy + half_h + wing // 2),
            (cx - half_w, cy + half_h),
        ],
        fill=color,
        outline=OUTLINE,
    )
    # Prawy zawinięty bok
    draw.polygon(
        [
            (cx + half_w, cy - half_h),
            (cx + half_w + wing, cy - half_h - wing // 2),
            (cx + half_w + wing, cy + half_h + wing // 2),
            (cx + half_w, cy + half_h),
        ],
        fill=color,
        outline=OUTLINE,
    )


def draw_pizza(
    draw,
    cx: int,
    cy: int,
    radius: int,
    num: int,
    den: int,
    topping: str = PIZZA_TOPPING,
    dough: str = PIZZA_DOUGH,
    crust_thickness: int = 3,
) -> None:
    """Pizza okrągła podzielona na `den` kawałków, `num` wypełnionych dodatkiem."""
    bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
    step = 360.0 / den
    for i in range(den):
        sa = -90 + i * step
        ea = sa + step
        fill = topping if i < num else dough
        draw.pieslice(bbox, start=sa, end=ea, fill=fill, outline=OUTLINE, width=1)
    # „Skórka" – grubszy obrys zewnętrzny w odcieniu pieczywa
    draw.ellipse(bbox, outline=PIZZA_CRUST, width=crust_thickness)


def draw_op(draw, cx: int, cy: int, size: int, op: str, color: str = OP_COLOR) -> None:
    """Rysuje znak działania (+, −, ×, ÷, =) w punkcie (cx, cy) o szerokości `size`."""
    s = max(6, size)
    arm = s // 3
    w = max(2, s // 8)
    if op == "+":
        draw.line([(cx - arm, cy), (cx + arm, cy)], fill=color, width=w)
        draw.line([(cx, cy - arm), (cx, cy + arm)], fill=color, width=w)
    elif op in ("-", "−"):
        draw.line([(cx - arm, cy), (cx + arm, cy)], fill=color, width=w)
    elif op in ("×", "x", "*"):
        draw.line([(cx - arm, cy - arm), (cx + arm, cy + arm)], fill=color, width=w)
        draw.line([(cx + arm, cy - arm), (cx - arm, cy + arm)], fill=color, width=w)
    elif op in ("÷", ":", "/"):
        # Kropka–kreska–kropka
        dot_r = max(2, s // 8)
        draw.line([(cx - arm, cy), (cx + arm, cy)], fill=color, width=w)
        draw.ellipse(
            [cx - dot_r, cy - arm - dot_r, cx + dot_r, cy - arm + dot_r],
            fill=color,
        )
        draw.ellipse(
            [cx - dot_r, cy + arm - dot_r, cx + dot_r, cy + arm + dot_r],
            fill=color,
        )
    elif op == "=":
        gap = s // 6
        draw.line([(cx - arm, cy - gap), (cx + arm, cy - gap)], fill=color, width=w)
        draw.line([(cx - arm, cy + gap), (cx + arm, cy + gap)], fill=color, width=w)


# Mapowanie nazw → funkcje rysujące. Pozwala wywołać draw_icon("apple", ...) bez ifów.
_ICONS: Dict[str, Callable] = {
    "apple_red": lambda d, x, y, s: draw_apple(d, x, y, s, color=APPLE_RED),
    "apple_green": lambda d, x, y, s: draw_apple(d, x, y, s, color=APPLE_GREEN),
    "star_gold": lambda d, x, y, s: draw_star(d, x, y, s, color=STAR_GOLD),
    "star_blue": lambda d, x, y, s: draw_star(d, x, y, s, color=STAR_BLUE),
    "fish_blue": lambda d, x, y, s: draw_fish(d, x, y, s, color=FISH_BLUE),
    "fish_orange": lambda d, x, y, s: draw_fish(d, x, y, s, color=FISH_ORANGE),
    "cookie": lambda d, x, y, s: draw_cookie(d, x, y, s, bitten=False),
    "cookie_bitten": lambda d, x, y, s: draw_cookie(d, x, y, s, bitten=True),
    "candy_pink": lambda d, x, y, s: draw_candy(d, x, y, s, color=CANDY_PINK),
    "candy_purple": lambda d, x, y, s: draw_candy(d, x, y, s, color=CANDY_PURPLE),
}


def draw_icon(draw, kind: str, cx: int, cy: int, size: int) -> None:
    """Rysuje ikonę po nazwie. Bezpieczny fallback: koło, gdy nazwa nieznana."""
    fn = _ICONS.get(kind)
    if fn is None:
        r = max(2, size // 2)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=APPLE_RED, outline=OUTLINE, width=1)
        return
    fn(draw, cx, cy, size)


# Tematy → para ikon do dwóch grup (left/right) + operator między nimi.
# Operator przyjmuje wartości: "+", "−", "×", "÷". None oznacza brak operatora (np. mnożenie ma siatkę).
TOPIC_THEMES: Dict[str, dict] = {
    "dodawanie": {"left": "apple_red", "right": "apple_green", "op": "+"},
    "odejmowanie": {"left": "cookie", "right": "cookie_bitten", "op": "−"},
    "mnożenie": {"grid": "star_gold", "op": "×"},
    "dzielenie": {"left": "fish_blue", "right": "fish_orange", "op": "÷"},
    "default": {"left": "apple_red", "right": "apple_green", "op": "+"},
}


def get_theme(topic: str) -> dict:
    """Zwraca motyw ikon dla danego tematu (z fallbackiem na default)."""
    return TOPIC_THEMES.get((topic or "").strip().lower(), TOPIC_THEMES["default"])
