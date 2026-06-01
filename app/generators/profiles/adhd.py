# profiles/adhd.py

# --------------------------------------------------
# PROFIL UCZNIA Z ADHD (MATMA)
# --------------------------------------------------
# Założenia dydaktyczne:
# Uczeń:
# - szybko traci uwagę
# - potrzebuje krótkich bloków informacji
# - lubi jasną strukturę
# - reaguje dobrze na „interakcję"
# --------------------------------------------------

from .base import StudentProfile


class ADHDProfile(StudentProfile):
    id = "ADHD"
    display_name = "ADHD"
    ui_label = "ADHD"
    ui_summary = "Krótkie, jednoetapowe zadania; ilustracja przy zadaniu (gdy włączona)."
    illustration_mode = "per_task"
    description = "Uczeń z ADHD – potrzebuje krótkich, dynamicznych wyjaśnień."

    rules = [
        "Dziel wyjaśnienia na bardzo krótkie sekcje.",
        "Stosuj listy punktowane i numerowane kroki.",
        "Często angażuj ucznia pytaniami kontrolnymi.",
        "Unikaj długich akapitów tekstu.",
        "Wyraźnie zaznacz, co jest najważniejsze.",
        "Utrzymuj prosty, energiczny styl wypowiedzi.",
        "ŻADNA sekcja nie może mieć więcej niż 3 zdania.",
        "Po każdym etapie zadaj jedno krótkie pytanie.",
    ]

    is_low_stimuli = True

    task_instruction = (
        "Krótkie polecenia (max 1 zdanie), jedna operacja na zadanie, "
        'wyraźny format "Policz: X op Y = ____", bez dodatkowych informacji.'
    )

    task_examples = (
        "Przykłady dla ADHD:\n"
        "- Policz: 6 + 3 = ____\n"
        "- Policz: 9 − 4 = ____\n"
        "- Policz: 2 × 5 = ____"
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
