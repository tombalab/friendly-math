# profiles/trudnosci.py

# --------------------------------------------------
# PROFIL UCZNIA Z TRUDNOŚCIAMI W NAUCE (MATMA)
# --------------------------------------------------
# Założenia dydaktyczne:
# Uczeń:
# - wolniejsze tempo przyswajania
# - potrzebuje powtórzeń i prostych przykładów
# - dużo „białego" miejsca i czytelnego layoutu pomaga
# --------------------------------------------------

from .base import StudentProfile


class TrudnosciProfile(StudentProfile):
    id = "trudności w nauce"
    display_name = "trudności w nauce"
    ui_label = "Trudności w nauce"
    ui_summary = "Wolniejsze tempo, prostsze liczby; ilustracja przy zadaniu (gdy włączona)."
    illustration_mode = "per_task"
    description = (
        "Uczeń z ogólnymi trudnościami w nauce – wolniejsze tempo, "
        "potrzebuje prostych liczb i czytelnego layoutu."
    )

    rules = [
        "Używaj prostych liczb i krótkich poleceń.",
        "Powtarzaj kluczowe pojęcia – nie zakładaj, że uczeń je pamięta.",
        "Pokazuj wynik na konkretnym przykładzie, dopiero potem ogólnie.",
        "Daj uczniowi czas – nie spiesz się z kolejnym pojęciem.",
        "Chwal mikropostępy.",
    ]

    is_low_stimuli = True

    task_instruction = (
        "Proste liczby (1-15), krótkie polecenia, jeden krok, "
        "dużo miejsca na odpowiedź."
    )

    task_examples = (
        "Przykłady dla trudności w nauce:\n"
        "- Policz: 4 + 5 = ____\n"
        "- Policz: 10 − 3 = ____\n"
        "- Policz: 7 + 2 = ____"
    )

    layout_overrides = {
        "title_font_size": 20,
        "metadata_font_size": 12,
        "section_font_size": 14,
        "task_font_size": 14,
        "margin": 60,
        "title_spacing": 32,
        "metadata_spacing": 26,
        "section_spacing": 24,
        "task_spacing": 14,
        "line_spacing": 20,
        "background_color": "#fafafa",
    }
