import json
import os
from dotenv import load_dotenv
from openai import OpenAI

# Ładowanie zmiennych z .env
load_dotenv()

# Inicjalizacja klienta OpenAI (używamy tego samego co w text_generator)
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
    Generuje layout JSON dla PDF używając OpenAI API.
    Day 7: layout sterowany AI (font size, spacing, kolory).
    
    Zwraca dict z kluczami:
    - title_font_size: int
    - metadata_font_size: int
    - section_font_size: int
    - task_font_size: int
    - margin: int
    - title_spacing: int (odstęp po tytule)
    - metadata_spacing: int
    - section_spacing: int
    - task_spacing: int (odstęp między zadaniami)
    - line_spacing: int (odstęp między liniami w zadaniu)
    - text_color: str (hex, np. "#000000")
    - background_color: str (hex, np. "#FFFFFF")
    """
    try:
        client = _get_client()
        
        # Prompt dla generowania layoutu
        prompt = f"""Jesteś ekspertem od layoutu edukacyjnych kart pracy dla uczniów z trudnościami w nauce.

Wygeneruj layout JSON dla karty pracy matematyki:
- Profil ucznia: {profile}
- Klasa: {grade}
- Liczba zadań: {number_of_tasks}

Wymagania:
- Dla dyskalkulia/ADHD: większe fonty (14-18px), większe odstępy, wysoki kontrast
- Dla standardowy: standardowe fonty (11-14px)
- Dla zdolny: mniejsze fonty (10-12px), więcej treści na stronę
- Kolory: czarny tekst na białym tle (lub bardzo jasny pastelowy tło dla low-stimuli)
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
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Jesteś ekspertem od layoutu edukacyjnych materiałów. Zwracasz tylko poprawny JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Niższa temperatura dla bardziej przewidywalnych wyników
            max_tokens=300
        )
        
        # Parsowanie JSON
        layout_text = response.choices[0].message.content.strip()
        # Usuń markdown code blocks jeśli są
        if layout_text.startswith("```"):
            layout_text = layout_text.split("```")[1]
            if layout_text.startswith("json"):
                layout_text = layout_text[4:]
        layout_text = layout_text.strip()

        layout = json.loads(layout_text)
        
        # Walidacja i fallback wartości
        return _validate_layout(layout, profile, grade)
    
    except Exception as e:
        # Fallback na domyślny layout jeśli API nie działa
        print(f"⚠️ Error generating layout: {e}. Using default layout.")
        return _get_default_layout(profile, grade)


def _validate_layout(layout: dict, profile: str, grade: str) -> dict:
    """Waliduje i poprawia wartości layoutu."""
    defaults = {
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

    if profile in ["dyskalkulia", "ADHD", "trudności w nauce"]:
        defaults["title_font_size"] = 20
        defaults["metadata_font_size"] = 12
        defaults["section_font_size"] = 14
        defaults["task_font_size"] = 14
        defaults["margin"] = 60
        defaults["title_spacing"] = 32
        defaults["metadata_spacing"] = 26
        defaults["section_spacing"] = 24
        defaults["task_spacing"] = 14
        defaults["line_spacing"] = 20

    if int(grade) <= 3:
        defaults["task_font_size"] = max(defaults["task_font_size"], 12)
        defaults["margin"] = max(defaults["margin"], 55)

    numeric_keys = [
        "title_font_size", "metadata_font_size", "section_font_size", "task_font_size",
        "margin", "title_spacing", "metadata_spacing", "section_spacing",
        "task_spacing", "line_spacing",
    ]

    for key, default_value in defaults.items():
        if key not in layout:
            layout[key] = default_value
        elif key in numeric_keys:
            try:
                layout[key] = int(float(layout[key]))
            except (TypeError, ValueError):
                layout[key] = default_value

    # Dla dyskalkulia/ADHD/trudności – wymuszamy większe fonty i odstępy (profil ma pierwszeństwo nad AI)
    if profile in ["dyskalkulia", "ADHD", "trudności w nauce"]:
        for key in ["title_font_size", "metadata_font_size", "section_font_size", "task_font_size",
                    "margin", "title_spacing", "metadata_spacing", "section_spacing",
                    "task_spacing", "line_spacing"]:
            layout[key] = defaults[key]

    return layout


def _get_default_layout(profile: str, grade: str) -> dict:
    """Zwraca domyślny layout bez użycia AI."""
    return _validate_layout({}, profile, grade)