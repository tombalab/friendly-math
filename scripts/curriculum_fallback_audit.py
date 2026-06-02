#!/usr/bin/env python3
"""Audit fallback banks vs profile validators (Faza 5 — curriculum smoke)."""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ai.fallback_tasks import fallback_tasks_for_topic
from app.domain.profile_catalog import profile_ids_for_ui
from app.domain.topic_catalog import TOPIC_CATALOG, topic_available_for_grade
from app.validators.task_validator import validate_tasks_for_profile


def run_audit(*, verbose: bool = False) -> int:
    profiles = profile_ids_for_ui()
    issues_by_code: Counter[str] = Counter()
    failing: list[tuple[int, str, str, Counter[str]]] = []
    audited = 0
    missing = 0

    for grade in range(1, 9):
        topic_ids = [
            tid
            for tid, defn in TOPIC_CATALOG.items()
            if topic_available_for_grade(defn, grade)
        ]
        for topic_id in topic_ids:
            for profile_id in profiles:
                tasks = fallback_tasks_for_topic(
                    topic_id, grade, 5, profile_id=profile_id
                )
                if not tasks:
                    missing += 1
                    if verbose:
                        print(f"MISSING bank: kl.{grade} {topic_id} / {profile_id}")
                    continue
                audited += 1
                result = validate_tasks_for_profile(
                    tasks,
                    profile_id=profile_id,
                    grade=grade,
                    topic_id=topic_id,
                )
                if result.issues:
                    counts = Counter(i.code for i in result.issues)
                    issues_by_code.update(counts)
                    failing.append((grade, topic_id, profile_id, counts))
                    if verbose:
                        print(
                            f"FAIL kl.{grade} {topic_id} / {profile_id}: {dict(counts)}"
                        )

    combos = sum(
        1
        for grade in range(1, 9)
        for defn in TOPIC_CATALOG.values()
        if topic_available_for_grade(defn, grade)
    )
    print(
        f"profiles={len(profiles)} ui_topic_combos={combos} "
        f"audited={audited} missing_banks={missing} failing={len(failing)}"
    )
    if issues_by_code:
        print("issues_by_code:", dict(sorted(issues_by_code.items())))
    if failing and not verbose:
        print(f"(use --verbose for {len(failing)} failing rows)")

    return 1 if failing or missing else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print each failing combination",
    )
    args = parser.parse_args()
    sys.exit(run_audit(verbose=args.verbose))


if __name__ == "__main__":
    main()
