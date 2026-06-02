# profiles/dyskalkulia.py

# --------------------------------------------------
# PROFIL UCZNIA Z DYSKALKULIĄ (MATMA)
# --------------------------------------------------
# Założenia dydaktyczne:
# Uczeń:
# - ma trudność z liczbami i symbolami
# - łatwiej rozumie język naturalny i metafory
# - potrzebuje mikrokroków
# - łatwo się gubi przy „przeskokach"
# --------------------------------------------------

from .base import StudentProfile


class DyskalkuliaProfile(StudentProfile):
    id = "dyskalkulia"
    display_name = "dyskalkulia"
    ui_label = "Dyskalkulia"
    ui_summary = "Prostsze liczby, większe odstępy, ilustracja przy każdym zadaniu (gdy włączona)."
    illustration_mode = "per_task"
    description = "Uczeń z trudnościami w rozumieniu liczb i symboli matematycznych."

    rules = [
        "Tłumacz bardzo wolno i krok po kroku.",
        "Unikaj skrótów myślowych i przeskoków.",
        "Używaj języka naturalnego zamiast symboli, jeśli to możliwe.",
        "Stosuj analogie z życia codziennego.",
        "Po każdym kroku krótko podsumuj, co zostało zrobione.",
        "Nie zakładaj, że uczeń pamięta poprzednie pojęcia.",
        "NIE używaj więcej niż jednego nowego pojęcia naraz.",
        "JEŚLI używasz symbolu matematycznego – natychmiast wyjaśnij go słowami.",
    ]

    is_low_stimuli = True

    task_instruction = (
        "Używaj bardzo prostych liczb (1-12), jeden krok na raz, "
        "język naturalny obok symboli, unikaj długich poleceń."
    )

    task_examples = (
        "Przykłady dla dyskalkulia:\n"
        "- Policz: 3 + 4 = ____\n"
        "- Policz: 8 − 2 = ____\n"
        "- Policz: 5 + 1 = ____"
    )

    layout_overrides = {
        "title_font_size": 20,
        "metadata_font_size": 12,
        "section_font_size": 14,
        "task_font_size": 14,
        "margin": 64,
        "title_spacing": 32,
        "metadata_spacing": 26,
        "section_spacing": 26,
        "task_spacing": 16,
        "line_spacing": 22,
        "workspace_lines": 5,
        "workspace_line_gap": 22,
        "background_color": "#f8f8f5",
    }
