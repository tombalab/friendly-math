# profiles/dysleksja.py

# --------------------------------------------------
# PROFIL UCZNIA Z DYSLEKSJĄ (MATMA)
# --------------------------------------------------
# Założenia dydaktyczne:
# Uczeń:
# - ma trudność z dekodowaniem tekstu (litery, długie polecenia)
# - łatwiej rozumie krótkie, zwięzłe instrukcje
# - pomaga konsekwentny układ i unikanie zbitek tekstu
# - czytelna typografia (większe odstępy, prosta czcionka) zmniejsza obciążenie
# --------------------------------------------------
# Uwaga: dysleksja ≠ dyskalkulia. Trudność leży po stronie *tekstu* polecenia,
# a nie liczby. Liczby mogą być normalne dla klasy, ale polecenie ma być krótkie.
# --------------------------------------------------

from .base import StudentProfile


class DysleksjaProfile(StudentProfile):
    id = "dysleksja"
    display_name = "dysleksja"
    ui_label = "Dysleksja"
    ui_summary = "Krótkie polecenia i czytelny układ; poziom liczb jak w klasie."
    illustration_mode = "header"
    description = (
        "Uczeń z dysleksją – potrzebuje krótkich poleceń i czytelnej typografii. "
        "Trudności dotyczą dekodowania tekstu, nie samej matematyki."
    )

    rules = [
        "Używaj krótkich, prostych poleceń (max 1 zdanie).",
        "Unikaj zbitek tekstu i długich akapitów.",
        "Stosuj wyraźną strukturę wizualną (listy, oddzielne linie).",
        "Nie używaj synonimów dla tych samych pojęć w jednym zadaniu.",
        "JEŚLI używasz nowego słowa – wyjaśnij je raz, prosto.",
        "Liczby mogą być normalne dla klasy – nie upraszczaj samej matematyki.",
    ]

    # Dysleksja nie jest klasycznym low-stimuli (jak ADHD/dyskalkulia),
    # ale korzysta z większego line_spacing i trochę większej czcionki.
    # Nie wymuszamy szarego tła – białe tło jest najczytelniejsze do druku.
    is_low_stimuli = False

    task_instruction = (
        "Krótkie polecenia (max 1 zdanie), czytelne liczby (zgodne z klasą), "
        "prosty, powtarzalny format zadania."
    )

    task_examples = (
        "Przykłady dla dysleksja:\n"
        "- Policz: 5 + 6 = ____\n"
        "- Policz: 12 − 5 = ____\n"
        "- Policz: 8 + 4 = ____"
    )

    layout_overrides = {
        "task_font_size": 13,
        "line_spacing": 22,
        "task_spacing": 12,
        "section_spacing": 20,
        "text_color": "#111111",
        "background_color": "#FFFFFF",
    }
