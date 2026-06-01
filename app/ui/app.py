#--------------------------------------------------
# FRIENDLY MATH - v1
# Generator kart pracy matematyki dla uczniów szkoły podstawowej
#--------------------------------------------------
#
# Autor: Tomasz Balabuch
# Data: 2026-02-24
# Wersja: 1.0.0
# 
#--------------------------------------------------
# --------------------------------------------------

# --------------------------------------------------
# Importy
# --------------------------------------------------

import os
import sys
from io import BytesIO
from pathlib import Path

try:
    import fitz  # type: ignore  # PyMuPDF
except ModuleNotFoundError:
    fitz = None  # pip install PyMuPDF — wtedy podgląd PDF jako obrazy będzie działał

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from app.ai.layout_generator import generate_layout
from app.ai.text_generator import generate_tasks, warning_messages
from app.generators.answers import compute_answer_key
from app.generators.images import generate_worksheet_image, generate_worksheet_images_for_tasks
from app.domain.profile_catalog import (
    default_profile_id,
    profile_ids_for_ui,
    profile_selectbox_labels,
    resolve_profile,
)
from app.domain.topic_catalog import (
    default_topic_label_for_grade,
    resolve_topic,
    topic_labels_for_grade,
)
from app.pdf.generator import WorksheetMeta, build_worksheet_pdf_bytes
from app.pdf.fonts import resolve_polish_font_path

def _pdf_bytes_to_images(pdf_bytes: bytes, dpi: int = 120) -> list[BytesIO]:
    """Konwertuje PDF (bytes) na listę obrazów stron (PNG w BytesIO). Wymaga: pip install PyMuPDF."""
    out = []
    if fitz is None:
        return out
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            pix = page.get_pixmap(dpi=dpi)
            png_bytes = pix.tobytes("png")
            out.append(BytesIO(png_bytes))
        doc.close()
    except Exception:
        pass
    return out


# --------------------------------------------------
# Konfiguracja strony
# --------------------------------------------------
st.set_page_config(
    page_title="Friendly Math",
    layout="centered",
)

# Cienka, szara ramka wokół podglądu stron PDF (PNG), żeby była widoczna na białym tle.
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

# --------------------------------------------------
# Panel boczny (lewa strona) – formularz
# --------------------------------------------------
st.sidebar.title("🧮 Friendly Math")
st.sidebar.subheader("Generator kart pracy")
st.sidebar.write(
    "Wybierz parametry karty pracy i kliknij **Generuj kartę**. "
    "Zadania zostaną wygenerowane przez AI, a PDF będzie gotowy do pobrania."
)
_font_path, _font_source = resolve_polish_font_path()
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
        help=(
            "Tematy zgodne z podstawą programową dla wybranej klasy. "
            "Lista aktualizuje się po zmianie klasy (przed wysłaniem formularza)."
        ),
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
        help=(
            "Profil dostosowuje styl zadań, układ PDF i sposób ilustracji. "
            "To preset dydaktyczny (PPP), nie diagnoza — wybierz opis pasujący do potrzeb ucznia."
        ),
    )
    _selected_profile = resolve_profile(student_profile)
    st.caption(_selected_profile.profile.ui_summary)

    include_illustration = st.checkbox(
        "Ilustracja w karcie",
        value=False,
        help=(
            "Domyślnie wyłączone. Profile „Standardowy”, „Zdolny” i „Dysleksja”: jedna ilustracja "
            "u góry karty. Profile „Dyskalkulia”, „ADHD” i „Trudności w nauce”: ilustracja przy "
            "zadaniu (tylko w bezpiecznym zakresie liczb). Dla tematów bez wsparcia wizualnego "
            "ilustracje są pomijane."
        ),
    )

    include_workspace = st.checkbox(
        "Miejsce na obliczenia",
        value=True,
        help=(
            "Pod każdym zadaniem rysowane są kropkowane linijki, na których uczeń "
            "może wykonać obliczenia. Domyślnie włączone."
        ),
    )

    include_answers = st.checkbox(
        "Dołącz stronę z odpowiedziami",
        value=False,
        help=(
            "Dodaje na końcu PDF stronę „Karta odpowiedzi” z wynikami. Klucz obsługuje: "
            "działania a op b, porównywanie liczb, równania z okienkiem, liczenie po, "
            "ułamki o tym samym mianowniku, intuicyjne ułamki (połowa/ćwierć)."
        ),
    )

    submitted = st.form_submit_button("🧠 Generuj kartę")

# --------------------------------------------------
# Sekcja główna – tylko wyniki (zadania + PDF)
# --------------------------------------------------
st.title("🧮 Friendly Math")

# --------------------------------------------------
# Logika po wysłaniu formularza
# --------------------------------------------------
if submitted:

    # v1.0: brak klucza API – nie wywołuj generowania
    if not os.getenv("OPENAI_API_KEY"):
        st.error(
            "Brak klucza **OPENAI_API_KEY**. Dodaj go do pliku `.env` w katalogu projektu "
            "(np. skopiuj z `.env.example` i uzupełnij klucz z platformy OpenAI)."
        )
        st.stop()

    # Prosta walidacja biznesowa
    if int(grade) <= 3 and number_of_tasks > 15:
        st.error("Dla klas 1–3 maksymalna liczba zadań to 15.")
    else:
        resolved_topic = resolve_topic(topic, _grade_int)
        resolved_profile = resolve_profile(student_profile)
        for warning in resolved_topic.warnings:
            st.warning(warning)
        for warning in resolved_profile.warnings:
            st.warning(warning)

        # request_payload = {
        #     "grade": int(grade),
        #     "topic": topic,
        #     "number_of_tasks": number_of_tasks,
        #     "student_profile": student_profile
        # }
        # st.success("✅ JSON request wygenerowany")
        # st.json(request_payload)
        # st.info(
        #     "Ten JSON będzie w kolejnym kroku wysyłany do API "
        #     "generującego zadania."
        # )

        st.subheader("📘 Wygenerowane zadania")

        result = generate_tasks(
            profile=student_profile,
            grade=grade,
            topic=resolved_topic.blueprint_key,
            n=number_of_tasks
        )

        for warning in warning_messages(result):
            st.warning(warning)

        if result.get("_blocked"):
            st.error(
                "Nie wygenerowano karty: system nie potrafi zachować wybranego tematu "
                "w bezpiecznym trybie zastępczym."
            )
            if result.get("_error"):
                st.caption(f"Szczegóły techniczne: {result['_error']}")
            st.stop()

        if result.get("_error"):
            st.warning(
                "Generowanie zadań przez API nie powiodło się (timeout lub błąd sieci). "
                "Poniżej zadania zastępcze zachowujące wybrany temat."
            )
        if result.get("_warning"):
            st.info(result["_warning"])

        # Lista zadań jako zwykły tekst
        tasks = result["tasks"]
        for i, task in enumerate(tasks, start=1):
            st.write(f"{i}. {task}")

        # ----------------------------------------------
        # PDF v0: generowanie, zapis do pliku + download
        # ----------------------------------------------
        st.divider()
        st.subheader("📄 Karta pracy PDF - podgląd")

        # Metadane karty pracy
        meta = WorksheetMeta(
            title=f"Karta pracy – klasa {grade}",
            grade=str(grade),
            topic_range=resolved_topic.label_pl,
            student_profile=resolved_profile.pdf_label,
            student_profile_id=resolved_profile.profile_id,
        )

        # Layout sterowany AI (Day 7) – font size, spacing, kolory
        layout = None
        try:
            layout = generate_layout(
                profile=resolved_profile.profile_id,
                grade=str(grade),
                number_of_tasks=number_of_tasks,
            )
        except Exception as e:
            st.warning(f"Layout AI niedostępny ({e}), używam domyślnego layoutu.")

        # Ilustracje są OPT-IN dla wszystkich profili (checkbox „Ilustracja w karcie").
        # Tematy w `_TOPICS_WITHOUT_IMAGES` (np. „równania") i tak są pomijane wewnątrz
        # generatora grafik – tu po prostu nie wywołujemy generatora gdy checkbox wyłączony.
        image_bytes = None
        task_images = None
        topic_skips_images = resolved_topic.capabilities.skip_images
        per_task_images = resolved_profile.illustration_mode == "per_task"

        if not include_illustration:
            st.caption("ℹ️ Ilustracje wyłączone – karta zawiera wyłącznie tekst zadań.")
        elif topic_skips_images:
            st.caption("ℹ️ Dla tego tematu ilustracje są wyłączone.")
        elif per_task_images:
            try:
                task_images = generate_worksheet_images_for_tasks(
                    tasks=tasks,
                    topic=resolved_topic.blueprint_key,
                    profile=resolved_profile.profile_id,
                    grade=_grade_int,
                )
            except Exception as e:
                st.warning(f"Grafiki per zadanie niedostępne ({e}), PDF bez ilustracji przy zadaniach.")
        else:
            try:
                image_bytes = generate_worksheet_image(
                    topic=resolved_topic.blueprint_key,
                    profile=resolved_profile.profile_id,
                    grade=_grade_int,
                )
            except Exception as e:
                st.warning(f"Grafika niedostępna ({e}), PDF bez ilustracji.")

        answer_key = None
        if include_answers:
            answer_key = compute_answer_key(
                tasks,
                topic_id=resolved_topic.topic_id,
                grade=_grade_int,
            )
            st.info(answer_key.summary_pl())
            review_nums = answer_key.tasks_needing_review()
            if review_nums:
                st.warning(
                    "Zadania bez automatycznej odpowiedzi (sprawdź ręcznie): "
                    + ", ".join(str(n) for n in review_nums)
                )

        # 1) Generowanie PDF (z layoutem, opcjonalnie image_bytes, task_images, answer_key)
        pdf_result = build_worksheet_pdf_bytes(
            meta=meta,
            tasks=tasks,
            layout=layout,
            image_bytes=image_bytes,
            task_images=task_images,
            answer_key=answer_key,
            include_workspace=include_workspace,
        )
        pdf_bytes = pdf_result.pdf_bytes
        for w in pdf_result.warnings:
            if w.code == "pdf_font_missing":
                st.warning(w.message)

        # 2) Zapis do pliku (wariant A)
        output_dir = ROOT_DIR / "data" / "out"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "worksheet.pdf"

        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

        # st.caption(f"Plik zapisany w: **{output_path.relative_to(ROOT_DIR)}**")

        # Podgląd PDF jako obrazy stron (działa w Chrome/Edge)
        page_images = _pdf_bytes_to_images(pdf_bytes)
        if page_images:
            for i, img_io in enumerate(page_images, start=1):
                st.image(img_io, caption=f"Strona {i}", width="stretch")
        else:
            st.caption("Podgląd niedostępny — pobierz PDF i otwórz plik na swoim komputerze.")

        st.caption("Po pobraniu otwórz plik (np. dwuklik), aby zobaczyć lub wydrukować PDF.")

        st.download_button(
            label="⬇️ Pobierz PDF",
            data=pdf_bytes,
            file_name="worksheet.pdf",
            mime="application/pdf",
        )

# --------------------------------------------------
# Stopka
# --------------------------------------------------
st.divider()
st.caption("Friendly Math v1.0 — generator kart pracy dla szkoły podstawowej")
