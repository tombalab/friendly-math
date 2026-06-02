"""
Skrypt podglądu PDF — generuje 3 przykładowe karty (klasa 1/2/3, różne tematy)
zapisuje do `data/preview/pdfs/`. Działa OFFLINE (bez wywołania API), używa
hardcoded zadań reprezentatywnych dla blueprintów.

Uruchom z roota repo: `python scripts/preview_pdfs.py`
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.generators.answers import compute_answer_key
from app.pdf.generator import WorksheetMeta, build_worksheet_pdf_bytes


def make(meta: WorksheetMeta, tasks: list[str], filename: str) -> None:
    out_dir = ROOT / "data" / "preview" / "pdfs"
    out_dir.mkdir(parents=True, exist_ok=True)
    answer_key = compute_answer_key(tasks, topic_label=meta.topic_range)
    print(f"    {answer_key.summary_pl()}")
    pdf_result = build_worksheet_pdf_bytes(
        meta=meta,
        tasks=tasks,
        answer_key=answer_key,
        include_workspace=True,
    )
    for w in pdf_result.warnings:
        print(f"[warn] {filename}: {w.message}")
    path = out_dir / filename
    path.write_bytes(pdf_result.pdf_bytes)
    size_kb = len(pdf_result.pdf_bytes) // 1024
    print(f"[ok] {path.relative_to(ROOT)} ({size_kb} KB, {len(tasks)} zadan)")


def main() -> None:
    # 1) Klasa 1, dodawanie do 20, standardowy
    make(
        WorksheetMeta(
            title="Karta pracy - klasa 1",
            grade="1",
            topic_range="dodawanie do 20",
            student_profile="standardowy",
        ),
        tasks=[
            "Policz: 3 + 4 = ____",
            "Policz: 8 + 2 = ____",
            "Policz: 10 + 5 = ____",
            "Policz: 6 + 7 = ____",
            "Policz: 9 + 4 = ____",
        ],
        filename="kl1_dodawanie_do_20.pdf",
    )

    # 2) Klasa 2, mix typow (porownywanie + okienka + liczenie po), standardowy
    make(
        WorksheetMeta(
            title="Karta pracy - klasa 2",
            grade="2",
            topic_range="liczby i porownywanie",
            student_profile="standardowy",
        ),
        tasks=[
            "Wstaw znak < , > lub =: 45 __ 54",
            "Wstaw znak < , > lub =: 80 __ 80",
            "Uzupelnij: 10, 20, 30, __, __",
            "Uzupelnij okienko: 35 + ☐ = 50",
            "Uzupelnij okienko: 4 × ☐ = 20",
            "Policz: 7 × 5 = ____",
        ],
        filename="kl2_liczby_i_porownywanie.pdf",
    )

    # 3) Klasa 3, ulamki + zadania tekstowe, standardowy
    make(
        WorksheetMeta(
            title="Karta pracy - klasa 3",
            grade="3",
            topic_range="ulamki i zadania tekstowe",
            student_profile="standardowy",
        ),
        tasks=[
            "Policz: 1/4 + 2/4 = ____",
            "Policz: 5/6 − 2/6 = ____",
            "Ile to jest polowa z 20? ____",
            "Ile to jest cwierc z 8? ____",
            "Ania miala 5 jablek. Kupila 4 jablka. Ile ma jablek? Odpowiedz: ____",
            "W koszyku bylo 12 kasztanow. 5 zabrano. Ile zostalo? Odpowiedz: ____",
        ],
        filename="kl3_ulamki_zadania_tekstowe.pdf",
    )

    print(f"\nOK - karty PDF w: data/preview/pdfs/")


if __name__ == "__main__":
    main()
