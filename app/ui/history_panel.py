"""Local worksheet history UI (P2.5)."""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.history.store import WorksheetHistoryStore
from app.ui.events_panel import record_download_event


def render_history_sidebar(store: WorksheetHistoryStore) -> str | None:
    """
    Lista ostatnich kart w sidebarze.
    Zwraca request_id do podglądu lub None.
    """
    entries = store.list_recent(limit=15)
    if not entries:
        st.sidebar.caption("Historia pusta — wygeneruj pierwszą kartę.")
        return None

    st.sidebar.divider()
    st.sidebar.subheader("📁 Historia (lokalna)")
    st.sidebar.caption(
        "Zapis w `data/history/` na tym komputerze. Bez imion uczniów — opcjonalna etykieta grupy."
    )

    by_id = {e.request_id: e for e in entries}
    selected = st.sidebar.selectbox(
        "Ostatnie karty",
        options=list(by_id.keys()),
        format_func=lambda rid: by_id[rid].display_title_pl(),
        key="fm_history_select",
    )

    if st.sidebar.button("Otwórz wybraną", key="fm_history_open"):
        st.session_state["fm_history_view"] = selected
        st.session_state.pop("fm_show_last_generation", None)

    if st.session_state.get("fm_history_view"):
        return st.session_state["fm_history_view"]
    return None


def render_history_view(
    store: WorksheetHistoryStore,
    request_id: str,
    *,
    pdf_to_images,
) -> None:
    """Podgląd karty z historii."""
    meta = store.load_meta(request_id)
    pdf_bytes = store.load_pdf_bytes(request_id)

    if meta is None or pdf_bytes is None:
        st.error("Nie znaleziono wpisu historii — mógł zostać usunięty ręcznie.")
        if st.button("Wróć"):
            st.session_state.pop("fm_history_view", None)
            st.rerun()
        return

    st.subheader("📁 Karta z historii")
    st.caption(meta.display_title_pl())
    st.caption(f"`request_id`: {meta.request_id}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Temat:** {meta.topic_label}")
        st.markdown(f"**Profil:** {meta.profile_label}")
    with col2:
        st.markdown(f"**Klasa:** {meta.grade}")
        st.markdown(f"**Zadań:** {meta.number_of_tasks}")
        if meta.worksheet_label:
            st.markdown(f"**Etykieta:** {meta.worksheet_label}")

    if meta.used_fallback:
        st.info("Źródło zadań: zastępcze (fallback).")
    if meta.warning_count:
        st.warning(
            f"{meta.warning_count} ostrzeżeń: "
            + ", ".join(meta.warning_codes[:8])
            + ("…" if len(meta.warning_codes) > 8 else "")
        )

    if meta.answers.get("enabled"):
        st.markdown(f"**Klucz odpowiedzi:** {meta.answers.get('summary_pl', '—')}")
    if meta.images:
        st.markdown(f"**Ilustracje:** {meta.images.get('detail_pl', '—')}")

    with st.expander("Metadane (JSON)", expanded=False):
        st.json(meta.to_dict())

    st.divider()
    st.subheader("📄 PDF z archiwum")

    page_images = pdf_to_images(pdf_bytes)
    if page_images:
        for i, img_io in enumerate(page_images, start=1):
            st.image(img_io, caption=f"Strona {i}", width="stretch")
    else:
        st.caption("Podgląd niedostępny — pobierz PDF.")

    class _DownloadProxy:
        """Minimalny obiekt dla record_download_event."""

        def __init__(self, rid: str, data: bytes) -> None:
            self.request_id = rid
            self.success = True
            self.pdf_bytes = data
            self.events = []

    st.download_button(
        label="⬇️ Pobierz PDF z historii",
        data=pdf_bytes,
        file_name=f"worksheet_{request_id[:8]}.pdf",
        mime="application/pdf",
        on_click=record_download_event,
        args=(_DownloadProxy(request_id, pdf_bytes),),
    )

    if st.button("Zamknij podgląd historii"):
        st.session_state.pop("fm_history_view", None)
        st.rerun()


def history_store_for_root(project_root: Path) -> WorksheetHistoryStore:
    from app.history.store import default_history_dir

    return WorksheetHistoryStore(default_history_dir(project_root))
