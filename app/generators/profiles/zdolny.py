# profiles/zdolny.py

# --------------------------------------------------
# PROFIL UCZNIA ZDOLNEGO (MATMA)
# --------------------------------------------------
# Założenia dydaktyczne:
# Uczeń:
# - szybko opanowuje materiał i nudzi się przy zbyt łatwych zadaniach
# - lubi wyzwania i zadania wieloetapowe
# - radzi sobie z większymi liczbami i prostymi łańcuchami operacji
# --------------------------------------------------

from .base import StudentProfile


class ZdolnyProfile(StudentProfile):
    id = "zdolny"
    display_name = "zdolny"
    ui_label = "Zdolny"
    ui_summary = "Nieco trudniejsze zadania i więcej treści na stronie."
    illustration_mode = "header"
    description = (
        "Uczeń zdolny – potrzebuje większych wyzwań, "
        "może rozwiązywać zadania wieloetapowe."
    )

    rules = [
        "Stawiaj większe wyzwania – nie upraszczaj poniżej poziomu klasy.",
        "Możesz wprowadzić zadanie wieloetapowe lub prosty łańcuch operacji.",
        "Zachęcaj do uzasadnienia odpowiedzi (dlaczego tak?).",
        "Pokazuj alternatywne sposoby rozwiązania.",
        "Nie zarzucaj nadmiarem teorii – zadanie ma być ciekawe, nie przegadane.",
    ]

    is_low_stimuli = False

    task_instruction = (
        "Nieco trudniejsze liczby (można do 50), opcjonalnie dwa kroki "
        'lub prosty łańcuch (np. "Policz: 2 + 3, wynik pomnóż przez 2 = ____").'
    )

    task_examples = (
        "Przykłady dla zdolny:\n"
        "- Policz: 15 + 23 = ____\n"
        "- Policz: 45 − 18 = ____\n"
        "- Policz: 2 + 3, wynik pomnóż przez 4 = ____"
    )

    layout_overrides = {
        # Zdolny: trochę mniejszy task_font, więcej treści na stronę.
        "task_font_size": 11,
        "line_spacing": 14,
        "task_spacing": 6,
    }
