"""Local worksheet history UI (P2.5 / Phase 3)."""
from __future__ import annotations

from collections.abc import Callable
from io import BytesIO

import streamlit as st

from app.history.store import WorksheetHistoryStore
from app.ui.events_panel import record_download_event


def render_history_sidebar(store: WorksheetHistoryStore) -> None:
    """Filtry i skróty historii w sidebarze."""
    entries = store.list_recent(limit=30)
    if not entries:
        st.sidebar.caption("Historia pusta — wygeneruj pierwszą kartę.")
        return

    st.sidebar.divider()
    st.sidebar.subheader("📁 Historia")
    filter_grade = st.sidebar.selectbox(
        "Filtr: klasa",
        options=["wszystkie"] + sorted({str(e.grade) for e in entries}),
        key="fm_hist_filter_grade",
    )
    filter_topic = st.sidebar.text_input(
        "Filtr: temat",
        placeholder="np. dodawanie",
        key="fm_hist_filter_topic",
    )

    grade_val = None if filter_grade == "wszystkie" else int(filter_grade)
    filtered = store.list_recent(
        limit=15,
        grade=grade_val,
        topic_query=filter_topic or None,
    )

    if not filtered:
        st.sidebar.caption("Brak wpisów dla filtra.")
        return

    by_id = {e.request_id: e for e in filtered}
    selected = st.sidebar.selectbox(
        "Ostatnie karty",
        options=list(by_id.keys()),
        format_func=lambda rid: by_id[rid].display_title_pl(
            reviewed=store.has_review(rid)
        ),
        key="fm_history_select",
    )

    c1, c2 = st.sidebar.columns(2)
    if c1.button("Otwórz", key="fm_history_open", use_container_width=True):
        st.session_state["fm_history_view"] = selected
        st.session_state["fm_nav_target"] = "Historia"
        st.rerun()
    if c2.button("Recenzja", key="fm_history_review", use_container_width=True):
        st.session_state["fm_history_view"] = selected
        st.session_state["fm_nav_target"] = "Recenzja"
        st.rerun()

    last = st.session_state.get("fm_last_result")
    if last and last.request_id and st.sidebar.button("Ostatnia generacja"):
        st.session_state.pop("fm_history_view", None)
        st.session_state["fm_nav_target"] = "Generuj"
        st.rerun()


def render_history_page(
    store: WorksheetHistoryStore,
    request_id: str | None,
    *,
    pdf_to_images: Callable[[bytes], list[BytesIO]],
) -> None:
    """Pełnostronicowy podgląd historii."""
    if not request_id:
        entries = store.list_recent(limit=20)
        if not entries:
            st.info("Brak zapisanych kart. Wygeneruj pierwszą kartę w zakładce **Generuj**.")
            return
        st.caption("Wybierz kartę w panelu bocznym → **Otwórz**.")
        for e in entries[:10]:
            badge = e.quality_badge_pl
            st.markdown(f"- **{e.display_title_pl(reviewed=store.has_review(e.request_id))}** — _{badge}_")
        return

    render_history_view(store, request_id, pdf_to_images=pdf_to_images)


def render_history_view(
    store: WorksheetHistoryStore,
    request_id: str,
    *,
    pdf_to_images: Callable[[bytes], list[BytesIO]],
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
    st.caption(meta.display_title_pl(reviewed=store.has_review(request_id)))
    st.caption(f"`request_id`: {meta.request_id} · jakość: **{meta.quality_badge_pl}**")

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

    review = store.load_review(request_id)
    if review:
        st.success(f"Recenzja: {review.get('rating')}/5")

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
        key=f"hist_dl_{request_id[:8]}",
    )

    if st.button("Zamknij podgląd historii"):
        st.session_state.pop("fm_history_view", None)
        st.session_state["fm_nav_target"] = "Generuj"
        st.rerun()


def history_store_for_root(project_root) -> WorksheetHistoryStore:
    from app.history.store import default_history_dir

    return WorksheetHistoryStore(default_history_dir(project_root))
