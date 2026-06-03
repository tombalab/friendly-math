#!/usr/bin/env python3
"""Porównanie profili dla jednego tematu i klasy (plan naprawczy profili)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ai.fallback_tasks import fallback_tasks_for_topic
from app.domain.profile_catalog import resolve_profile
from app.domain.profile_pedagogy import get_pedagogy_spec
from app.domain.worksheet_layout import resolve_worksheet_layout
from app.validators.profile_enforcement import count_enriched_tasks
from app.validators.task_validator import validate_tasks_for_profile

PROFILES = (
    "standardowy",
    "ADHD",
    "dyskalkulia",
    "dysleksja",
    "trudności w nauce",
    "zdolny",
)


def _max_operand(tasks: list[str]) -> int:
    import re

    nums = [int(n) for t in tasks for n in re.findall(r"\d+", t)]
    return max(nums) if nums else 0


def _avg_length(tasks: list[str]) -> float:
    return sum(len(t) for t in tasks) / len(tasks) if tasks else 0.0


def report(topic_id: str, grade: int, n: int = 5) -> dict:
    rows: list[dict] = []
    fallback_sets: dict[str, list[str]] = {}

    for pid in PROFILES:
        tasks = fallback_tasks_for_topic(topic_id, grade, n, profile_id=pid) or []
        fallback_sets[pid] = tasks
        spec = get_pedagogy_spec(pid)
        rp = resolve_profile(pid)
        layout = resolve_worksheet_layout(rp, grade, n)
        validation = validate_tasks_for_profile(
            tasks, profile_id=pid, grade=grade, topic_id=topic_id
        )
        rows.append(
            {
                "profile": pid,
                "profile_group": spec.profile_group,
                "tasks": tasks,
                "max_operand": _max_operand(tasks),
                "avg_task_length": round(_avg_length(tasks), 1),
                "enriched_count": count_enriched_tasks(tasks),
                "validation_issues": len(validation.issues),
                "layout": {
                    "task_font_size": layout.task_font_size,
                    "task_spacing": layout.task_spacing,
                    "line_spacing": layout.line_spacing,
                    "workspace_lines": layout.workspace_lines,
                },
                "illustration_mode": rp.illustration_mode,
            }
        )

    unique_banks = len({frozenset(t) for t in fallback_sets.values()})
    return {
        "topic_id": topic_id,
        "grade": grade,
        "unique_fallback_banks": unique_banks,
        "profiles": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Raport różnic profili ucznia")
    parser.add_argument("--topic", default="dodawanie_do_20")
    parser.add_argument("--grade", type=int, default=1)
    parser.add_argument("--tasks", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    data = report(args.topic, args.grade, args.tasks)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    print(f"Temat: {data['topic_id']} · klasa {data['grade']}")
    print(f"Unikalne banki fallback: {data['unique_fallback_banks']}/{len(PROFILES)}")
    print()
    for row in data["profiles"]:
        print(f"=== {row['profile']} ({row['profile_group']}) ===")
        print(f"  max_operand={row['max_operand']}  avg_len={row['avg_task_length']}")
        print(f"  enriched={row['enriched_count']}  validation_issues={row['validation_issues']}")
        print(f"  layout: font={row['layout']['task_font_size']} spacing={row['layout']['task_spacing']}")
        for t in row["tasks"]:
            print(f"    · {t}")
        print()


if __name__ == "__main__":
    main()
