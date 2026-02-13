"""
Day 8: Generator grafiki dla karty pracy.
Day 11: Ilustracja per zadanie (związek z treścią zadania), opcja dla profili.
"""
from __future__ import annotations

import re
from io import BytesIO
from typing import List, Tuple

from PIL import Image, ImageDraw  # pyright: ignore[reportMissingModuleSource]


# Kolory pastelowe, low-stimuli (spokojne, niski kontrast)
_PASTEL_BG = "#f5f8f5"
_PASTEL_SHAPES = ("#c8e6c9", "#b3e5fc", "#fff9c4", "#ffccbc", "#d1c4e9")


def generate_worksheet_image(
    topic: str,
    profile: str,
    size: Tuple[int, int] = (280, 160),
) -> bytes:
    """
    Generuje jedną ilustrację w stylu low-stimuli, z lekkim związkiem z tematem:
    - dodawanie: dwie grupy kół (np. 3 + 2)
    - odejmowanie: grupa kół, część „zabrana” (jaśniejsza)
    - mnożenie: prostokątna siatka kropek (np. 2×3)
    - dzielenie: jedna grupa podzielona na równe części
    - ułamki: koło lub prostokąt przecięty linią (połowa / ćwiartka)
    - równania: dwie równe grupy (lewa = prawa)
    """
    w, h = size
    img = Image.new("RGB", (w, h), _PASTEL_BG)
    draw = ImageDraw.Draw(img)
    colors = list(_PASTEL_SHAPES)
    margin = 20
    ss = min(28, (w - 2 * margin) // 5, (h - 2 * margin) // 4)  # rozmiar pojedynczego elementu
    if profile in ["dyskalkulia", "ADHD", "trudności w nauce"]:
        ss = min(ss + 4, 36)  # trochę większe dla czytelności

    topic_lower = (topic or "").strip().lower()

    if topic_lower == "dodawanie":
        # Dwie grupy: np. 3 + 2 kółka (wizualnie „3 + 2”)
        gap = 24
        cx1, cy = margin + 40, h // 2
        for i in range(3):
            x = cx1 + i * (ss + 6) - (3 * (ss + 6)) // 2
            draw.ellipse([x, cy - ss // 2, x + ss, cy + ss // 2], fill=colors[0], outline="#9e9e9e", width=1)
        cx2 = w - margin - 40
        for i in range(2):
            x = cx2 + i * (ss + 6) - (2 * (ss + 6)) // 2
            draw.ellipse([x, cy - ss // 2, x + ss, cy + ss // 2], fill=colors[1], outline="#9e9e9e", width=1)
    elif topic_lower == "odejmowanie":
        # Grupa 5 kół, 2 „zabrane” (wypełnione tłem / bardzo jasne)
        n_total, n_gone = 5, 2
        cx, cy = w // 2, h // 2
        start_x = cx - (n_total * (ss + 6)) // 2 + (ss + 6) // 2
        for i in range(n_total):
            x = start_x + i * (ss + 6)
            if i < n_total - n_gone:
                draw.ellipse([x, cy - ss // 2, x + ss, cy + ss // 2], fill=colors[0], outline="#9e9e9e", width=1)
            else:
                draw.ellipse([x, cy - ss // 2, x + ss, cy + ss // 2], fill=_PASTEL_BG, outline="#bdbdbd", width=1)
    elif topic_lower == "mnożenie":
        # Siatka 2×3 (proste „mnożenie”)
        rows, cols = 2, 3
        total_w = cols * ss + (cols - 1) * 6
        total_h = rows * ss + (rows - 1) * 6
        ox = (w - total_w) // 2
        oy = (h - total_h) // 2
        for r in range(rows):
            for c in range(cols):
                x = ox + c * (ss + 6)
                y = oy + r * (ss + 6)
                draw.ellipse([x, y, x + ss, y + ss], fill=colors[(r + c) % len(colors)], outline="#9e9e9e", width=1)
    elif topic_lower == "dzielenie":
        # 6 kół w dwóch rzędach („6 : 2 = 3”)
        n = 6
        cx, cy = w // 2, h // 2
        start_x = cx - (3 * (ss + 6)) // 2 + (ss + 6) // 2
        for i in range(3):
            x = start_x + i * (ss + 6)
            draw.ellipse([x, cy - ss // 2 - (ss + 6), x + ss, cy + ss // 2 - (ss + 6)], fill=colors[0], outline="#9e9e9e", width=1)
        for i in range(3):
            x = start_x + i * (ss + 6)
            draw.ellipse([x, cy - ss // 2 + (ss + 6), x + ss, cy + ss // 2 + (ss + 6)], fill=colors[1], outline="#9e9e9e", width=1)
    elif topic_lower == "ułamki":
        # Koło przecięte na pół (1/2)
        cx, cy = w // 2, h // 2
        r = min(45, w // 4, h // 4)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline="#9e9e9e", width=2, fill=colors[0])
        draw.line([cx - r, cy, cx + r, cy], fill="#9e9e9e", width=2)
    elif topic_lower == "równania":
        # Dwie równe grupy (lewa = prawa), po 2 kółka
        cy = h // 2
        left_cx, right_cx = w // 4, 3 * w // 4
        for dx, mult in [(-1, left_cx), (1, right_cx)]:
            for i in range(2):
                x = mult + (i - 0.5) * (ss + 8)
                draw.ellipse([x, cy - ss // 2, x + ss, cy + ss // 2], fill=colors[i % len(colors)], outline="#9e9e9e", width=1)
    else:
        # Domyślnie: proste grupy kół i kwadratów (jak wcześniej)
        n_shapes = min(5, 3 + hash(topic or "x") % 3)
        if profile in ["dyskalkulia", "ADHD", "trudności w nauce"]:
            n_shapes = min(n_shapes, 4)
        for i in range(n_shapes):
            c = colors[i % len(colors)]
            x = margin + (i * (w - 2 * margin - ss) // max(1, n_shapes - 1))
            y = h // 2 - ss // 2 + (i % 3 - 1) * (ss // 2)
            y = max(margin, min(h - margin - ss, y))
            if i % 2 == 0:
                draw.ellipse([x, y, x + ss, y + ss], fill=c, outline="#9e9e9e", width=1)
            else:
                draw.rectangle([x, y, x + ss, y + ss], fill=c, outline="#9e9e9e", width=1)

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _parse_numbers_from_task(task: str) -> List[int]:
    """Wyciąga liczby z treści zadania (np. 'Policz: 3 + 4 = ____' -> [3, 4])."""
    numbers = re.findall(r"\d+", task)
    return [min(int(n), 12) for n in numbers[:4]]  # max 4 liczby, każda do 12 (czytelność)


def _parse_fraction_from_task(task: str) -> Tuple[int, int] | None:
    """Wyciąga pierwszy ułamek z treści (np. 'Zaznacz 1/2 koła' -> (1, 2), '3/4' -> (3, 4))."""
    m = re.search(r"(\d+)\s*/\s*(\d+)", task)
    if not m:
        return None
    num, den = int(m.group(1)), int(m.group(2))
    if den <= 0 or num < 0 or num > den:
        return None
    # ograniczenie czytelności: mianownik do 8
    den = min(den, 8)
    num = min(num, den)
    return (num, den)


def _circle_size_to_fit(available_w: int, available_h: int, num_cols: int, num_rows: int, gap: int = 6) -> int:
    """Oblicza rozmiar kółka ss tak, aby num_cols×num_rows mieściło się w available_w × available_h."""
    if num_cols <= 0 or num_rows <= 0:
        return min(available_w, available_h) // 2
    ss_w = (available_w - (num_cols - 1) * gap) // num_cols
    ss_h = (available_h - (num_rows - 1) * gap) // num_rows
    ss = max(6, min(ss_w, ss_h, 40))  # min 6px, max 40 (czytelność)
    return ss


def generate_worksheet_images_for_tasks(
    tasks: List[str],
    topic: str,
    profile: str,
    size: Tuple[int, int] = (480, 100),
) -> List[bytes]:
    """
    Day 11: Jedna ilustracja na zadanie, powiązana z treścią i tematem.
    Rozmiar kółek (ss) dostosowany do liczby elementów i miejsca – nic nie ucinane.
    """
    result: List[bytes] = []
    colors = list(_PASTEL_SHAPES)
    topic_lower = (topic or "").strip().lower()
    w, h = size
    margin = 24
    pad = 10  # wewnętrzny padding – żeby skrajne kółka nie były ucinane
    gap = 6
    aw = w - 2 * margin - 2 * pad
    ah = h - 2 * margin - 2 * pad
    max_circles = 12

    for task in tasks:
        nums = _parse_numbers_from_task(task)
        img = Image.new("RGB", (w, h), _PASTEL_BG)
        draw = ImageDraw.Draw(img)
        # Początek obszaru rysowania (z paddingiem)
        bx, by = margin + pad, margin + pad

        if not nums:
            ss = min(aw, ah) // 4
            cx, cy = w // 2, h // 2
            draw.ellipse([cx - ss, cy - ss, cx + ss, cy + ss], fill=colors[0], outline="#9e9e9e", width=1)
        elif topic_lower == "mnożenie" and len(nums) >= 2:
            # a × b = siatka a wierszy, b kolumn (zgodnie z treścią zadania)
            rows, cols = min(nums[0], 6), min(nums[1], 8)
            ss = _circle_size_to_fit(aw, ah, cols, rows, gap)
            total_w = cols * (ss + gap) - gap
            total_h = rows * (ss + gap) - gap
            ox = bx + (aw - total_w) // 2
            oy = by + (ah - total_h) // 2
            for r in range(rows):
                for c in range(cols):
                    x = ox + c * (ss + gap)
                    y = oy + r * (ss + gap)
                    draw.ellipse([x, y, x + ss, y + ss], fill=colors[(r + c) % len(colors)], outline="#9e9e9e", width=1)
        elif topic_lower == "odejmowanie" and len(nums) >= 1:
            # np. 7 − 2: 7 kółek, ostatnie 2 przekreślone („zabrane”)
            n_total = min(nums[0], max_circles)
            n_gone = min(nums[1], n_total - 1) if len(nums) >= 2 else 2
            n_visible = n_total - n_gone
            ss = _circle_size_to_fit(aw, ah, n_total, 1, gap)
            total_w = n_total * (ss + gap) - gap
            start_x = bx + (aw - total_w) // 2
            cy = by + ah // 2
            for i in range(n_total):
                x = start_x + i * (ss + gap)
                draw.ellipse([x, cy - ss // 2, x + ss, cy + ss // 2], fill=colors[0], outline="#9e9e9e", width=1)
                if i >= n_visible:
                    # Przekreślenie – „zabrane” (X przez kółko)
                    draw.line([x, cy - ss // 2, x + ss, cy + ss // 2], fill="#e57373", width=2)
                    draw.line([x + ss, cy - ss // 2, x, cy + ss // 2], fill="#e57373", width=2)
        elif topic_lower == "dzielenie" and len(nums) >= 2:
            # np. 6 : 2 = 3 → dwie grupy po 3 (obok siebie, jak „6 podzielone na 2”)
            n_total = min(nums[0], 12)
            n_groups = max(1, min(nums[1], 4))
            per_group = n_total // n_groups  # w każdej grupie tyle samo
            if per_group == 0:
                per_group = 1
            n1, n2 = per_group, per_group
            group_gap = 24
            ss = _circle_size_to_fit(aw // 2 - group_gap // 2, ah, n1, 1, gap)
            ss = min(ss, _circle_size_to_fit(aw // 2 - group_gap // 2, ah, n2, 1, gap))
            cy = by + ah // 2
            total1 = n1 * (ss + gap) - gap
            start1 = bx + (aw // 2 - group_gap // 2 - total1) // 2
            for i in range(n1):
                x = start1 + i * (ss + gap)
                draw.ellipse([x, cy - ss // 2, x + ss, cy + ss // 2], fill=colors[0], outline="#9e9e9e", width=1)
            total2 = n2 * (ss + gap) - gap
            start2 = bx + aw // 2 + group_gap // 2 + (aw - aw // 2 - group_gap // 2 - total2) // 2
            for i in range(n2):
                x = start2 + i * (ss + gap)
                draw.ellipse([x, cy - ss // 2, x + ss, cy + ss // 2], fill=colors[1], outline="#9e9e9e", width=1)
        elif topic_lower == "ułamki":
            # Ilustracja zgodna z treścią: koło podzielone na mianownik części, licznik części zaznaczonych
            frac = _parse_fraction_from_task(task)
            if frac:
                num, den = frac
                r = min(40, aw // 2, ah // 2 - 4)
                cx, cy = bx + aw // 2, by + ah // 2
                # Pełne koło (obrys)
                bbox = [cx - r, cy - r, cx + r, cy + r]
                # Podział na den „kawałków” (początek od góry: -90°), każdy kawałek 360/den stopni
                step = 360.0 / den
                for i in range(den):
                    start_angle = -90 + i * step  # -90 żeby pierwszy kawałek od góry
                    end_angle = start_angle + step
                    fill_color = colors[0] if i < num else _PASTEL_BG
                    outline_color = "#9e9e9e"
                    draw.pieslice(bbox, start=start_angle, end=end_angle, fill=fill_color, outline=outline_color, width=2)
            else:
                # Fallback: 1/2 – pół koła
                r = min(40, aw // 2, ah // 2 - 4)
                cx, cy = bx + aw // 2, by + ah // 2
                bbox = [cx - r, cy - r, cx + r, cy + r]
                draw.pieslice(bbox, start=-90, end=90, fill=colors[0], outline="#9e9e9e", width=2)
                draw.pieslice(bbox, start=90, end=270, fill=_PASTEL_BG, outline="#9e9e9e", width=2)
        elif topic_lower == "równania" and len(nums) >= 2:
            n1, n2 = min(nums[0], 6), min(nums[1], 6)
            half_aw = aw // 2
            group_gap = 16
            ss1 = _circle_size_to_fit(half_aw - group_gap, ah, n1, 1, gap)
            ss2 = _circle_size_to_fit(half_aw - group_gap, ah, n2, 1, gap)
            ss = min(ss1, ss2)
            cy = by + ah // 2
            total1 = n1 * (ss + gap) - gap
            start1 = bx + (half_aw - group_gap - total1) // 2
            for i in range(n1):
                x = start1 + i * (ss + gap)
                draw.ellipse([x, cy - ss // 2, x + ss, cy + ss // 2], fill=colors[0], outline="#9e9e9e", width=1)
            total2 = n2 * (ss + gap) - gap
            right_half_w = aw - half_aw - group_gap
            start2 = bx + half_aw + group_gap + max(0, (right_half_w - total2) // 2)
            for i in range(n2):
                x = start2 + i * (ss + gap)
                draw.ellipse([x, cy - ss // 2, x + ss, cy + ss // 2], fill=colors[1], outline="#9e9e9e", width=1)
        else:
            # Dodawanie (lub domyślnie): dwie grupy kół (np. 3 + 4)
            if len(nums) == 1:
                n1, n2 = min(nums[0], max_circles), 0
            else:
                n1, n2 = min(nums[0], max_circles), min(nums[1], max_circles)
            n_total = n1 + n2
            if n_total == 0:
                ss = min(aw, ah) // 4
                cx, cy = w // 2, h // 2
                draw.ellipse([cx - ss, cy - ss, cx + ss, cy + ss], fill=colors[0], outline="#9e9e9e", width=1)
            else:
                group_gap = 24
                half_aw = aw // 2
                ss1 = _circle_size_to_fit(half_aw - group_gap // 2, ah, n1, 1, gap)
                ss2 = _circle_size_to_fit(half_aw - group_gap // 2, ah, n2, 1, gap)
                ss = max(6, min(ss1, ss2, ah, 40))
                cy = by + ah // 2
                if n1:
                    total1 = n1 * (ss + gap) - gap
                    start1 = bx + (half_aw - group_gap // 2 - total1) // 2
                    for i in range(n1):
                        x = start1 + i * (ss + gap)
                        draw.ellipse([x, cy - ss // 2, x + ss, cy + ss // 2], fill=colors[0], outline="#9e9e9e", width=1)
                if n2:
                    total2 = n2 * (ss + gap) - gap
                    start2 = bx + half_aw + group_gap // 2 + (aw - half_aw - group_gap // 2 - total2) // 2
                    for i in range(n2):
                        x = start2 + i * (ss + gap)
                        draw.ellipse([x, cy - ss // 2, x + ss, cy + ss // 2], fill=colors[1], outline="#9e9e9e", width=1)

        buf = BytesIO()
        img.save(buf, format="PNG")
        result.append(buf.getvalue())

    return result
