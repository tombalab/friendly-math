"""Local logging sink for worksheet events (P2.4)."""
from __future__ import annotations

import logging
import os

from app.observability.events import WorksheetEvent

_LOGGER = logging.getLogger("friendly_math.worksheet")


def is_observability_enabled() -> bool:
    """Domyślnie włączone; wyłącz: FRIENDLY_MATH_OBSERVABILITY=0|false|no."""
    raw = os.getenv("FRIENDLY_MATH_OBSERVABILITY", "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def emit_to_log(event: WorksheetEvent) -> None:
    """Jedna linia JSON na zdarzenie — czytelna w terminalu i plikach logów."""
    if not is_observability_enabled():
        return
    if not _LOGGER.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        _LOGGER.addHandler(handler)
        _LOGGER.setLevel(logging.INFO)
    _LOGGER.info(event.to_json_line())
