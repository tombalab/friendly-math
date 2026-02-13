#--------------------------------------------------
# FRIENDLY MATH - v1
# Generator kart pracy matematyki dla uczniów szkoły podstawowej
#--------------------------------------------------
#
# Autor: Tomasz Balabuch
# Data: 2026-01-13
# Wersja: 1.0.0
#
#--------------------------------------------------
# --------------------------------------------------

# --------------------------------------------------
# Importy
# --------------------------------------------------

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from app.ai.layout_generator import generate_layout
from app.ai.text_generator import generate_tasks
from app.generators.images import generate_worksheet_image, generate_worksheet_images_for_tasks
from app.pdf.generator import WorksheetMeta, build_worksheet_pdf_bytes

# --------------------------------------------------
# Konfiguracja strony
# --------------------------------------------------
st.set_page_config(
    page_title="Friendly Math",
    layout="centered"
)

# Nagłówek
# --------------------------------------------------
st.title("🧮 Friendly Math")
st.subheader("Generator kart pracy (MVP)")

st.write(
    "Wypełnij formularz i wygeneruj JSON request, "
    "który w kolejnym etapie zostanie wysłany do AI."
)

# --------------------------------------------------
# Formularz
# --------------------------------------------------
with st.form("worksheet_form"):

    grade = st.selectbox(
        "Klasa",
        options=["1", "2", "3", "4", "5", "6", "7", "8"],
        help="Wybierz klasę ucznia"
    )

    topic = st.selectbox(
        "Zakres materiału",
        options=[
            "dodawanie",
            "odejmowanie",
            "mnożenie",
            "dzielenie",
            "ułamki",
            "równania"
        ],
        help="Zakres tematyczny karty pracy"
    )

    number_of_tasks = st.number_input(
        "Liczba zadań",
        min_value=1,
        max_value=30,
        value=10,
        step=1,
        help="Ile zadań ma zawierać karta pracy"
    )

    student_profile = st.selectbox(
        "Profil ucznia",
        options=[
            "standardowy",
            "dyskalkulia",
            "zdolny",
            "trudności w nauce",
            "ADHD"
        ],
        help="Profil wpływa na styl i trudność zadań"
    )

    # Day 11: dla standardowy/zdolny – opcja ilustracji; dla dyskalkulia/ADHD/trudności zawsze per zadanie
    include_illustration = st.checkbox(
        "Ilustracja w karcie",
        value=True,
        help="Dla profili standardowy/zdolny: jedna ilustracja u góry. Dla dyskalkulia/ADHD/trudności: ilustracja przy każdym zadaniu (zawsze włączone).",
    )

    submitted = st.form_submit_button("🧠 Generuj kartę")

# --------------------------------------------------
# Logika po wysłaniu formularza
# --------------------------------------------------
if submitted:

    # Prosta walidacja biznesowa
    if int(grade) <= 3 and number_of_tasks > 15:
        st.error("Dla klas 1–3 maksymalna liczba zadań to 15.")
    else:
        request_payload = {
            "grade": int(grade),
            "topic": topic,
            "number_of_tasks": number_of_tasks,
            "student_profile": student_profile
        }

        st.success("✅ JSON request wygenerowany")
        st.json(request_payload)

        st.info(
            "Ten JSON będzie w kolejnym kroku wysyłany do API "
            "generującego zadania."
        )
        
        st.divider()
        st.subheader("📘 Wygenerowane zadania (MVP)")

        result = generate_tasks(
            profile=student_profile,
            grade=grade,
            topic=topic,
            n=number_of_tasks
        )

        # Lista zadań jako zwykły tekst
        tasks = result["tasks"]
        for i, task in enumerate(tasks, start=1):
            st.write(f"{i}. {task}")

        # ----------------------------------------------
        # PDF v0: generowanie, zapis do pliku + download
        # ----------------------------------------------
        st.divider()
        st.subheader("📄 PDF v0")

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

        # 1) Generowanie PDF (z layoutem, opcjonalnie image_bytes lub task_images)
        pdf_bytes = build_worksheet_pdf_bytes(
            meta=meta,
            tasks=tasks,
            layout=layout,
            image_bytes=image_bytes,
            task_images=task_images,
        )

        # 2) Zapis do pliku (wariant A)
        output_dir = ROOT_DIR / "data" / "out"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "worksheet.pdf"

        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

        st.write(
            f"📁 PDF zapisany jako: "
            f"`{output_path.relative_to(ROOT_DIR)}`"
        )

        # 3) Przycisk pobierania (wariant B)
        st.download_button(
            label="⬇️ Pobierz PDF",
            data=pdf_bytes,
            file_name="worksheet.pdf",
            mime="application/pdf",
        )
