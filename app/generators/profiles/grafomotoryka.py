from .base import StudentProfile


class GrafomotorykaProfile(StudentProfile):
    id = "trudności grafomotoryczne"
    display_name = "trudności grafomotoryczne"
    ui_label = "Trudności grafomotoryczne"
    ui_summary = "Mniej pisania, duże pola odpowiedzi, więcej zaznaczania i wyboru."
    illustration_mode = "per_task"
    description = (
        "Uczeń z trudnościami grafomotorycznymi - potrzebuje ograniczenia pisania "
        "oraz dużych, czytelnych pól odpowiedzi."
    )

    rules = [
        "Ogranicz konieczność ręcznego zapisu.",
        "Preferuj zaznaczanie, łączenie i wybór odpowiedzi.",
        "Dawaj bardzo duże pola odpowiedzi.",
        "Nie wymagaj przepisywania długich treści.",
        "Utrzymuj duże odstępy między elementami.",
    ]

    is_low_stimuli = True

    task_instruction = (
        "Krótkie polecenia, mało pisania, odpowiedzi przez zaznaczenie, wybór "
        "lub wpisanie pojedynczej liczby."
    )

    task_examples = (
        "Przykłady dla trudności grafomotorycznych:\n"
        "- Policz: 4 + 2 = ____\n"
        "- Zaznacz wynik: 6, 7, 8\n"
        "- Połącz działanie z wynikiem."
    )

    layout_overrides = {
        "title_font_size": 21,
        "metadata_font_size": 12,
        "section_font_size": 15,
        "task_font_size": 15,
        "margin": 64,
        "title_spacing": 32,
        "metadata_spacing": 26,
        "section_spacing": 26,
        "task_spacing": 18,
        "line_spacing": 24,
        "workspace_lines": 1,
        "workspace_line_gap": 28,
        "background_color": "#fbfbf8",
    }
