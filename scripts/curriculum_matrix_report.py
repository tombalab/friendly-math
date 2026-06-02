#!/usr/bin/env python3
"""Print topic × grade capability rows (sync check for docs/curriculum-matrix.md)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ai.fallback_tasks import fallback_tasks_for_topic
from app.domain.topic_catalog import (
    TOPIC_CATALOG,
    TOPIC_DISPLAY_ORDER,
    resolve_topic,
    topic_available_for_grade,
)

REF_DIR = ROOT / "data" / "reference_worksheets"


def _has_reference(grade: int, topic_id: str) -> bool:
    prefix = f"{grade}_"
    needle = topic_id.replace("_", "")
    for path in REF_DIR.glob("*.json"):
        stem = path.stem
        if not stem.startswith(prefix):
            continue
        if needle in stem.replace("_", ""):
            return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="emit markdown table rows",
    )
    args = parser.parse_args()

    rows: list[tuple] = []
    for grade in range(1, 9):
        for tid in TOPIC_DISPLAY_ORDER:
            defn = TOPIC_CATALOG[tid]
            if not topic_available_for_grade(defn, grade):
                continue
            resolved = resolve_topic(defn.label_pl, grade)
            rows.append(
                (
                    grade,
                    tid,
                    defn.label_pl,
                    resolved.blueprint_status,
                    defn.capabilities.answer_support,
                    fallback_tasks_for_topic(tid, grade, 1) is not None,
                    _has_reference(grade, tid),
                )
            )

    if args.markdown:
        print("| Klasa | topic_id | Temat UI | Blueprint | Klucz | Fallback | Wzorzec |")
        print("|------:|----------|----------|-----------|-------|:--------:|:-------:|")
        for g, tid, label, bp, ans, fb, ref in rows:
            fb_mark = "tak" if fb else "nie"
            ref_mark = "tak" if ref else "—"
            print(f"| {g} | `{tid}` | {label} | {bp} | {ans} | {fb_mark} | {ref_mark} |")
    else:
        for row in rows:
            print("\t".join(map(str, row)))
        print(f"TOTAL {len(rows)}")


if __name__ == "__main__":
    main()
