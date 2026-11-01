"""Wektorowe pomoce dydaktyczne rysowane w PDF (Q5).

Każda funkcja rysuje w prostokącie (x, y_top, width) i zajmuje `visual_height()`.
Rysunek nie podpowiada wyniku tam, gdzie zadanie go sprawdza: oś liczbowa
zaznacza tylko start, przy dzieleniu talerze są puste, zegar „do narysowania”
nie ma wskazówek.
"""
from __future__ import annotations

import math

from reportlab.lib.colors import HexColor

from app.generators.task_visuals import TaskVisual

INK = "#37474f"
FIRST = "#e53935"  # pierwszy składnik
SECOND = "#1e88e5"  # drugi składnik
NEUTRAL = "#78909c"
SHADE = "#ffb74d"
GOLD = "#f2c94c"
SILVER = "#cfd8dc"

_MAX_CELL = 18.0


def visual_height(visual: TaskVisual, width: float) -> float:
    kind = visual.kind
    if kind == "ten_frame":
        return 2 * _ten_frame_cell(visual, width) + 2
    if kind == "number_line":
        return 34
    if kind == "array":
        return visual.a * _array_cell(visual, width)
    if kind == "sharing":
        return _sharing_dot(visual, width) + 8 + 30
    if kind == "fraction":
        return 50
    if kind == "coins":
        return 34
    if kind == "clock":
        return 70
    if kind == "rectangle":
        return 64
    return 0


def draw_task_visual(c, visual: TaskVisual, x: float, y_top: float, width: float, font: str) -> None:
    drawer = {
        "ten_frame": _draw_ten_frame,
        "number_line": _draw_number_line,
        "array": _draw_array,
        "sharing": _draw_sharing,
        "fraction": _draw_fractions,
        "coins": _draw_coins,
        "clock": _draw_clock,
        "rectangle": _draw_rectangle,
    }.get(visual.kind)
    if drawer is None:
        return
    c.saveState()
    try:
        drawer(c, visual, x, y_top, width, font)
    finally:
        c.restoreState()


# --- ramka dziesiątkowa ---------------------------------------------------


def _ten_frame_total(visual: TaskVisual) -> int:
    return visual.a + visual.b if visual.op == "+" else visual.a


def _ten_frame_count(visual: TaskVisual) -> int:
    return 2 if _ten_frame_total(visual) > 10 else 1


def _ten_frame_cell(visual: TaskVisual, width: float) -> float:
    frames = _ten_frame_count(visual)
    gap = 12
    return min(_MAX_CELL, (width - (frames - 1) * gap) / (5 * frames))


def _draw_ten_frame(c, visual: TaskVisual, x: float, y_top: float, width: float, font: str) -> None:
    frames = _ten_frame_count(visual)
    cell = _ten_frame_cell(visual, width)
    gap = 12
    total_w = frames * 5 * cell + (frames - 1) * gap
    x0 = x + (width - total_w) / 2
    r = cell * 0.32
    c.setLineWidth(0.8)
    c.setStrokeColor(HexColor(INK))
    for f in range(frames):
        fx = x0 + f * (5 * cell + gap)
        for row in range(2):
            for col in range(5):
                c.rect(fx + col * cell, y_top - (row + 1) * cell, cell, cell, fill=0, stroke=1)

    total = _ten_frame_total(visual)
    for i in range(total):
        f, pos = divmod(i, 10)
        row, col = divmod(pos, 5)
        cx = x0 + f * (5 * cell + gap) + col * cell + cell / 2
        cy = y_top - row * cell - cell / 2
        if visual.op == "+":
            c.setFillColor(HexColor(FIRST if i < visual.a else SECOND))
            c.circle(cx, cy, r, fill=1, stroke=0)
        else:
            c.setFillColor(HexColor(SECOND))
            c.circle(cx, cy, r, fill=1, stroke=0)
            if i >= visual.a - visual.b:
                # Zabrane kropki są przekreślone.
                c.setStrokeColor(HexColor(INK))
                c.setLineWidth(1.2)
                c.line(cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1)
                c.line(cx - r - 1, cy + r + 1, cx + r + 1, cy - r - 1)


# --- oś liczbowa ----------------------------------------------------------


def _draw_number_line(c, visual: TaskVisual, x: float, y_top: float, width: float, font: str) -> None:
    from app.generators.task_visuals import NUMBER_LINE_MAX

    left = x + 8
    right = x + width - 8
    step = (right - left) / NUMBER_LINE_MAX
    y = y_top - 12
    c.setStrokeColor(HexColor(INK))
    c.setLineWidth(1)
    c.line(left, y, right, y)
    label_every = 1 if step >= 11 else 2 if step >= 6 else 5
    c.setFont(font, 7 if step >= 9 else 6)
    c.setFillColor(HexColor(INK))
    for n in range(NUMBER_LINE_MAX + 1):
        tx = left + n * step
        tall = n % 5 == 0
        c.line(tx, y - (4 if tall else 2.5), tx, y + (4 if tall else 2.5))
        if n % label_every == 0 or n == NUMBER_LINE_MAX:
            c.drawCentredString(tx, y - 13, str(n))
    # Zaznaczony tylko punkt startu — skoki rysuje uczeń.
    c.setFillColor(HexColor(FIRST))
    c.circle(left + visual.a * step, y, 3.2, fill=1, stroke=0)


# --- mnożenie: układ kropek ------------------------------------------------


def _array_cell(visual: TaskVisual, width: float) -> float:
    return min(14.0, width / max(1, visual.b), 64.0 / max(1, visual.a))


def _draw_array(c, visual: TaskVisual, x: float, y_top: float, width: float, font: str) -> None:
    cell = _array_cell(visual, width)
    x0 = x + (width - visual.b * cell) / 2
    c.setFillColor(HexColor(SECOND))
    for row in range(visual.a):
        for col in range(visual.b):
            c.circle(x0 + col * cell + cell / 2, y_top - row * cell - cell / 2, cell * 0.32, fill=1, stroke=0)


# --- dzielenie: kropki i puste talerze --------------------------------------


def _sharing_dot(visual: TaskVisual, width: float) -> float:
    return min(12.0, width / max(1, visual.a))


def _draw_sharing(c, visual: TaskVisual, x: float, y_top: float, width: float, font: str) -> None:
    dot = _sharing_dot(visual, width)
    x0 = x + (width - visual.a * dot) / 2
    c.setFillColor(HexColor(SECOND))
    for i in range(visual.a):
        c.circle(x0 + i * dot + dot / 2, y_top - dot / 2, dot * 0.32, fill=1, stroke=0)
    plate_r = 14
    gap = 10
    plates_w = visual.b * 2 * plate_r + (visual.b - 1) * gap
    px0 = x + (width - plates_w) / 2
    py = y_top - dot - 8 - plate_r
    c.setStrokeColor(HexColor(INK))
    c.setLineWidth(0.8)
    for i in range(visual.b):
        c.circle(px0 + plate_r + i * (2 * plate_r + gap), py, plate_r, fill=0, stroke=1)


# --- ułamki: koło podzielone na części -------------------------------------


def _draw_fractions(c, visual: TaskVisual, x: float, y_top: float, width: float, font: str) -> None:
    fractions = visual.fractions or ()
    if not fractions:
        return
    r = 23
    gap = 22
    total_w = len(fractions) * 2 * r + (len(fractions) - 1) * gap
    x0 = x + (width - total_w) / 2
    for i, (num, den) in enumerate(fractions):
        cx = x0 + r + i * (2 * r + gap)
        cy = y_top - r - 2
        c.setStrokeColor(HexColor(INK))
        c.setLineWidth(0.9)
        for k in range(den):
            start = 90 - (k + 1) * 360 / den
            c.setFillColor(HexColor(SHADE if k < num else "#FFFFFF"))
            c.wedge(cx - r, cy - r, cx + r, cy + r, start, 360 / den, fill=1, stroke=1)


# --- pieniądze: polskie monety ---------------------------------------------


def _coin_radius(value: int) -> float:
    return {5: 15.5, 2: 14.5, 1: 13.5}.get(value, 13.5)


def _draw_coin(c, cx: float, cy: float, value: int, font: str) -> None:
    r = _coin_radius(value)
    # 5 zł: złoty środek, srebrny pierścień; 2 zł: odwrotnie; 1 zł: srebrna.
    outer, inner = {5: (SILVER, GOLD), 2: (GOLD, SILVER)}.get(value, (SILVER, SILVER))
    c.setStrokeColor(HexColor(INK))
    c.setLineWidth(0.7)
    c.setFillColor(HexColor(outer))
    c.circle(cx, cy, r, fill=1, stroke=1)
    c.setFillColor(HexColor(inner))
    c.circle(cx, cy, r * 0.72, fill=1, stroke=0)
    c.setFillColor(HexColor(INK))
    c.setFont(font, 8)
    c.drawCentredString(cx, cy - 2.8, f"{value} zł")


def _draw_coins(c, visual: TaskVisual, x: float, y_top: float, width: float, font: str) -> None:
    groups = [g for g in visual.coin_groups if g]
    if not groups:
        return
    coin_gap = 3
    op_w = 18
    widths = [sum(2 * _coin_radius(v) for v in g) + coin_gap * (len(g) - 1) for g in groups]
    total_w = sum(widths) + op_w * (len(groups) - 1)
    cursor = x + max(0.0, (width - total_w) / 2)
    cy = y_top - 17
    for gi, group in enumerate(groups):
        if gi:
            c.setFillColor(HexColor(INK))
            c.setFont(font, 12)
            c.drawCentredString(cursor + op_w / 2, cy - 4, "+")
            cursor += op_w
        for value in group:
            r = _coin_radius(value)
            _draw_coin(c, cursor + r, cy, value, font)
            cursor += 2 * r + coin_gap
        cursor -= coin_gap


# --- czas: tarcza zegara ----------------------------------------------------


def _draw_clock(c, visual: TaskVisual, x: float, y_top: float, width: float, font: str) -> None:
    r = 33
    cx = x + width / 2
    cy = y_top - r - 2
    c.setStrokeColor(HexColor(INK))
    c.setFillColor(HexColor("#FFFFFF"))
    c.setLineWidth(1.2)
    c.circle(cx, cy, r, fill=1, stroke=1)
    c.setFillColor(HexColor(INK))
    c.setFont(font, 7.5)
    for n in range(1, 13):
        ang = math.radians(90 - n * 30)
        c.drawCentredString(cx + math.cos(ang) * (r - 8), cy + math.sin(ang) * (r - 8) - 2.6, str(n))
    for m in range(60):
        ang = math.radians(90 - m * 6)
        inner = r - (3 if m % 5 == 0 else 1.5)
        c.setLineWidth(0.8 if m % 5 == 0 else 0.4)
        c.line(cx + math.cos(ang) * inner, cy + math.sin(ang) * inner, cx + math.cos(ang) * r, cy + math.sin(ang) * r)
    if visual.show_hands:
        hour_ang = math.radians(90 - visual.hour * 30)
        c.setLineWidth(2.4)
        c.line(cx, cy, cx + math.cos(hour_ang) * r * 0.4, cy + math.sin(hour_ang) * r * 0.4)
        c.setLineWidth(1.4)
        # Minutowa kończy się przed cyframi, żeby nie zasłaniać „12”.
        c.line(cx, cy, cx, cy + r * 0.55)
    c.circle(cx, cy, 1.8, fill=1, stroke=0)


# --- obwody: prostokąt z wymiarami -------------------------------------------


def _draw_rectangle(c, visual: TaskVisual, x: float, y_top: float, width: float, font: str) -> None:
    w_units, h_units = max(1, visual.a), max(1, visual.b)
    max_w, max_h = min(width - 50, 150.0), 44.0
    scale = min(max_w / w_units, max_h / h_units)
    rw, rh = w_units * scale, h_units * scale
    rx = x + (width - rw) / 2 - 10
    ry = y_top - 4 - rh
    c.setStrokeColor(HexColor(INK))
    c.setFillColor(HexColor("#eef4f8"))
    c.setLineWidth(1.2)
    c.rect(rx, ry, rw, rh, fill=1, stroke=1)
    c.setFillColor(HexColor(INK))
    c.setFont(font, 8)
    c.drawCentredString(rx + rw / 2, ry - 11, f"{visual.a} cm")
    c.drawString(rx + rw + 5, ry + rh / 2 - 3, f"{visual.b} cm")
