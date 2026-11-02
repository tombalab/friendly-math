"""
Złote karty (Q6): generuje offline wszystkie wzorce z polem `golden`, zapisuje PDF
(i PNG stron) do `data/preview/golden/` i wypisuje wynik automatycznej checklisty.

Resztę checklisty (`docs/quality-checklist.md`) sprawdź na wydruku albo w PNG.

Uruchom z roota repo: `python scripts/render_golden.py`
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("FRIENDLY_MATH_OBSERVABILITY", "0")

from app.review.golden import list_golden_cards, run_golden


def main() -> int:
    import fitz

    out_dir = ROOT / "data" / "preview" / "golden"
    out_dir.mkdir(parents=True, exist_ok=True)
    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        for card in list_golden_cards():
            report = run_golden(card, output_dir=Path(tmp) / "out", history_dir=Path(tmp) / "history")
            pdf = report.result.pdf_bytes
            if pdf:
                (out_dir / f"{card.name}.pdf").write_bytes(pdf)
                doc = fitz.open(stream=pdf, filetype="pdf")
                for i, page in enumerate(doc, start=1):
                    page.get_pixmap(dpi=80).save(str(out_dir / f"{card.name}_p{i}.png"))
                doc.close()
            status = "ok" if not report.issues else "BŁĄD"
            print(f"[{status}] {card.name}: {len(report.student_pages)} str. ucznia — {card.golden['why']}")
            for issue in report.issues:
                print(f"       - {issue}")
            failed += bool(report.issues)
    print(f"\nPDF i PNG: {out_dir.relative_to(ROOT)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
