"""Render worksheet generation result (Phase 3)."""
from __future__ import annotations

from collections.abc import Callable
from io import BytesIO

import streamlit as st

from app.domain.worksheet_contract import WorksheetResult
from app.ui.events_panel import record_download_event
from app.ui.quality_panel import render_quality_panel


def render_generation_result(
    result: WorksheetResult,
    *,
    pdf_to_images: Callable[[bytes], list[BytesIO]],
    show_events: bool = True,
) -> None:
    """Pełny widok bieżącej generacji: jakość, zadania, PDF."""
    render_quality_panel(result)

    if show_events:
        from app.ui.events_panel import render_events_panel

        render_events_panel(result)

    if result.blocked:
        return

    st.subheader("📘 Wygenerowane zadania")
    for i, task in enumerate(result.tasks, start=1):
        st.write(f"{i}. {task}")

    if result.answer_key and result.answer_key.tasks_needing_review():
        st.warning(
            "Zadania bez automatycznej odpowiedzi: "
            + ", ".join(str(n) for n in result.answer_key.tasks_needing_review())
        )

    st.divider()
    st.subheader("📄 Karta pracy PDF — podgląd")

    if not result.pdf_bytes:
        st.caption("PDF niedostępny.")
        return

    page_images = pdf_to_images(result.pdf_bytes)
    if page_images:
        for i, img_io in enumerate(page_images, start=1):
            st.image(img_io, caption=f"Strona {i}", width="stretch")
    else:
        st.caption("Podgląd niedostępny — zainstaluj PyMuPDF lub pobierz PDF.")

    st.download_button(
        label="⬇️ Pobierz PDF",
        data=result.pdf_bytes,
        file_name="worksheet.pdf",
        mime="application/pdf",
        disabled=not result.can_download_pdf,
        on_click=record_download_event,
        args=(result,),
        key=f"download_{result.request_id or 'current'}",
    )
