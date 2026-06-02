"""Observability panel for Streamlit sessions (P2.4)."""
from __future__ import annotations

import streamlit as st

from app.domain.worksheet_contract import WorksheetResult
from app.observability.events import WorksheetEvent


def render_events_panel(result: WorksheetResult) -> None:
    """Podgląd zdarzeń bieżącej generacji (bez treści zadań ani kontekstu)."""
    if not result.events:
        return

    with st.expander("🔍 Zdarzenia generacji (debug)", expanded=False):
        st.caption(f"request_id: `{result.request_id}`")
        for ev in result.events:
            st.markdown(f"**{ev.event}** · `{ev.ts}`")
            if ev.data:
                st.json(ev.data, expanded=False)


def record_download_event(result: WorksheetResult) -> None:
    """Wywołaj z `on_click` przycisku pobierania PDF."""
    from app.observability.events import EVENT_DOWNLOAD, WorksheetEvent
    from app.observability.sink import emit_to_log, is_observability_enabled

    data = {
        "success": result.success,
        "pdf_bytes": len(result.pdf_bytes) if result.pdf_bytes else 0,
    }
    ev = WorksheetEvent(
        request_id=result.request_id,
        event=EVENT_DOWNLOAD,
        data=data,
    )
    result.events.append(ev)
    if is_observability_enabled():
        emit_to_log(ev)
