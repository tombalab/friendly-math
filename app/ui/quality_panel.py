"""Generation quality panel for Streamlit (P1.6)."""
from __future__ import annotations

import streamlit as st

from app.domain.worksheet_contract import WorksheetResult, WorksheetWarning


def render_quality_panel(result: WorksheetResult) -> None:
    """Panel jakości przed podglądem PDF — ostrzeżenia pogrupowane po ważności."""
    st.subheader("📊 Jakość generacji")

    summary = result.quality_summary_pl()
    cols = st.columns(2)
    items = list(summary.items())
    for i, (label, value) in enumerate(items):
        cols[i % 2].markdown(f"**{label}:** {value}")

    grouped = result.warnings_by_severity()
    if grouped["error"]:
        with st.expander("❌ Problemy blokujące / krytyczne", expanded=True):
            for w in grouped["error"]:
                st.error(_format_warning(w))
    if grouped["warning"]:
        with st.expander("⚠️ Uwagi", expanded=not grouped["error"]):
            for w in grouped["warning"]:
                st.warning(_format_warning(w))
    if grouped["info"]:
        with st.expander("ℹ️ Informacje", expanded=False):
            for w in grouped["info"]:
                st.info(_format_warning(w))

    if result.blocked:
        st.error(
            "Karta nie została w pełni wygenerowana — pobieranie PDF jest wyłączone."
        )
    elif result.used_fallback:
        st.info(
            "Zadania pochodzą z bezpiecznego szablonu tematycznego (nie z pełnej odpowiedzi AI)."
        )


def _format_warning(w: WorksheetWarning) -> str:
    if w.code and w.code != "unknown":
        return f"{w.message} (`{w.code}`)"
    return w.message
