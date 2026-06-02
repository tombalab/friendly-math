"""Teacher review against reference worksheets (Phase 3)."""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.domain.worksheet_contract import WorksheetResult
from app.history.store import WorksheetHistoryStore
from app.review.reference_loader import find_best_reference, list_reference_cards


def render_review_tab(
    store: WorksheetHistoryStore,
    result: WorksheetResult | None,
    *,
    project_root: Path,
    request_id: str | None = None,
) -> None:
    """
    Porównanie z kartą wzorcową + zapis oceny nauczyciela (bez PII).
    """
    st.subheader("📝 Recenzja karty")

    rid = request_id
    meta = None
    if result is not None and result.request_id:
        rid = result.request_id
        grade = result.request.grade
        topic = result.request.topic_label
        profile = result.request.profile_id
        tasks = result.tasks
    elif rid:
        meta = store.load_meta(rid)
        if meta is None:
            st.warning("Wybierz kartę z historii lub wygeneruj nową.")
            return
        grade = meta.grade
        topic = meta.topic_label
        profile = meta.profile_id
        tasks = []
    else:
        st.info("Wygeneruj kartę lub otwórz wpis z historii, aby rozpocząć recenzję.")
        _render_reference_catalog(project_root)
        return

    ref = find_best_reference(
        grade=grade,
        topic_label=topic,
        profile_id=profile,
        project_root=project_root,
    )

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Twoja karta**")
        st.caption(f"Klasa {grade} · {topic} · {profile}")
        if tasks:
            for i, t in enumerate(tasks, start=1):
                st.write(f"{i}. {t}")
        elif meta:
            st.caption(f"PDF w historii (`{rid[:8]}…`)")

    with col_b:
        st.markdown("**Wzorzec referencyjny**")
        if ref is None:
            st.caption("Brak dokładnego wzorca dla tej kombinacji — użyj checklisty poniżej.")
        else:
            st.caption(ref.title)
            for i, t in enumerate(ref.tasks[:6], start=1):
                st.write(f"{i}. {t}")
            if len(ref.tasks) > 6:
                st.caption(f"… i {len(ref.tasks) - 6} kolejnych w pliku wzorca.")

    if ref is not None:
        with st.expander("Kryteria jakości wzorca", expanded=True):
            for line in ref.quality_criteria:
                st.markdown(f"- {line}")
            if ref.structured_criteria is not None:
                st.json(ref.structured_criteria.to_dict())

    _render_checklist()

    if rid:
        existing = store.load_review(rid)
        if existing:
            st.success(
                f"Zapisana recenzja: {existing.get('rating')}/5 "
                f"({existing.get('reviewed_at', '')[:16]})"
            )
            if existing.get("notes"):
                st.caption(existing["notes"])

        with st.form(f"review_form_{rid}"):
            rating = st.slider("Ocena jakości karty (1–5)", 1, 5, value=4)
            notes = st.text_area(
                "Notatki (bez imion uczniów)",
                placeholder="np. liczby za trudne, format OK, do druku",
                height=100,
            )
            if st.form_submit_button("Zapisz recenzję lokalnie"):
                store.save_review(
                    rid,
                    rating=rating,
                    notes=notes,
                    reference_file=ref.path.name if ref else None,
                )
                st.success("Recenzja zapisana w `data/history/` (tylko na tym komputerze).")
                st.rerun()


def _render_checklist() -> None:
    st.markdown("**Checklista nauczyciela**")
    st.markdown(
        """
- Czy temat i klasa się zgadzają?
- Czy polecenia są krótkie i czytelne (profil PPP)?
- Czy liczby mieszczą się w zakresie klasy?
- Czy PDF ma polskie znaki i czytelny układ?
- Czy klucz odpowiedzi (jeśli włączony) jest użyteczny?
        """
    )


def _render_reference_catalog(project_root: Path) -> None:
    cards = list_reference_cards(project_root)
    if not cards:
        return
    with st.expander("Dostępne karty wzorcowe w repo", expanded=False):
        for c in cards:
            st.caption(f"**{c.path.name}** — kl.{c.grade}, {c.topic}, {c.profile}")
