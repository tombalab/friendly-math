"""
Skrypt podglądu ilustracji AI – generuje próbki przez gpt-image-1
i zapisuje do `data/preview/ai_images/`.

UWAGA: każde uruchomienie kosztuje pieniądze (gpt-image-1 quality=low ~$0.011/obraz).
Domyślnie generujemy 6 obrazków (~$0.066, ~25 groszy).

Uruchamiać z roota repo: `python scripts/preview_ai_images.py`
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ai.image_generator import estimate, generate_task_images_ai


def main() -> None:
    out_dir = ROOT / "data" / "preview" / "ai_images"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Zestaw testowy – mix tematów i profili
    test_cases = [
        # (topic, profile, task)
        ("dodawanie", "standardowy", "Policz: 3 + 4 = ____"),
        ("dodawanie", "dyskalkulia", "Policz: 5 + 2 = ____"),
        ("odejmowanie", "ADHD", "Policz: 8 − 3 = ____"),
        ("mnożenie", "standardowy", "Policz: 12 × 4 = ____"),
        ("dzielenie", "dyskalkulia", "Policz: 10 : 2 = ____"),
        ("ułamki", "dysleksja", "Policz: 1/2 + 1/4 = ____"),
        ("równania", "zdolny", "x + 5 = 12"),
    ]

    est = estimate(len(test_cases))
    print(f"Generuje {est.n_images} obrazkow AI:")
    print(f"  Koszt:   ~${est.cost_usd}")
    print(f"  Czas:    ~{est.latency_s_parallel:.0f}s (rownolegle)")
    print(f"  Model:   {est.model} (quality={est.quality})")
    print()

    # Grupujemy po tematach żeby przekazać do generate_task_images_ai jednym wywołaniem
    # (lista zadań tego samego tematu) – ale tu mamy mix, więc po prostu pojedyncze wywołania.
    done = 0
    start = time.time()

    def on_progress(d: int, t: int) -> None:
        nonlocal done
        done = d
        elapsed = time.time() - start
        print(f"  [{d}/{t}] {elapsed:.1f}s")

    # Wywołujemy każdy case osobno (zachowujemy mapowanie na pliki)
    for i, (topic, profile, task) in enumerate(test_cases, start=1):
        case_start = time.time()
        images = generate_task_images_ai(
            tasks=[task],
            topic=topic,
            profile=profile,
            max_workers=1,
        )
        elapsed = time.time() - case_start
        png = images[0] if images else b""
        if not png:
            print(f"[FAIL] {topic}/{profile} -> brak obrazka ({elapsed:.1f}s)")
            continue
        safe_topic = topic.replace(" ", "_")
        safe_profile = profile.replace(" ", "_")
        path = out_dir / f"ai_{i:02d}_{safe_topic}_{safe_profile}.png"
        path.write_bytes(png)
        size_kb = len(png) / 1024
        print(f"[OK]   {path.name} ({size_kb:.1f} kB, {elapsed:.1f}s)")

    total_time = time.time() - start
    print()
    print(f"OK - probki w: {out_dir.relative_to(ROOT)}/")
    print(f"Calkowity czas: {total_time:.1f}s")


if __name__ == "__main__":
    main()
