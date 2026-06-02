# profiles/standardowy.py

# --------------------------------------------------
# PROFIL UCZNIA STANDARDOWEGO (MATMA)
# --------------------------------------------------
# Domyślny profil – uczeń bez zdiagnozowanych specjalnych potrzeb.
# --------------------------------------------------

from .base import StudentProfile


class StandardowyProfile(StudentProfile):
    id = "standardowy"
    display_name = "standardowy"
    ui_label = "Standardowy"
    ui_summary = "Typowy poziom klasy — bez dodatkowych uproszczeń."
    illustration_mode = "header"
    description = "Uczeń bez specjalnych potrzeb – standardowy poziom klasy."

    rules = [
        "Tłumacz jasno i zwięźle, dostosowując poziom do klasy.",
        "Nie upraszczaj nadmiernie, ale nie komplikuj bez powodu.",
        "Pokazuj typowy sposób rozwiązania, jeden na raz.",
    ]

    is_low_stimuli = False

    task_instruction = "Standardowe zadania dla klasy, odpowiednie do poziomu."

    task_examples = (
        "Przykłady dla standardowy:\n"
        "- Policz: 7 + 8 = ____\n"
        "- Policz: 15 − 6 = ____\n"
        "- Policz: 4 × 3 = ____"
    )

    # Brak nadpisań – używamy domyślnego layoutu z PDF generatora.
    layout_overrides = None
