#--------------------------------------------------
# FRIENDLY MATH - Streamlit UI (Phase 3 polish)
#--------------------------------------------------

import sys
from io import BytesIO
from pathlib import Path

try:
    import fitz  # type: ignore
except ModuleNotFoundError:
    fitz = None

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from app.domain.educational_strategy import available_templates
from app.domain.profile_catalog import (
    default_profile_id,
    profile_ids_for_ui,
    profile_selectbox_labels,
    resolve_profile,
)
from app.domain.profile_pedagogy import teacher_hint_for_profile
from app.domain.topic_catalog import (
    answer_key_expectation_pl,
    default_topic_label_for_grade,
    topic_labels_for_grade,
    upper_grades_mvp_caption_pl,
)
from app.domain.worksheet_contract import WorksheetRequest
from app.history.store import default_history_dir
from app.pdf.fonts import resolve_polish_font_path
from app.ui.generation_view import render_generation_result
from app.ui.history_panel import history_store_for_root, render_history_page, render_history_sidebar
from app.ui.review_panel import render_review_tab
from app.worksheet.service import WorksheetService

HISTORY_DIR = default_history_dir(ROOT_DIR)
OUT_DIR = ROOT_DIR / "data" / "out"
_history_store = history_store_for_root(ROOT_DIR)

APP_VERSION = "1.3.0"


def _pdf_bytes_to_images(pdf_bytes: bytes, dpi: int = 120) -> list[BytesIO]:
    out: list[BytesIO] = []
    if fitz is None:
        return out
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            pix = page.get_pixmap(dpi=dpi)
            out.append(BytesIO(pix.tobytes("png")))
        doc.close()
    except Exception:
        pass
    return out


st.set_page_config(page_title="Friendly Math", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
    .stImage img { border: 1px solid #d0d0d0; border-radius: 4px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.title("🧮 Friendly Math")
st.sidebar.caption(f"v{APP_VERSION} · Streamlit MVP")

_font_path, _ = resolve_polish_font_path()
if _font_path is None:
    st.sidebar.warning(
        "Brak czcionki DejaVu Sans — patrz assets/fonts/README.md."
    )

grade = st.sidebar.selectbox(
    "Klasa",
    options=["1", "2", "3", "4", "5", "6", "7", "8"],
    index=1,
    key="fm_grade",
)
_grade_int = int(grade)
_mvp_caption = upper_grades_mvp_caption_pl(_grade_int)
if _mvp_caption:
    st.sidebar.info(_mvp_caption)

_topic_options = topic_labels_for_grade(_grade_int)
_default_topic = default_topic_label_for_grade(_grade_int)
_topic_index = (
    _topic_options.index(_default_topic) if _default_topic in _topic_options else 0
)

topic = st.sidebar.selectbox(
    "Zakres materiału",
    options=_topic_options,
    index=_topic_index,
    key="fm_topic",
)

include_answers = st.sidebar.checkbox("Dołącz stronę z odpowiedziami", value=False)
if include_answers:
    _key_hint = answer_key_expectation_pl(topic, _grade_int)
    if _key_hint:
        st.sidebar.warning(_key_hint)

with st.sidebar.form("worksheet_form"):
    number_of_tasks = st.number_input("Liczba zadań", min_value=1, max_value=30, value=5, step=1)
    _profile_ids = profile_ids_for_ui()
    _profile_labels = profile_selectbox_labels()
    _default_pid = default_profile_id()
    student_profile = st.selectbox(
        "Profil ucznia",
        options=_profile_ids,
        index=_profile_ids.index(_default_pid) if _default_pid in _profile_ids else 0,
        format_func=lambda pid: _profile_labels.get(pid, pid),
    )
    st.caption(teacher_hint_for_profile(student_profile))
    _templates = available_templates()
    visual_template_id = st.selectbox(
        "Szablon wizualny",
        options=list(_templates.keys()),
        format_func=lambda tid: _templates.get(tid, tid),
    )
    worksheet_label = st.text_input(
        "Etykieta karty (opcjonalnie)",
        placeholder="np. grupa A",
    )
    include_illustration = st.checkbox("Ilustracja w karcie", value=False)
    include_workspace = st.checkbox("Miejsce na obliczenia", value=True)
    submitted = st.form_submit_button("🧠 Generuj kartę", use_container_width=True)

render_history_sidebar(_history_store)

if "fm_page" not in st.session_state:
    st.session_state["fm_page"] = "Generuj"

# Nawigacja programowa (przyciski historii) — przed widgetem `fm_page`.
_nav = st.session_state.pop("fm_nav_target", None)
if _nav:
    st.session_state["fm_page"] = _nav

if submitted:
    st.session_state.pop("fm_history_view", None)
    st.session_state["fm_page"] = "Generuj"

st.title("🧮 Friendly Math")

page = st.radio(
    "Sekcja",
    options=["Generuj", "Historia", "Recenzja"],
    horizontal=True,
    key="fm_page",
    label_visibility="collapsed",
)

if submitted:
    request = WorksheetRequest(
        grade=_grade_int,
        topic_label=topic,
        profile_id=student_profile,
        number_of_tasks=int(number_of_tasks),
        include_illustration=include_illustration,
        include_workspace=include_workspace,
        include_answers=include_answers,
        worksheet_label=worksheet_label.strip() or None,
        visual_template_id=visual_template_id,
    )
    service = WorksheetService(output_dir=OUT_DIR, history_dir=HISTORY_DIR)
    with st.spinner("Generowanie karty…"):
        result = service.generate(request)
    st.session_state["fm_last_result"] = result

    if result.history_path:
        st.toast(f"Zapisano w historii: {result.history_path.name}")

if page == "Generuj":
    result = st.session_state.get("fm_last_result")
    if result is None and not submitted:
        st.info(
            "Ustaw parametry w panelu bocznym i kliknij **Generuj kartę**. "
            "Po generacji zobaczysz jakość, zadania i podgląd PDF."
        )
        with st.expander("Ograniczenia MVP (przeczytaj raz)", expanded=False):
            st.markdown(
                """
- Wymaga `OPENAI_API_KEY` w `.env` lub Secrets (Streamlit Cloud).
- Klasy 1–3: max 15 zadań; klasy 4–8: wąski zakres rachunkowy (nie pełna PP).
- Klucz odpowiedzi: pełny, częściowy lub ręczny — zależnie od tematu (podpowiedź przy checkboxie).
- Historia i recenzje są **lokalne** na tym komputerze (bez kont użytkowników).
                """
            )
    elif result is not None:
        render_generation_result(result, pdf_to_images=_pdf_bytes_to_images)

elif page == "Historia":
    render_history_page(
        _history_store,
        st.session_state.get("fm_history_view"),
        pdf_to_images=_pdf_bytes_to_images,
    )

elif page == "Recenzja":
    render_review_tab(
        _history_store,
        st.session_state.get("fm_last_result"),
        project_root=ROOT_DIR,
        request_id=st.session_state.get("fm_history_view"),
    )

st.divider()
st.caption(
    f"Friendly Math v{APP_VERSION} — generator kart pracy · "
    "historia: `data/history/` · bez danych osobowych uczniów"
)
