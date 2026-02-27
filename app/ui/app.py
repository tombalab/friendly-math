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
from app.ai.text_generator import generate_tasks
from app.generators.answers import compute_answers
from app.generators.images import generate_worksheet_image, generate_worksheet_images_for_tasks
from app.pdf.generator import WorksheetMeta, build_worksheet_pdf_bytes

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

# --------------------------------------------------
# Panel boczny (lewa strona) – formularz
# --------------------------------------------------
st.sidebar.title("🧮 Friendly Math")
st.sidebar.subheader("Generator kart pracy")
st.sidebar.write(
    "Wybierz parametry karty pracy i kliknij **Generuj kartę**. "
    "Zadania zostaną wygenerowane przez AI, a PDF będzie gotowy do pobrania."
)

with st.sidebar.form("worksheet_form"):
    grade = st.selectbox(
        "Klasa",
        options=["1", "2", "3", "4", "5", "6", "7", "8"],
        index=1,
        help="Klasa ucznia (1–8). Wpływa na poziom trudności zadań.",
    )

    topic = st.selectbox(
        "Zakres materiału",
        options=[
            "dodawanie",
            "odejmowanie",
            "mnożenie",
            "dzielenie",
            "ułamki",
            "równania",
        ],
        index=0,
        help="Temat karty pracy (jedna operacja lub zakres na kartę).",
    )

    number_of_tasks = st.number_input(
        "Liczba zadań",
        min_value=1,
        max_value=30,
        value=5,
        step=1,
        help="Ile zadań ma zawierać karta (1–30). Dla klas 1–3 max 15.",
    )

    student_profile = st.selectbox(
        "Profil ucznia",
        options=[
            "standardowy",
            "dyskalkulia",
            "zdolny",
            "trudności w nauce",
            "ADHD",
        ],
        index=0,
        help="Profil wpływa na styl zadań, layout i ilustracje (np. dyskalkulia: prostsze liczby, większe fonty).",
    )

    include_illustration = st.checkbox(
        "Ilustracja w karcie",
        value=True,
        help="Dla profili standardowy/zdolny: jedna ilustracja u góry. Dla dyskalkulia/ADHD/trudności: ilustracja przy każdym zadaniu (zawsze włączone).",
    )

    include_answers = st.checkbox(
        "Dołącz stronę z odpowiedziami",
        value=False,
        help="Dodaje na końcu PDF stronę „Odpowiedzi” z wynikami (dla prostych działań typu a op b).",
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
            topic=topic,
            n=number_of_tasks
        )

        if result.get("_error"):
            st.warning(
                "Generowanie zadań przez API nie powiodło się (timeout lub błąd sieci). "
                "Poniżej zadania zastępcze — możesz wygenerować PDF."
            )

        # Lista zadań jako zwykły tekst
        tasks = result["tasks"]
        for i, task in enumerate(tasks, start=1):
            st.write(f"{i}. {task}")

        # ----------------------------------------------
        # PDF v0: generowanie, zapis do pliku + download
        # ----------------------------------------------
        st.divider()
        st.subheader("📄 Karta pracy PDF")

        # Metadane karty pracy
        meta = WorksheetMeta(
            title=f"Karta pracy – klasa {grade}",
            grade=str(grade),
            topic_range=topic,
            student_profile=student_profile,
        )

        # Layout sterowany AI (Day 7) – font size, spacing, kolory
        layout = None
        try:
            layout = generate_layout(
                profile=student_profile,
                grade=str(grade),
                number_of_tasks=number_of_tasks,
            )
        except Exception as e:
            st.warning(f"Layout AI niedostępny ({e}), używam domyślnego layoutu.")

        # Ilustracja (Day 8/11): per zadanie dla low-stimuli, opcjonalnie jedna u góry dla standardowy/zdolny
        image_bytes = None
        task_images = None
        low_stimuli_profiles = ["dyskalkulia", "ADHD", "trudności w nauce"]
        if student_profile in low_stimuli_profiles:
            try:
                task_images = generate_worksheet_images_for_tasks(
                    tasks=tasks, topic=topic, profile=student_profile
                )
            except Exception as e:
                st.warning(f"Grafiki per zadanie niedostępne ({e}), PDF bez ilustracji przy zadaniach.")
        elif include_illustration:
            try:
                image_bytes = generate_worksheet_image(topic=topic, profile=student_profile)
            except Exception as e:
                st.warning(f"Grafika niedostępna ({e}), PDF bez ilustracji.")

        # Odpowiedzi do klucza (v1.0) – tylko dla prostych zadań
        answers = compute_answers(tasks) if include_answers else None

        # 1) Generowanie PDF (z layoutem, opcjonalnie image_bytes, task_images, answers)
        pdf_bytes = build_worksheet_pdf_bytes(
            meta=meta,
            tasks=tasks,
            layout=layout,
            image_bytes=image_bytes,
            task_images=task_images,
            answers=answers,
        )

        # 2) Zapis do pliku (wariant A)
        output_dir = ROOT_DIR / "data" / "out"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "worksheet.pdf"

        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

        st.caption(f"Plik zapisany w: **{output_path.relative_to(ROOT_DIR)}**")

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
