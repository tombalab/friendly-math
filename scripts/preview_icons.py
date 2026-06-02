"""
Skrypt podglądu ikon — generuje próbki PNG dla każdego tematu i zapisuje do `data/preview/icons/`.
Uruchamiać z roota repo: `python scripts/preview_icons.py`
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.generators.images import (
    generate_worksheet_image,
    generate_worksheet_images_for_tasks,
)


def main() -> None:
    out_dir = ROOT / "data" / "preview" / "icons"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Pojedyncza ilustracja u góry karty (dla profilu standardowy/zdolny/dysleksja)
    single_cases = [
        ("dodawanie", "standardowy"),
        ("odejmowanie", "standardowy"),
        ("mnożenie", "standardowy"),
        ("dzielenie", "standardowy"),
        ("ułamki", "standardowy"),
        ("równania", "standardowy"),  # → pusty bytes (skip)
    ]
    for topic, profile in single_cases:
        png = generate_worksheet_image(topic=topic, profile=profile)
        if not png:
            print(f"[skip] single {topic}/{profile} — brak grafiki (świadome).")
            continue
        path = out_dir / f"single_{topic}_{profile}.png"
        path.write_bytes(png)
        print(f"[ok]   {path.relative_to(ROOT)}")

    # Ilustracje per zadanie - mix bezpiecznych (powinny się narysować) i trudnych
    # (powinny być świadomie pominięte = pusty bytes).
    per_task_cases = [
        ("dodawanie", "dyskalkulia", [
            "Policz: 3 + 4 = ____",         # OK
            "Policz: 5 + 2 = ____",         # OK
            "Policz: 25 + 17 = ____",       # SKIP - poza zakresem
        ]),
        ("odejmowanie", "ADHD", [
            "Policz: 8 - 3 = ____",         # OK
            "Policz: 5 - 2 = ____",         # OK
            "Policz: 45 - 18 = ____",       # SKIP - poza zakresem
        ]),
        ("mnożenie", "trudności w nauce", [
            "Policz: 2 x 3 = ____",         # OK
            "Policz: 4 x 2 = ____",         # OK
            "Policz: 15 x 6 = ____",        # SKIP - 15 > 5
            "Policz: 12 x 4 = ____",        # SKIP - 12 > 5
        ]),
        ("dzielenie", "dyskalkulia", [
            "Policz: 6 : 2 = ____",         # OK - 3 grupy po 2 ryby
            "Policz: 8 : 2 = ____",         # OK - 2 grupy po 4 ryby
            "Policz: 10 : 3 = ____",        # SKIP - 10 % 3 != 0
        ]),
        ("ułamki", "dyskalkulia", [
            "Policz: 1/2 + 1/4 = ____",     # OK
            "Policz: 3/4 - 1/4 = ____",     # OK
            "Policz: 5/12 + 7/12 = ____",   # SKIP - mianownik > 6
        ]),
    ]
    for topic, profile, tasks in per_task_cases:
        pngs = generate_worksheet_images_for_tasks(tasks=tasks, topic=topic, profile=profile)
        for i, png in enumerate(pngs, start=1):
            if not png:
                print(f"[skip] task {topic}/{profile}/{i:02d} ({tasks[i-1]!r}) - poza bezpiecznym zakresem")
                continue
            path = out_dir / f"task_{topic}_{profile}_{i:02d}.png"
            path.write_bytes(png)
            print(f"[ok]   {path.relative_to(ROOT)}")

    print(f"\nOK - probki w: {out_dir.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
