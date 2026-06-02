# profiles/base.py
# Każdy profil dziedziczy po tej klasie i wystawia dane potrzebne
# generatorowi tekstu (text_generator) i layoutu (layout_generator).

from __future__ import annotations

from typing import Literal, Optional

IllustrationMode = Literal["header", "per_task"]


class StudentProfile:
    """
    Bazowy profil PPP (Pupil Profile Preset).

    Pola:
    - id: stabilny identyfikator profilu (zgodny z tym, co przesyła UI).
    - display_name: nazwa do wyświetlenia (np. w UI/PDF). Domyślnie = id.
    - description: krótki opis profilu (do system promptu czatu).
    - rules: zasady pracy z uczniem (do system promptu czatu).
    - is_low_stimuli: True dla profili wymagających większych fontów,
      jasnego tła i upraszczania bodźców (dyskalkulia, ADHD, trudności).
    - task_instruction: krótka instrukcja stylu zadań (do prompta do generowania zadań).
    - task_examples: kilka przykładów zadań dla danego profilu (few-shot).
    - layout_overrides: opcjonalny słownik nadpisujący domyślny layout PDF.
    - ui_label: nazwa w selectboxie Streamlit (bez diagnozy klinicznej).
    - ui_summary: jedno zdanie pomocy dla nauczyciela.
    - ui_visible: czy profil jest dostępny w UI.
    - illustration_mode: „header" (jedna ilustracja u góry) lub „per_task".
    """

    id: str = "base"
    display_name: str = "base"
    ui_label: str = ""
    ui_summary: str = ""
    ui_visible: bool = True
    illustration_mode: IllustrationMode = "header"
    description: str = ""
    rules: list[str] = []

    is_low_stimuli: bool = False
    task_instruction: str = "Standardowe zadania, odpowiednie do poziomu klasy."
    task_examples: str = ""
    layout_overrides: Optional[dict] = None

    def render_rules(self) -> str:
        return "\n".join(f"- {rule}" for rule in self.rules)

    @property
    def name(self) -> str:
        # Wsteczna kompatybilność: stary kod używał `profile.name`.
        return self.id

    @property
    def label_for_ui(self) -> str:
        return self.ui_label or self.display_name or self.id

    @property
    def label_for_pdf(self) -> str:
        return self.ui_label or self.display_name or self.id
