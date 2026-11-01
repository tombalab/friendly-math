"""Profile-first worksheet strategy and expanded layout schema."""
from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from typing import Literal

from app.domain.profile_catalog import ResolvedProfile
from app.domain.profile_pedagogy import get_pedagogy_spec
from app.domain.topic_catalog import ResolvedTopic, visual_family_for_topic
from app.generators.answers import compute_answer_key

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
    options: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorksheetSection:
    section_id: str
    title: str
    purpose_pl: str
    blocks: tuple[WorksheetBlock, ...]
    spacing_after: int = 16
    instruction_pl: str = ""


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
                    "instruction_pl": s.instruction_pl,
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
                            "options": list(b.options),
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
    answer_key = compute_answer_key(tasks, topic_id=resolved_topic.topic_id, grade=resolved_topic.grade)
    answers = [item.value if item.status == "supported" else "" for item in answer_key.items]
    blocks = [
        _block_for_task(
            task,
            idx,
            profile_group=pedagogy.profile_group,
            strategy=strategy,
            total=len(tasks),
            answer=answers[idx] if idx < len(answers) else "",
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


_INLINE_BLANK_RE = re.compile(r"_{3,}")
_INTEGER_RE = re.compile(r"^-?\d+$")


def _block_for_task(
    task: str,
    idx: int,
    *,
    profile_group: str,
    strategy: StrategySpec,
    total: int,
    answer: str = "",
) -> WorksheetBlock:
    """Aktywność wynika z sekcji i z treści zadania (Q3), nie z numeru zadania.

    Wybór i kolorowanie są możliwe tylko wtedy, gdy znamy odpowiedź liczbową
    i możemy pokazać opcje. W przeciwnym razie uczeń liczy i wpisuje wynik.
    """
    section_id = _section_id_for(idx, total)
    activity = _activity_for_section(section_id, profile_group)
    options = _choice_options(answer, idx) if activity in ("choice", "color") else ()
    if activity in ("choice", "color") and not options:
        activity = "compute"
    answer_mode = _answer_mode_for_activity(activity, profile_group, strategy.preferred_answer_modes)
    task_text = _INLINE_BLANK_RE.sub("?", task) if options else task
    difficulty: Difficulty = "warmup" if section_id == "A" else "challenge" if section_id == "C" else "core"
    return WorksheetBlock(
        block_id=f"task-{idx + 1}",
        task_index=idx,
        title=_activity_title(activity),
        task_text=task_text,
        activity_type=activity,
        answer_mode=answer_mode,
        difficulty=difficulty,
        visual_cue=_cue_for(activity, profile_group),
        answer_box_lines=_answer_lines_for(answer_mode, profile_group),
        progress_label=f"{idx + 1}/{total}" if strategy.progress_markers else "",
        options=options,
    )


def _section_id_for(idx: int, total: int) -> str:
    if idx == 0:
        return "A"
    if total > 2 and idx == total - 1:
        return "C"
    return "B"


def _activity_for_section(section_id: str, profile_group: str) -> ActivityType:
    """Jedna aktywność na sekcję — spójny sposób odpowiadania w obrębie sekcji."""
    if profile_group == "adhd":
        # Zmiana aktywności między sekcjami, nie między sąsiednimi zadaniami.
        return {"A": "compute", "B": "choice", "C": "color"}[section_id]  # type: ignore[return-value]
    if profile_group == "grafomotoryka":
        return "choice"
    return "compute"


def _choice_options(answer: str, idx: int) -> tuple[str, ...]:
    """Trzy opcje: poprawna i dwa bliskie dystraktory, kolejność zależna od numeru zadania."""
    value = answer.strip()
    if not _INTEGER_RE.match(value):
        return ()
    n = int(value)
    distractors = [n + 1, n - 1] if n >= 1 else [n + 1, n + 2]
    options = [n, *distractors]
    shift = idx % 3
    options = options[shift:] + options[:shift]
    return tuple(str(o) for o in options)


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
        main_title = "B. Zaznacz odpowiedź"
        special_title = "C. Ostatnie zadanie"
    else:
        main_title = "B. Główne zadania"
        special_title = "C. Zadanie na koniec"

    def section(section_id: str, title: str, purpose: str, items: list[WorksheetBlock]) -> WorksheetSection:
        instruction, blocks_out = _section_instruction(items, profile_group)
        return WorksheetSection(section_id, title, purpose, blocks_out, instruction_pl=instruction)

    sections: list[WorksheetSection] = [
        section("A", "A. Rozgrzewka", "Łatwy start i wejście w temat.", warmup),
    ]
    if middle:
        sections.append(section("B", main_title, "Główna praca nad tematem.", middle))
    if special:
        sections.append(section("C", special_title, "Krótka aktywność końcowa.", special))
    sections.append(
        WorksheetSection(
            "D",
            "D. Jak mi poszło?",
            "Uczeń sam ocenia, jak mu poszło.",
            (
                WorksheetBlock(
                    "self-check",
                    None,
                    "Moja ocena",
                    "Zaznacz jedną kratkę.",
                    "reflect",
                    "checkbox",
                    "summary",
                    "",
                    1,
                    options=("łatwo", "średnio", "trudno"),
                ),
            ),
            spacing_after=0,
        )
    )
    return tuple(sections)


def _section_instruction(
    blocks: list[WorksheetBlock], profile_group: str
) -> tuple[str, tuple[WorksheetBlock, ...]]:
    """Jedno polecenie dla sekcji, gdy na wszystkie zadania odpowiada się tak samo.

    Gdy sekcja jest mieszana (np. część zadań bez znanej odpowiedzi), polecenie
    trafia do każdego zadania osobno.
    """
    instructions = [_instruction_for(b, profile_group) for b in blocks]
    if len(set(instructions)) == 1:
        return instructions[0], tuple(blocks)
    return "", tuple(replace(b, instructions=(instr,)) for b, instr in zip(blocks, instructions))


def _instruction_for(block: WorksheetBlock, profile_group: str) -> str:
    if block.activity_type == "choice":
        if block.answer_mode == "checkbox":
            return "Zaznacz X w kratce przy dobrej odpowiedzi."
        return "Otocz kółkiem dobrą odpowiedź."
    if block.activity_type == "color":
        return "Pokoloruj kółko z dobrą odpowiedzią."
    has_blank = bool(_INLINE_BLANK_RE.search(block.task_text))
    if profile_group == "dyskalkulia":
        if has_blank:
            return "Policz spokojnie, krok po kroku. Wpisz wynik w lukę."
        return "Policz spokojnie, krok po kroku. Zapisz wynik w ramce."
    return "Oblicz i wpisz wynik w lukę." if has_blank else "Rozwiąż i zapisz odpowiedź w ramce."


def _answer_mode_for_activity(
    activity: ActivityType,
    profile_group: str,
    preferred: tuple[AnswerMode, ...],
) -> AnswerMode:
    if profile_group == "grafomotoryka":
        return "checkbox" if activity == "choice" else "large_write"
    if activity == "color":
        return "color"
    if activity == "choice":
        return "circle"
    return preferred[0]


def _answer_lines_for(answer_mode: AnswerMode, profile_group: str) -> int:
    if answer_mode in ("checkbox", "circle", "connect", "color"):
        return 2 if profile_group == "grafomotoryka" else 1
    if answer_mode == "large_write":
        return 3 if profile_group in ("dyskalkulia", "grafomotoryka") else 2
    return 1


def _activity_title(activity: ActivityType) -> str:
    return {
        "compute": "Oblicz",
        "match": "Dopasuj",
        "color": "Pokoloruj",
        "choice": "Wybierz odpowiedź",
        "puzzle": "Zagadka",
        "trace": "Po śladzie",
        "reflect": "Moja ocena",
    }[activity]


def _cue_for(activity: ActivityType, profile_group: str) -> str:
    if profile_group == "adhd":
        return {"compute": "Start", "match": "Ruch", "color": "Kolor", "puzzle": "Bonus"}.get(activity, "Cel")
    if profile_group == "grafomotoryka":
        return {"choice": "Zaznacz", "match": "Połącz", "compute": "Duże pole"}.get(activity, "Krótko")
    if profile_group == "dyskalkulia":
        return "1 krok"
    return "Zadanie"
