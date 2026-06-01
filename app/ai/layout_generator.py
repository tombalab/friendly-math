import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from app.generators.profiles.registry import get_profile

load_dotenv()

# v1.0: model i parametry layoutu w jednym miejscu.
_MODEL = "gpt-4o-mini"
_TEMPERATURE = 0.3
_MAX_TOKENS = 2000

_client = None


def _get_client():
    """Lazy initialization OpenAI client."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY nie znaleziony w .env. "
                "Sprawdź czy masz plik .env z kluczem API."
            )
        _client = OpenAI(api_key=api_key)
    return _client


def generate_layout(profile: str, grade: str, number_of_tasks: int) -> dict:
    """
    Generuje layout JSON dla PDF.
    
    Dla profili low-stimuli (dyskalkulia, ADHD, trudności w nauce) pomijamy
    wywołanie OpenAI – ich layout jest twardo zdefiniowany w klasie profilu
    (i tak nadpisywaliśmy odpowiedź AI w `_validate_layout`). Mniej kosztu, mniej źródeł błędu.
    """
    student_profile = get_profile(profile)

    # Skrót dla low-stimuli: bierzemy nadpisania prosto z klasy profilu.
    if student_profile.is_low_stimuli:
        return _build_layout_from_profile(student_profile, grade)

    try:
        client = _get_client()

        prompt = f"""Jesteś ekspertem od layoutu edukacyjnych kart pracy dla uczniów z trudnościami w nauce.

Wygeneruj layout JSON dla karty pracy matematyki:
- Profil ucznia: {profile}
- Klasa: {grade}
- Liczba zadań: {number_of_tasks}

Wymagania:
- Dla standardowy: standardowe fonty (11-14px)
- Dla zdolny: mniejsze fonty (10-12px), więcej treści na stronę
- Dla dysleksja: większy line_spacing (16-20px), task_font_size 12-14
- Kolory: czarny tekst na białym tle
- Marginesy: 40-60px (większe dla młodszych klas)

Zwróć TYLKO JSON w formacie:
{{
    "title_font_size": 18,
    "metadata_font_size": 10,
    "section_font_size": 12,
    "task_font_size": 13,
    "margin": 50,
    "title_spacing": 30,
    "metadata_spacing": 20,
    "section_spacing": 18,
    "task_spacing": 8,
    "line_spacing": 16,
    "text_color": "#000000",
    "background_color": "#FFFFFF"
}}

Tylko JSON, bez dodatkowych komentarzy."""

        response = client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": "Jesteś ekspertem od layoutu edukacyjnych materiałów. Zwracasz tylko poprawny JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=_TEMPERATURE,
            max_completion_tokens=_MAX_TOKENS,
        )

        layout_text = response.choices[0].message.content.strip()
        if layout_text.startswith("```"):
            layout_text = layout_text.split("```")[1]
            if layout_text.startswith("json"):
                layout_text = layout_text[4:]
        layout_text = layout_text.strip()

        layout = json.loads(layout_text)
        return _validate_layout(layout, student_profile, grade)

    except Exception as e:
        print(f"⚠️ Error generating layout: {e}. Using profile-default layout.")
        return _build_layout_from_profile(student_profile, grade)


# --------------------------------------------------------------------
# Helpery layoutu
# --------------------------------------------------------------------


def _base_defaults() -> dict:
    return {
        "title_font_size": 16,
        "metadata_font_size": 10,
        "section_font_size": 12,
        "task_font_size": 11,
        "margin": 50,
        "title_spacing": 24,
        "metadata_spacing": 20,
        "section_spacing": 18,
        "task_spacing": 6,
        "line_spacing": 14,
        "text_color": "#000000",
        "background_color": "#FFFFFF",
    }


def _apply_grade_constraints(layout: dict, grade: str) -> dict:
    """Klasy 1-3: nieco większy task_font i margines (czytelność dla młodszych)."""
    try:
        grade_int = int(grade)
    except (TypeError, ValueError):
        return layout
    if grade_int <= 3:
        layout["task_font_size"] = max(layout.get("task_font_size", 11), 12)
        layout["margin"] = max(layout.get("margin", 50), 55)
    return layout


def _build_layout_from_profile(profile, grade: str) -> dict:
    """Layout zbudowany z domyślnych + nadpisań z klasy profilu (bez API)."""
    layout = _base_defaults()
    if profile.layout_overrides:
        layout.update(profile.layout_overrides)
    return _apply_grade_constraints(layout, grade)


def _validate_layout(layout: dict, profile, grade: str) -> dict:
    """
    Waliduje wartości layoutu z AI: poprawia typy, uzupełnia braki,
    dla profili z `layout_overrides` wymusza wartości z profilu (profil > AI).
    """
    defaults = _base_defaults()
    if profile.layout_overrides:
        defaults.update(profile.layout_overrides)
    defaults = _apply_grade_constraints(defaults, grade)

    numeric_keys = {
        "title_font_size", "metadata_font_size", "section_font_size", "task_font_size",
        "margin", "title_spacing", "metadata_spacing", "section_spacing",
        "task_spacing", "line_spacing",
    }

    for key, default_value in defaults.items():
        if key not in layout:
            layout[key] = default_value
        elif key in numeric_keys:
            try:
                layout[key] = int(float(layout[key]))
            except (TypeError, ValueError):
                layout[key] = default_value

    # Profil ma pierwszeństwo nad AI dla swoich nadpisań.
    if profile.layout_overrides:
        for key in profile.layout_overrides:
            layout[key] = defaults[key]

    return layout


def _get_default_layout(profile: str, grade: str) -> dict:
    """Wsteczna kompatybilność: zwraca domyślny layout dla profilu (bez AI)."""
    return _build_layout_from_profile(get_profile(profile), grade)
