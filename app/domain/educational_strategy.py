"""Profile-first worksheet strategy and expanded layout schema."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from app.domain.profile_catalog import ResolvedProfile
from app.domain.profile_pedagogy import get_pedagogy_spec
from app.domain.topic_catalog import ResolvedTopic, visual_family_for_topic

ActivityType = Literal["compute", "match", "color", "choice", "puzzle", "trace", "reflect"]
AnswerMode = Literal["write", "large_write", "checkbox", "circle", "connect", "color"]
Difficulty = Literal["warmup", "core", "challenge", "summary"]


@dataclass(frozen=True)
class VisualThemeSpec:
    family: str
    motif: str
    learning_role_pl: str
    prompt_pl: str


@dataclass(frozen=True)
class WorksheetTemplate:
    template_id: str
    name_pl: str
    accent_color: str
    soft_color: str
    border_color: str
    header_label: str
    footer_label: str
    icon_kind: str
    motif_label: str
    pattern: str


@dataclass(frozen=True)
class StrategySpec:
    profile_id: str
    profile_group: str
    short_goal_pl: str
    allowed_activity_types: tuple[ActivityType, ...]
    preferred_answer_modes: tuple[AnswerMode, ...]
    progress_markers: bool
    visual_cues: tuple[str, ...]
    max_tasks_per_section: int
    cognitive_load_note_pl: str


@dataclass(frozen=True)
class WorksheetBlock:
    block_id: str
    task_index: int | None
    title: str
    task_text: str
    activity_type: ActivityType
    answer_mode: AnswerMode
    difficulty: Difficulty
    visual_cue: str
    answer_box_lines: int
    progress_label: str = ""
    instructions: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorksheetSection:
    section_id: str
    title: str
    purpose_pl: str
    blocks: tuple[WorksheetBlock, ...]
    spacing_after: int = 16


@dataclass(frozen=True)
class WorksheetPlan:
    template: WorksheetTemplate
    strategy: StrategySpec
    visual_theme: VisualThemeSpec
    sections: tuple[WorksheetSection, ...]

    def to_layout_json(self) -> dict:
        """Machine-readable expanded JSON schema used by PDF and diagnostics."""
        return {
            "template": self.template.__dict__,
            "strategy": {
                "profile_id": self.strategy.profile_id,
                "profile_group": self.strategy.profile_group,
                "activity_types": list(self.strategy.allowed_activity_types),
                "answer_modes": list(self.strategy.preferred_answer_modes),
                "progress_markers": self.strategy.progress_markers,
                "visual_cues": list(self.strategy.visual_cues),
                "cognitive_load_note_pl": self.strategy.cognitive_load_note_pl,
            },
            "visual_theme": self.visual_theme.__dict__,
            "sections": [
                {
                    "section_id": s.section_id,
                    "title": s.title,
                    "purpose_pl": s.purpose_pl,
                    "spacing_after": s.spacing_after,
                    "blocks": [
                        {
                            "block_id": b.block_id,
                            "task_index": b.task_index,
                            "title": b.title,
                            "task_text": b.task_text,
                            "activity_type": b.activity_type,
                            "answer_mode": b.answer_mode,
                            "difficulty": b.difficulty,
                            "visual_cue": b.visual_cue,
                            "answer_box_lines": b.answer_box_lines,
                            "progress_label": b.progress_label,
                            "instructions": list(b.instructions),
                        }
                        for b in s.blocks
                    ],
                }
                for s in self.sections
            ],
        }


_TEMPLATES: dict[str, WorksheetTemplate] = {
    "classic": WorksheetTemplate(
        "classic",
        "Klasyczny",
        "#3f51b5",
        "#eef1ff",
        "#c7cffc",
        "Karta pracy",
        "Friendly Math",
        "book",
        "porządek i czytelne kroki",
        "rule_lines",
    ),
    "adventure": WorksheetTemplate(
        "adventure",
        "Przygoda",
        "#2e7d32",
        "#edf7ed",
        "#b8ddb8",
        "Misja matematyczna",
        "Kolejny krok",
        "compass",
        "ścieżka z kolejnymi etapami",
        "trail",
    ),
    "space": WorksheetTemplate(
        "space",
        "Kosmos",
        "#4a3f8f",
        "#f1efff",
        "#cbc4f7",
        "Lot po liczby",
        "Baza Friendly Math",
        "rocket",
        "krótkie misje i stacje postępu",
        "stars",
    ),
    "detective": WorksheetTemplate(
        "detective",
        "Detektyw Matematyczny",
        "#795548",
        "#fff4e8",
        "#e0c6aa",
        "Sprawa do rozwiązania",
        "Notatnik detektywa",
        "magnifier",
        "tropy, dowody i sprawdzanie wyniku",
        "clues",
    ),
    "friendly_minimal": WorksheetTemplate(
        "friendly_minimal",
        "Friendly Minimal",
        "#546e7a",
        "#f7f9fa",
        "#d9e1e5",
        "Spokojna karta",
        "Mały sukces",
        "smile",
        "minimum bodźców i dużo oddechu",
        "none",
    ),
}


_VISUAL_THEMES: dict[str, VisualThemeSpec] = {
    "dodawanie": VisualThemeSpec(
        "dodawanie",
        "jabłka, balony i zabawki w dwóch grupach",
        "Pokazuje łączenie dwóch ilości w jedną całość.",
        "Dwie wyraźne grupy przedmiotów, znak plus między grupami, bez dekoracji w tle.",
    ),
    "odejmowanie": VisualThemeSpec(
        "odejmowanie",
        "ciastka lub obiekty przekreślone/odjęte",
        "Pokazuje, co znika albo zostaje zabrane.",
        "Rząd obiektów, część przekreślona lub oddzielona, wynik widoczny jako pozostałe obiekty.",
    ),
    "mnożenie": VisualThemeSpec(
        "mnożenie",
        "równe grupy lub tablica elementów",
        "Buduje rozumienie mnożenia jako równych grup.",
        "Układ wiersze razy kolumny, równe odstępy, mało kolorów.",
    ),
    "dzielenie": VisualThemeSpec(
        "dzielenie",
        "przedmioty rozdzielone na równe grupy",
        "Pokazuje sprawiedliwy podział i liczebność każdej grupy.",
        "Kilka wyraźnych grup z taką samą liczbą elementów.",
    ),
    "ułamki": VisualThemeSpec(
        "ułamki",
        "pizza, czekolada albo figura podzielona na części",
        "Łączy zapis ułamka z częścią całości.",
        "Jedna figura podzielona na równe części, zaznaczony licznik, podpis mianownika.",
    ),
    "pieniądze": VisualThemeSpec(
        "pieniądze",
        "monety i banknoty",
        "Pomaga przeliczać kwoty na konkretnych nominałach.",
        "Monety lub banknoty ułożone w grupy odpowiadające kwotom z zadania.",
    ),
    "czas": VisualThemeSpec(
        "czas",
        "czytelny zegar analogowy",
        "Wspiera odczytywanie godzin z położenia wskazówek.",
        "Duży zegar z wyraźnymi wskazówkami i bez dodatkowych ozdobników.",
    ),
    "obwody": VisualThemeSpec(
        "obwody",
        "figura z oznaczonymi bokami",
        "Pokazuje, które odcinki trzeba zsumować.",
        "Prosta figura geometryczna z podpisanymi bokami bez tła dekoracyjnego.",
    ),
    "default": VisualThemeSpec(
        "default",
        "proste elementy matematyczne",
        "Porządkuje uwagę ucznia wokół treści zadania.",
        "Minimalna ilustracja bez dekoracji, związana bezpośrednio z poleceniem.",
    ),
}


def available_templates() -> dict[str, str]:
    return {key: value.name_pl for key, value in _TEMPLATES.items()}


def resolve_template(template_id: str | None, *, profile_group: str = "", topic_id: str = "") -> WorksheetTemplate:
    if template_id and template_id in _TEMPLATES:
        return _TEMPLATES[template_id]
    if profile_group == "dyskalkulia":
        return _TEMPLATES["friendly_minimal"]
    if profile_group == "adhd":
        return _TEMPLATES["space" if topic_id == "czas" else "adventure"]
    if profile_group == "grafomotoryka":
        return _TEMPLATES["classic"]
    return _TEMPLATES["classic"]


def visual_theme_for_topic(topic: ResolvedTopic | str) -> VisualThemeSpec:
    family = visual_family_for_topic(topic.blueprint_key if isinstance(topic, ResolvedTopic) else str(topic))
    return _VISUAL_THEMES.get(family or "", _VISUAL_THEMES["default"])


def build_worksheet_plan(
    *,
    tasks: list[str],
    resolved_profile: ResolvedProfile,
    resolved_topic: ResolvedTopic,
    template_id: str | None = None,
) -> WorksheetPlan:
    pedagogy = get_pedagogy_spec(resolved_profile.profile_id)
    strategy = _strategy_for_profile(resolved_profile.profile_id)
    template = resolve_template(
        template_id,
        profile_group=pedagogy.profile_group,
        topic_id=resolved_topic.topic_id,
    )
    blocks = [
        _block_for_task(
            task,
            idx,
            profile_group=pedagogy.profile_group,
            strategy=strategy,
            total=len(tasks),
        )
        for idx, task in enumerate(tasks)
    ]
    sections = _sections_for_blocks(blocks, profile_group=pedagogy.profile_group)
    return WorksheetPlan(
        template=template,
        strategy=strategy,
        visual_theme=visual_theme_for_topic(resolved_topic),
        sections=sections,
    )


def _strategy_for_profile(profile_id: str) -> StrategySpec:
    spec = get_pedagogy_spec(profile_id)
    if spec.profile_group == "dyskalkulia":
        return StrategySpec(
            profile_id,
            spec.profile_group,
            "Jedna myśl naraz, krótkie polecenia i silne wsparcie obrazem.",
            ("compute", "choice", "color"),
            ("large_write", "circle"),
            False,
            ("Popatrz", "Policz", "Wpisz wynik"),
            3,
            "Ograniczono liczbę bodźców, dodano mikrokroki i duże odstępy.",
        )
    if spec.profile_group == "adhd":
        return StrategySpec(
            profile_id,
            spec.profile_group,
            "Krótkie segmenty, zmiana aktywności i widoczny postęp.",
            ("compute", "match", "color", "puzzle"),
            ("write", "circle", "connect", "color"),
            True,
            ("Start", "Cel", "Bonus", "Meta"),
            2,
            "Zadania podzielono na krótkie bloki z częstą zmianą aktywności.",
        )
    if spec.profile_group == "grafomotoryka":
        return StrategySpec(
            profile_id,
            spec.profile_group,
            "Mniej pisania, większe pola, więcej wyboru i łączenia.",
            ("choice", "match", "compute"),
            ("checkbox", "connect", "large_write"),
            True,
            ("Zaznacz", "Połącz", "Wpisz jedną liczbę"),
            3,
            "Ograniczono ręczny zapis do minimum i powiększono przestrzeń odpowiedzi.",
        )
    if spec.profile_group == "trudnosci":
        return StrategySpec(
            profile_id,
            spec.profile_group,
            "Stały rytm, prosty język i więcej miejsca na pracę.",
            ("compute", "choice"),
            ("large_write", "circle"),
            False,
            ("Przeczytaj", "Policz", "Sprawdź"),
            3,
            "Zastosowano powtarzalny układ i wolniejsze tempo zadań.",
        )
    return StrategySpec(
        profile_id,
        spec.profile_group,
        spec.goal_pl,
        ("compute", "reflect"),
        ("write",),
        False,
        ("Zadanie",),
        5,
        "Standardowy układ z czytelną hierarchią.",
    )


def _block_for_task(
    task: str,
    idx: int,
    *,
    profile_group: str,
    strategy: StrategySpec,
    total: int,
) -> WorksheetBlock:
    activity = _activity_for_index(idx, profile_group, strategy.allowed_activity_types)
    answer_mode = _answer_mode_for_activity(activity, profile_group, strategy.preferred_answer_modes)
    difficulty: Difficulty = "warmup" if idx == 0 else "challenge" if idx == total - 1 and total > 2 else "core"
    title = _activity_title(activity)
    instructions = _instructions_for(profile_group, activity)
    return WorksheetBlock(
        block_id=f"task-{idx + 1}",
        task_index=idx,
        title=title,
        task_text=task,
        activity_type=activity,
        answer_mode=answer_mode,
        difficulty=difficulty,
        visual_cue=_cue_for(activity, profile_group),
        answer_box_lines=_answer_lines_for(answer_mode, profile_group),
        progress_label=f"{idx + 1}/{total}" if strategy.progress_markers else "",
        instructions=instructions,
    )


def _sections_for_blocks(blocks: list[WorksheetBlock], *, profile_group: str) -> tuple[WorksheetSection, ...]:
    if not blocks:
        return ()
    warmup = blocks[:1]
    special = blocks[-1:] if len(blocks) > 2 else []
    middle = blocks[1:-1] if special else blocks[1:]
    if profile_group == "adhd":
        main_title = "B. Misje krótkie"
        special_title = "C. Bonus: zmiana aktywności"
    elif profile_group == "dyskalkulia":
        main_title = "B. Krok po kroku"
        special_title = "C. Spokojne sprawdzenie"
    elif profile_group == "grafomotoryka":
        main_title = "B. Zaznacz albo połącz"
        special_title = "C. Jedna odpowiedź"
    else:
        main_title = "B. Główne zadania"
        special_title = "C. Zadanie specjalne"

    sections: list[WorksheetSection] = [
        WorksheetSection("A", "A. Rozgrzewka", "Łatwy start i wejście w temat.", tuple(warmup)),
    ]
    if middle:
        sections.append(WorksheetSection("B", main_title, "Główna praca nad tematem.", tuple(middle)))
    if special:
        sections.append(WorksheetSection("C", special_title, "Krótka aktywność końcowa.", tuple(special)))
    sections.append(
        WorksheetSection(
            "D",
            "D. Podsumowanie sukcesu",
            "Uczeń zaznacza, co już umie.",
            (
                WorksheetBlock(
                    "success",
                    None,
                    "Mój sukces",
                    "Zaznacz: dziś umiem trochę więcej.",
                    "reflect",
                    "checkbox",
                    "summary",
                    "Sukces",
                    1,
                    instructions=("Uśmiechnij się do jednego dobrze zrobionego zadania.",),
                ),
            ),
            spacing_after=0,
        )
    )
    return tuple(sections)


def _activity_for_index(idx: int, profile_group: str, allowed: tuple[ActivityType, ...]) -> ActivityType:
    if profile_group == "adhd":
        cycle: tuple[ActivityType, ...] = ("compute", "match", "color", "puzzle")
    elif profile_group == "grafomotoryka":
        cycle = ("choice", "match", "compute")
    elif profile_group == "dyskalkulia":
        cycle = ("compute", "choice", "compute")
    else:
        cycle = allowed
    return cycle[idx % len(cycle)]


def _answer_mode_for_activity(
    activity: ActivityType,
    profile_group: str,
    preferred: tuple[AnswerMode, ...],
) -> AnswerMode:
    if profile_group == "grafomotoryka":
        return {"choice": "checkbox", "match": "connect"}.get(activity, "large_write")  # type: ignore[return-value]
    if activity == "color":
        return "color"
    if activity == "match":
        return "connect"
    if activity == "choice":
        return "circle"
    return preferred[0]


def _answer_lines_for(answer_mode: AnswerMode, profile_group: str) -> int:
    if answer_mode in ("checkbox", "circle", "connect", "color"):
        return 2 if profile_group == "grafomotoryka" else 1
    if answer_mode == "large_write":
        return 3 if profile_group in ("dyskalkulia", "grafomotoryka") else 2
    return 1


def _instructions_for(profile_group: str, activity: ActivityType) -> tuple[str, ...]:
    if profile_group == "dyskalkulia":
        return ("Popatrz na obrazek.", "Policz spokojnie.", "Wpisz wynik.")
    if profile_group == "adhd":
        labels = {
            "compute": ("Cel: policz.",),
            "match": ("Połącz pasujące elementy.",),
            "color": ("Pokoloruj odpowiedź.",),
            "puzzle": ("Rozwiąż zagadkę.",),
        }
        return labels.get(activity, ("Zrób jedno zadanie.",))
    if profile_group == "grafomotoryka":
        labels = {
            "choice": ("Zaznacz odpowiedź.",),
            "match": ("Połącz linią.",),
            "compute": ("Wpisz jedną liczbę.",),
        }
        return labels.get(activity, ("Odpowiedz krótko.",))
    return ()


def _activity_title(activity: ActivityType) -> str:
    return {
        "compute": "Policz",
        "match": "Dopasuj",
        "color": "Koloruj",
        "choice": "Wybierz",
        "puzzle": "Zagadka",
        "trace": "Po śladzie",
        "reflect": "Sukces",
    }[activity]


def _cue_for(activity: ActivityType, profile_group: str) -> str:
    if profile_group == "adhd":
        return {"compute": "Start", "match": "Ruch", "color": "Kolor", "puzzle": "Bonus"}.get(activity, "Cel")
    if profile_group == "grafomotoryka":
        return {"choice": "Zaznacz", "match": "Połącz", "compute": "Duże pole"}.get(activity, "Krótko")
    if profile_group == "dyskalkulia":
        return "1 krok"
    return "Zadanie"
