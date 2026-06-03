"""Filesystem store for local worksheet history (P2.5)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from app.history.models import HistoryEntryMeta, utc_now_iso

if TYPE_CHECKING:
    from app.domain.worksheet_contract import WorksheetResult
    from app.observability.events import GenerationTrace

META_FILENAME = "meta.json"
PDF_FILENAME = "worksheet.pdf"
EVENTS_FILENAME = "events.jsonl"
REVIEW_FILENAME = "review.json"


def default_history_dir(project_root: Path | None = None) -> Path:
    root = project_root or Path(__file__).resolve().parents[2]
    return root / "data" / "history"


class WorksheetHistoryStore:
    """
    Lokalny katalog `data/history/<request_id>/` z PDF i metadanymi.
    Prototyp — nie zastępuje polityki prywatności w środowisku wieloużytkownikowym.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def entry_dir(self, request_id: str) -> Path:
        return self.root / request_id

    def save(
        self,
        result: "WorksheetResult",
        trace: "GenerationTrace | None" = None,
        *,
        worksheet_label: str | None = None,
    ) -> Path:
        if not result.request_id:
            raise ValueError("WorksheetResult.request_id jest wymagane do zapisu historii")
        if not result.pdf_bytes:
            raise ValueError("Brak PDF — historia zapisuje tylko udane karty z plikiem")

        entry_dir = self.entry_dir(result.request_id)
        entry_dir.mkdir(parents=True, exist_ok=True)

        pdf_path = entry_dir / PDF_FILENAME
        pdf_path.write_bytes(result.pdf_bytes)

        label = worksheet_label
        if label is None:
            label = result.request.worksheet_label
        meta = self._meta_from_result(result, worksheet_label=label)
        meta_path = entry_dir / META_FILENAME
        meta_path.write_text(
            json.dumps(meta.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        if trace and trace.events:
            events_path = entry_dir / EVENTS_FILENAME
            lines = [ev.to_json_line() for ev in trace.events]
            events_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        return entry_dir

    def list_recent(
        self,
        limit: int = 20,
        *,
        grade: int | None = None,
        topic_query: str | None = None,
    ) -> list[HistoryEntryMeta]:
        if not self.root.is_dir():
            return []

        q = (topic_query or "").strip().casefold()
        entries: list[HistoryEntryMeta] = []
        for child in self.root.iterdir():
            if not child.is_dir():
                continue
            meta_path = child / META_FILENAME
            if not meta_path.is_file():
                continue
            try:
                raw = json.loads(meta_path.read_text(encoding="utf-8"))
                entry = HistoryEntryMeta.from_dict(raw)
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                continue
            if grade is not None and entry.grade != grade:
                continue
            if q and q not in entry.topic_label.casefold() and q not in entry.profile_label.casefold():
                continue
            entries.append(entry)

        entries.sort(key=lambda e: e.created_at, reverse=True)
        return entries[:limit]

    def save_review(
        self,
        request_id: str,
        *,
        rating: int,
        notes: str,
        reference_file: str | None = None,
    ) -> Path:
        entry_dir = self.entry_dir(request_id)
        if not entry_dir.is_dir():
            raise FileNotFoundError(f"Brak wpisu historii: {request_id}")
        payload = {
            "rating": rating,
            "notes": notes.strip(),
            "reviewed_at": utc_now_iso(),
            "reference_file": reference_file,
        }
        path = entry_dir / REVIEW_FILENAME
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def load_review(self, request_id: str) -> dict | None:
        path = self.entry_dir(request_id) / REVIEW_FILENAME
        if not path.is_file():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            return raw if isinstance(raw, dict) else None
        except (json.JSONDecodeError, OSError):
            return None

    def has_review(self, request_id: str) -> bool:
        return (self.entry_dir(request_id) / REVIEW_FILENAME).is_file()

    def load_meta(self, request_id: str) -> HistoryEntryMeta | None:
        meta_path = self.entry_dir(request_id) / META_FILENAME
        if not meta_path.is_file():
            return None
        try:
            raw = json.loads(meta_path.read_text(encoding="utf-8"))
            return HistoryEntryMeta.from_dict(raw)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return None

    def load_pdf_bytes(self, request_id: str) -> bytes | None:
        meta = self.load_meta(request_id)
        if meta is None:
            return None
        pdf_path = self.entry_dir(request_id) / meta.pdf_relative
        if not pdf_path.is_file():
            return None
        return pdf_path.read_bytes()

    def _meta_from_result(
        self,
        result: "WorksheetResult",
        *,
        worksheet_label: str | None,
    ) -> HistoryEntryMeta:
        req = result.request
        topic = result.resolved_topic
        profile = result.resolved_profile

        answers: dict = {"enabled": result.request.include_answers}
        if result.answer_key is not None:
            ak = result.answer_key
            answers.update(
                {
                    "supported_count": ak.supported_count,
                    "total": len(result.tasks),
                    "manual_review_count": ak.manual_review_count,
                    "summary_pl": ak.summary_pl(),
                }
            )

        images: dict = {}
        if result.image_coverage is not None:
            ic = result.image_coverage
            images = {
                "mode": ic.mode,
                "requested": ic.requested,
                "rendered_count": ic.rendered_count,
                "total_slots": ic.total_slots,
                "detail_pl": ic.detail_pl,
            }
            if ic.per_task:
                images["per_task"] = [
                    {
                        "task_index": entry.task_index,
                        "rendered": entry.rendered,
                        "skip_reason": entry.skip_reason,
                    }
                    for entry in ic.per_task
                ]

        label = (worksheet_label or "").strip() or None

        return HistoryEntryMeta(
            request_id=result.request_id,
            created_at=utc_now_iso(),
            grade=req.grade,
            topic_label=req.topic_label,
            topic_id=topic.topic_id if topic else "",
            profile_id=req.profile_id,
            profile_label=profile.ui_label if profile else req.profile_id,
            number_of_tasks=req.number_of_tasks,
            success=result.success,
            blocked=result.blocked,
            used_fallback=result.used_fallback,
            warning_count=len(result.warnings),
            warning_codes=sorted({w.code for w in result.warnings if w.code}),
            answers=answers,
            images=images,
            worksheet_label=label,
            pdf_relative=PDF_FILENAME,
        )
