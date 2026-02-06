"""
Day 8: Generator grafiki dla karty pracy.
Jedna ilustracja / PDF, styl low-stimuli, proste kształty (Pillow).
Grafika ma lekki związek z tematem (dodawanie → grupy, mnożenie → siatka, itd.).
"""
from __future__ import annotations

from io import BytesIO
from typing import Tuple

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
