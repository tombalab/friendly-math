#--------------------------------------------------
# FRIENDLY MATH - Streamlit UI (cienka warstwa nad WorksheetService)
#--------------------------------------------------

import os
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
from app.domain.profile_catalog import (
    default_profile_id,
    profile_ids_for_ui,
    profile_selectbox_labels,
    resolve_profile,
)
from app.domain.topic_catalog import (
    default_topic_label_for_grade,
    topic_labels_for_grade,
)
from app.domain.worksheet_contract import WorksheetRequest
from app.pdf.fonts import resolve_polish_font_path
from app.ui.quality_panel import render_quality_panel
from app.worksheet.service import WorksheetService


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


st.set_page_config(page_title="Friendly Math", layout="centered")

st.markdown(
    """
    <style>
    .stImage img {
        border: 1px solid #d0d0d0;
        border-radius: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.title("🧮 Friendly Math")
st.sidebar.subheader("Generator kart pracy")
st.sidebar.write(
    "Wybierz parametry karty pracy i kliknij **Generuj kartę**. "
    "Zadania zostaną wygenerowane przez AI, a PDF będzie gotowy do pobrania."
)

_font_path, _ = resolve_polish_font_path()
if _font_path is None:
    st.sidebar.warning(
        "Brak czcionki DejaVu Sans — PDF może nie wyświetlać polskich znaków. "
        "Zainstaluj zależności projektu (patrz assets/fonts/README.md)."
    )

grade = st.sidebar.selectbox(
    "Klasa",
    options=["1", "2", "3", "4", "5", "6", "7", "8"],
    index=1,
    help="Klasa ucznia (1–8). Wpływa na poziom trudności zadań i dostępne tematy.",
)
_grade_int = int(grade)
_topic_options = topic_labels_for_grade(_grade_int)
_default_topic = default_topic_label_for_grade(_grade_int)
_topic_index = (
    _topic_options.index(_default_topic) if _default_topic in _topic_options else 0
)

with st.sidebar.form("worksheet_form"):
    topic = st.selectbox(
        "Zakres materiału",
        options=_topic_options,
        index=_topic_index,
        help="Tematy zgodne z podstawą programową dla wybranej klasy.",
    )
    number_of_tasks = st.number_input(
        "Liczba zadań",
        min_value=1,
        max_value=30,
        value=5,
        step=1,
        help="Ile zadań ma zawierać karta (1–30). Dla klas 1–3 max 15.",
    )
    _profile_ids = profile_ids_for_ui()
    _profile_labels = profile_selectbox_labels()
    _default_pid = default_profile_id()
    student_profile = st.selectbox(
        "Profil ucznia",
        options=_profile_ids,
        index=_profile_ids.index(_default_pid) if _default_pid in _profile_ids else 0,
        format_func=lambda pid: _profile_labels.get(pid, pid),
        help="Preset dydaktyczny (PPP), nie diagnoza kliniczna.",
    )
    _selected_profile = resolve_profile(student_profile)
    st.caption(_selected_profile.profile.ui_summary)

    include_illustration = st.checkbox("Ilustracja w karcie", value=False)
    include_workspace = st.checkbox("Miejsce na obliczenia", value=True)
    include_answers = st.checkbox("Dołącz stronę z odpowiedziami", value=False)
    submitted = st.form_submit_button("🧠 Generuj kartę")

st.title("🧮 Friendly Math")

if submitted:
    request = WorksheetRequest(
        grade=_grade_int,
        topic_label=topic,
        profile_id=student_profile,
        number_of_tasks=int(number_of_tasks),
        include_illustration=include_illustration,
        include_workspace=include_workspace,
        include_answers=include_answers,
    )

    service = WorksheetService(output_dir=ROOT_DIR / "data" / "out")
    result = service.generate(request)

    render_quality_panel(result)

    if result.blocked:
        st.stop()

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

    if result.pdf_bytes:
        page_images = _pdf_bytes_to_images(result.pdf_bytes)
        if page_images:
            for i, img_io in enumerate(page_images, start=1):
                st.image(img_io, caption=f"Strona {i}", width="stretch")
        else:
            st.caption("Podgląd niedostępny — pobierz PDF lokalnie.")

        st.download_button(
            label="⬇️ Pobierz PDF",
            data=result.pdf_bytes,
            file_name="worksheet.pdf",
            mime="application/pdf",
            disabled=not result.can_download_pdf,
        )
    else:
        st.caption("PDF niedostępny.")

st.divider()
st.caption("Friendly Math v1.1 — generator kart pracy dla szkoły podstawowej")
