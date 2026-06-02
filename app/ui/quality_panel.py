"""Generation quality panel for Streamlit (P1.6 / Phase 3)."""
from __future__ import annotations

import streamlit as st

from app.domain.profile_pedagogy import teacher_hint_for_profile
from app.domain.worksheet_contract import WorksheetResult, WorksheetWarning


def render_quality_panel(result: WorksheetResult) -> None:
    """Panel jakości przed podglądem PDF — ostrzeżenia pogrupowane po ważności."""
    st.subheader("📊 Jakość generacji")

    _render_status_banner(result)

    if result.resolved_profile:
        st.caption(teacher_hint_for_profile(result.resolved_profile.profile_id))

    summary = result.quality_summary_pl()
    cols = st.columns(2)
    items = list(summary.items())
    for i, (label, value) in enumerate(items):
        cols[i % 2].markdown(f"**{label}:** {value}")

    grouped = result.warnings_by_severity()
    task_quality = [w for w in grouped["warning"] if w.code.startswith("task_quality_")]
    other_warnings = [w for w in grouped["warning"] if not w.code.startswith("task_quality_")]

    if grouped["error"]:
        with st.expander("❌ Problemy blokujące / krytyczne", expanded=True):
            for w in grouped["error"]:
                st.error(_format_warning(w))

    if task_quality:
        with st.expander(f"📐 Walidacja zadań ({len(task_quality)})", expanded=bool(task_quality)):
            for w in task_quality:
                st.warning(_format_warning(w))

    if other_warnings:
        with st.expander(f"⚠️ Inne uwagi ({len(other_warnings)})", expanded=not grouped["error"]):
            for w in other_warnings:
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


def _render_status_banner(result: WorksheetResult) -> None:
    if result.blocked:
        st.error("Status: **zablokowano** — sprawdź błędy poniżej.")
        return
    errors = len(result.warnings_by_severity()["error"])
    warnings = len(result.warnings_by_severity()["warning"])
    if errors:
        st.error(f"Status: **błąd** ({errors} krytycznych).")
    elif warnings:
        st.warning(f"Status: **uwagi** ({warnings}) — PDF dostępny, warto przejrzeć.")
    else:
        st.success("Status: **OK** — brak istotnych ostrzeżeń.")


def _format_warning(w: WorksheetWarning) -> str:
    if w.code and w.code != "unknown":
        return f"{w.message} (`{w.code}`)"
    return w.message
