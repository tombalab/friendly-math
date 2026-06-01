"""
Generator ilustracji per zadanie przy użyciu OpenAI `gpt-image-1`.

UWAGA – v1.x eksperymentalne. Po sprawdzeniu jakości/kosztów decydujemy,
czy zostaje, czy wracamy do Pillow primitives (`app/generators/images.py`).

Koszty (stan na 2026, ceny mogą się zmienić):
- gpt-image-1 quality="low",  1024x1024  ~ $0.011 / obraz
- gpt-image-1 quality="medium",1024x1024 ~ $0.042 / obraz
- gpt-image-1 quality="high", 1024x1024  ~ $0.167 / obraz

Dla naszego use case (mała ikonka 480×100 pt w PDF) wystarcza `low`.
Pobrany obraz 1024×1024 jest skalowany do 480×~100 px PNG, żeby PDF był lekki.

Sygnatura `generate_task_images_ai(tasks, topic, profile) -> List[bytes]`
celowo dopasowana do `generate_worksheet_images_for_tasks` z `app/generators/images.py`,
żeby UI mogło je zamieniać 1:1.
"""
from __future__ import annotations

import base64
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from io import BytesIO
from typing import Iterable, List, Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image  # pyright: ignore[reportMissingModuleSource]

load_dotenv()


# Domyślny model i parametry – małe, tanie, wystarczające do ikonek w PDF.
_DEFAULT_MODEL = "gpt-image-1"
_DEFAULT_SIZE = "1024x1024"  # gpt-image-1 obsługuje 1024x1024 / 1024x1536 / 1536x1024
_DEFAULT_QUALITY = "low"

# Szacunkowy koszt USD per obraz (do estymaty w UI – przybliżenie).
_COST_PER_IMAGE_USD = {
    ("gpt-image-1", "low"): 0.011,
    ("gpt-image-1", "medium"): 0.042,
    ("gpt-image-1", "high"): 0.167,
}

# Średnia latencja per obraz (sekundy) – obserwowana, do estymaty.
_LATENCY_PER_IMAGE_S = {
    ("gpt-image-1", "low"): 8.0,
    ("gpt-image-1", "medium"): 12.0,
    ("gpt-image-1", "high"): 25.0,
}

# Docelowy rozmiar obrazka w PDF (px). Aspect ratio 480/100 = 4.8 musi pasować
# do `_TASK_IMAGE_ASPECT` w pdf/generator.py (inaczej PDF spłaszczy/rozciągnie).
# Skalujemy w dół przed zapisem, żeby nie ciągnąć 1024×1024 PNG-ów po 200kB.
_TARGET_W_PX = 480
_TARGET_H_PX = 100

# Cache w pamięci procesu – te same zadania (np. przy regeneracji karty)
# nie kosztują dwa razy. Wystarczy proste dict, niewielki rozmiar.
_CACHE_LOCK = threading.Lock()
_CACHE: dict[str, bytes] = {}
_CACHE_MAX = 256

_client: Optional[OpenAI] = None


# --------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------


@dataclass(frozen=True)
class AiImageEstimate:
    """Estymata kosztu/czasu dla wygenerowania N obrazków."""
    n_images: int
    model: str
    quality: str
    cost_usd: float
    latency_s_sequential: float
    latency_s_parallel: float


def estimate(
    n_images: int,
    *,
    model: str = _DEFAULT_MODEL,
    quality: str = _DEFAULT_QUALITY,
    max_workers: int = 4,
) -> AiImageEstimate:
    """Zwraca szacunek kosztu i czasu (przed wywołaniem API)."""
    n = max(0, int(n_images))
    cost = _COST_PER_IMAGE_USD.get((model, quality), 0.05) * n
    lat = _LATENCY_PER_IMAGE_S.get((model, quality), 10.0)
    seq = lat * n
    par = lat * max(1, (n + max_workers - 1) // max_workers)
    return AiImageEstimate(
        n_images=n,
        model=model,
        quality=quality,
        cost_usd=round(cost, 3),
        latency_s_sequential=round(seq, 1),
        latency_s_parallel=round(par, 1),
    )


def generate_task_images_ai(
    tasks: Iterable[str],
    topic: str,
    profile: str,
    *,
    model: str = _DEFAULT_MODEL,
    quality: str = _DEFAULT_QUALITY,
    size: str = _DEFAULT_SIZE,
    max_workers: int = 4,
    progress_cb=None,
) -> List[bytes]:
    """
    Generuje listę ilustracji (PNG bytes) – jedna na zadanie, równolegle.

    progress_cb: opcjonalna funkcja `(done, total) -> None` wywoływana w trakcie generowania
    (np. do `st.progress` w Streamlit).
    """
    task_list = list(tasks)
    n = len(task_list)
    if n == 0:
        return []

    results: List[Optional[bytes]] = [None] * n
    done = 0

    def _worker(idx: int, task: str) -> Tuple[int, bytes]:
        png = _generate_one(task=task, topic=topic, profile=profile,
                            model=model, quality=quality, size=size)
        return idx, png

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(_worker, i, t) for i, t in enumerate(task_list)]
        for fut in as_completed(futures):
            idx, png = fut.result()
            results[idx] = png
            done += 1
            if progress_cb:
                try:
                    progress_cb(done, n)
                except Exception:
                    pass

    # results[i] może być b"" przy błędzie – pozwalamy by PDF generator pominął
    return [r if r is not None else b"" for r in results]


# --------------------------------------------------------------------
# Internals
# --------------------------------------------------------------------


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY nie znaleziony w .env. "
                "Dodaj klucz API żeby używać ilustracji AI."
            )
        _client = OpenAI(api_key=api_key)
    return _client


def _cache_get(key: str) -> Optional[bytes]:
    with _CACHE_LOCK:
        return _CACHE.get(key)


def _cache_set(key: str, value: bytes) -> None:
    with _CACHE_LOCK:
        if len(_CACHE) >= _CACHE_MAX:
            # prosty FIFO trim
            for old_key in list(_CACHE.keys())[: _CACHE_MAX // 4]:
                _CACHE.pop(old_key, None)
        _CACHE[key] = value


def _generate_one(
    task: str,
    topic: str,
    profile: str,
    *,
    model: str,
    quality: str,
    size: str,
) -> bytes:
    """Generuje JEDEN obrazek (z cache + obsługą błędów). Zwraca b"" jeśli się nie udało."""
    cache_key = f"{model}|{quality}|{size}|{topic}|{profile}|{task.strip()}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        client = _get_client()
        prompt = _build_prompt(task=task, topic=topic, profile=profile)

        # gpt-image-1 zwraca b64_json domyślnie (nie URL).
        response = client.images.generate(
            model=model,
            prompt=prompt,
            n=1,
            size=size,
            quality=quality,
        )
        b64 = response.data[0].b64_json
        if not b64:
            return b""
        raw_png = base64.b64decode(b64)
        # Skalujemy w dół – PDF nie potrzebuje 1024x1024.
        small_png = _resize_for_pdf(raw_png)
        _cache_set(cache_key, small_png)
        return small_png
    except Exception as e:  # noqa: BLE001 – świadomie szeroki: AI ma padać miękko
        print(f"⚠️ AI image error for task '{task[:40]}...': {e}")
        return b""


def _resize_for_pdf(raw_png: bytes) -> bytes:
    """Skaluje obraz do _TARGET_W_PX × _TARGET_H_PX (z zachowaniem aspect ratio, padding przezroczysty)."""
    try:
        img = Image.open(BytesIO(raw_png)).convert("RGB")
        # Skalujemy do szerokości docelowej, wysokość proporcjonalna.
        ratio = _TARGET_W_PX / img.width
        new_h = max(1, int(img.height * ratio))
        img = img.resize((_TARGET_W_PX, new_h), Image.LANCZOS)
        # Jeśli wynik jest wyższy niż _TARGET_H_PX, przycinamy do _TARGET_H_PX (środek).
        if img.height > _TARGET_H_PX:
            top = (img.height - _TARGET_H_PX) // 2
            img = img.crop((0, top, _TARGET_W_PX, top + _TARGET_H_PX))
        buf = BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
    except Exception:
        # W razie problemu z resize – zwracamy oryginał (PDF i tak go przeskaluje).
        return raw_png


def _build_prompt(task: str, topic: str, profile: str) -> str:
    """
    Buduje prompt dla `gpt-image-1`. Konwencja:
    - jeden obrazek = ilustracja konkretnego działania z zadania
    - styl: minimalistyczny, dziecięcy, pastelowy, na białym tle, BEZ liczb i tekstu na obrazku
    - format poziomy (banner) – pasuje do paska nad zadaniem w PDF
    """
    topic_lower = (topic or "").strip().lower()

    # Styl bazowy – jednolity dla całej karty, żeby ilustracje wyglądały spójnie.
    style = (
        "Minimalist children's math illustration. "
        "Flat vector style. Soft pastel colors on a clean white background. "
        "No text, no numbers, no symbols. No watermarks. "
        "Horizontal banner composition with generous white margins. "
        "Friendly, gentle, low-stimuli style (no clutter, no busy patterns)."
    )

    # Profilowe wskazówki – low-stimuli = jeszcze prościej, mniej elementów.
    profile_low_stimuli = profile in {"dyskalkulia", "ADHD", "trudności w nauce"}
    profile_hint = (
        "Use only 2-3 colors total. Use very simple shapes. Maximum 8 objects in the image."
        if profile_low_stimuli
        else "Use 3-4 colors total. Keep composition uncluttered."
    )

    # Treść – mapowanie tematu i liczb z zadania na opis sceny.
    scene = _scene_description_from_task(task, topic_lower)

    return f"{style} {profile_hint} Scene: {scene}"


def _scene_description_from_task(task: str, topic_lower: str) -> str:
    """Zamienia treść zadania na konkretny opis sceny dla AI."""
    import re

    # Wyciągamy liczby (bez ułamków) i ułamki osobno
    fraction_match = re.findall(r"(\d+)\s*/\s*(\d+)", task)
    cleaned = re.sub(r"\d+\s*/\s*\d+", " ", task)
    int_numbers = [int(n) for n in re.findall(r"\d+", cleaned)]

    if topic_lower == "dodawanie" and len(int_numbers) >= 2:
        a, b = int_numbers[0], int_numbers[1]
        return (
            f"On the left side, {a} red apples arranged in a neat row. "
            f"On the right side, {b} green apples arranged in a neat row. "
            f"A clear plus sign symbol (+) shape between the two groups, "
            f"suggesting addition. No equals sign, no numbers anywhere."
        )

    if topic_lower == "odejmowanie" and len(int_numbers) >= 2:
        a, b = int_numbers[0], int_numbers[1]
        remaining = max(0, a - b)
        return (
            f"A row of {a} cookies on a plate, where {b} of them have a clear bite "
            f"taken out of them (showing they are being eaten). The remaining {remaining} "
            f"cookies are whole and intact. The scene illustrates subtraction by eating."
        )

    if topic_lower == "mnożenie" and len(int_numbers) >= 2:
        rows, cols = int_numbers[0], int_numbers[1]
        # Limit – AI sobie nie poradzi z 50 obiektami w czytelnej siatce
        rows_show = min(rows, 6)
        cols_show = min(cols, 6)
        return (
            f"A neat rectangular grid of {rows_show} rows and {cols_show} columns of "
            f"identical yellow stars. The stars are evenly spaced and aligned. "
            f"The grid illustrates multiplication as repeated rows."
        )

    if topic_lower == "dzielenie" and len(int_numbers) >= 2:
        total, groups = int_numbers[0], int_numbers[1]
        groups_show = max(2, min(groups, 4))
        per_group = max(1, total // groups_show)
        return (
            f"{groups_show} small bowls arranged in a row. Each bowl contains exactly "
            f"{per_group} identical orange fish. The fish are equally distributed. "
            f"The scene illustrates division as fair sharing into equal groups."
        )

    if topic_lower == "ułamki" and fraction_match:
        num, den = int(fraction_match[0][0]), int(fraction_match[0][1])
        return (
            f"A round pizza viewed from above, cleanly cut into {den} equal slices. "
            f"Exactly {num} of the slices have red tomato sauce topping, while the "
            f"remaining {den - num} slices show plain dough. Clear black lines between "
            f"slices. The scene illustrates the fraction {num}/{den}."
        )

    if topic_lower == "równania":
        return (
            "An old-fashioned balance scale with two pans, perfectly level (balanced). "
            "A small wooden block on the left pan, a small wooden block on the right pan. "
            "The scene illustrates the concept of equation: both sides are equal."
        )

    # Domyślnie – generic illustration tematu
    return f"A simple, friendly illustration related to elementary school math topic: {topic_lower}."
