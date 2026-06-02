"""Load and match reference worksheets for teacher review (Phase 3)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.domain.structured_criteria import StructuredQualityCriteria


@dataclass(frozen=True)
class ReferenceCard:
    path: Path
    title: str
    grade: int
    topic: str
    profile: str
    tasks: tuple[str, ...]
    quality_criteria: tuple[str, ...]
    structured_criteria: StructuredQualityCriteria | None
    metadata: dict[str, Any] = field(repr=False)

    @classmethod
    def from_file(cls, path: Path) -> ReferenceCard | None:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        meta = raw.get("metadata")
        if not isinstance(meta, dict):
            return None
        tasks = raw.get("tasks")
        if not isinstance(tasks, list):
            return None
        criteria = raw.get("quality_criteria")
        if not isinstance(criteria, list):
            criteria = []
        structured = None
        if raw.get("structured_criteria"):
            structured = StructuredQualityCriteria.from_mapping(raw["structured_criteria"])
        return cls(
            path=path,
            title=str(meta.get("title", path.stem)),
            grade=int(meta["grade"]),
            topic=str(meta["topic"]),
            profile=str(meta["profile"]),
            tasks=tuple(str(t) for t in tasks),
            quality_criteria=tuple(str(c) for c in criteria),
            structured_criteria=structured,
            metadata=meta,
        )

    def match_key(self) -> str:
        return f"{self.grade}|{self.topic.casefold()}|{self.profile.casefold()}"


def reference_dir(project_root: Path | None = None) -> Path:
    root = project_root or Path(__file__).resolve().parents[2]
    return root / "data" / "reference_worksheets"


def list_reference_cards(project_root: Path | None = None) -> list[ReferenceCard]:
    ref_dir = reference_dir(project_root)
    if not ref_dir.is_dir():
        return []
    cards: list[ReferenceCard] = []
    for path in sorted(ref_dir.glob("*.json")):
        card = ReferenceCard.from_file(path)
        if card is not None:
            cards.append(card)
    return cards


def find_best_reference(
    *,
    grade: int,
    topic_label: str,
    profile_id: str,
    project_root: Path | None = None,
) -> ReferenceCard | None:
    """
    Dopasowuje kartę wzorcową po klasie, temacie i profilu (heurystyka tekstowa).
  """
    topic_cf = topic_label.casefold()
    profile_cf = profile_id.casefold()
    best: ReferenceCard | None = None
    best_score = 0

    for card in list_reference_cards(project_root):
        if card.grade != grade:
            continue
        score = 0
        if card.topic.casefold() in topic_cf or topic_cf in card.topic.casefold():
            score += 3
        if card.profile.casefold() in profile_cf or profile_cf in card.profile.casefold():
            score += 2
        if score > best_score:
            best_score = score
            best = card
    return best if best_score >= 3 else None
