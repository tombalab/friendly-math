"""
Centralna polityka pedagogiczna profili PPP (plan naprawczy profili).

Źródło merytoryczne: docs/domains/student-profile-pedagogy-sources.md
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.generators.profiles.registry import get_profile

ProfileGroup = Literal[
    "standardowy",
    "adhd",
    "dyskalkulia",
    "dysleksja",
    "trudnosci",
    "grafomotoryka",
    "zdolny",
]

TaskShape = Literal["standard", "one_step_compact", "enriched_optional_chain"]
WordingStyle = Literal["neutral", "brief_precise", "minimal_text", "scaffolded"]
VisualSupport = Literal["header", "per_task_sparse", "per_task_rich", "none"]
LayoutDensity = Literal["standard", "spacious", "readable", "compact_with_reasoning"]
ValidationMode = Literal["advisory", "enforce_with_fallback"]


@dataclass(frozen=True)
class ProfilePedagogySpec:
    profile_id: str
    profile_group: ProfileGroup
    display_name: str
    goal_pl: str
    task_shape: TaskShape
    max_steps_default: int
    wording: WordingStyle
    visual_support: VisualSupport
    layout_density: LayoutDensity
    validation_mode: ValidationMode
    numeric_scale: float  # mnożnik max_operand blueprintu (1.0 = bez zmian)
    max_task_length_default: int
    forbid_word_problems: bool
    require_enriched_ratio: float  # ułamek zadań wzbogaconych (zdolny)
    prompt_positive: str
    prompt_negative: str
    teacher_hint_pl: str
    max_icon_count: int  # górny limit obiektów w ilustracji per zadanie


_PROFILE_SPECS: dict[str, ProfilePedagogySpec] = {
    "standardowy": ProfilePedagogySpec(
        profile_id="standardowy",
        profile_group="standardowy",
        display_name="Standardowy",
        goal_pl="Typowy poziom klasy — bez dodatkowych uproszczeń.",
        task_shape="standard",
        max_steps_default=2,
        wording="neutral",
        visual_support="header",
        layout_density="standard",
        validation_mode="advisory",
        numeric_scale=1.0,
        max_task_length_default=80,
        forbid_word_problems=False,
        require_enriched_ratio=0.0,
        prompt_positive="Zadania zgodne z blueprintem tematu i klasą.",
        prompt_negative="Nie upraszczaj ani nie komplikuj bez potrzeby.",
        teacher_hint_pl="Typowy poziom klasy — bez dodatkowych uproszczeń.",
        max_icon_count=8,
    ),
    "ADHD": ProfilePedagogySpec(
        profile_id="ADHD",
        profile_group="adhd",
        display_name="ADHD",
        goal_pl="Krótkie, jednoetapowe zadania; mało bodźców; jasna struktura.",
        task_shape="one_step_compact",
        max_steps_default=1,
        wording="brief_precise",
        visual_support="per_task_sparse",
        layout_density="spacious",
        validation_mode="enforce_with_fallback",
        numeric_scale=0.55,
        max_task_length_default=48,
        forbid_word_problems=True,
        require_enriched_ratio=0.0,
        prompt_positive=(
            "Bardzo krótkie polecenia (max 1 zdanie), format „Policz: a op b = ____”, "
            "jedna operacja, liczby małe (np. do 10 w klasie 1–2)."
        ),
        prompt_negative=(
            "Bez zadań tekstowych, bez historii (Ania, Tomek), bez dwóch operacji w jednym zadaniu, "
            "bez dodatkowych danych."
        ),
        teacher_hint_pl="Krótkie, jednoetapowe zadania; ilustracja przy zadaniu (gdy włączona).",
        max_icon_count=6,
    ),
    "dyskalkulia": ProfilePedagogySpec(
        profile_id="dyskalkulia",
        profile_group="dyskalkulia",
        display_name="Dyskalkulia",
        goal_pl="Proste liczby, jeden krok, wizualizacja ilości.",
        task_shape="one_step_compact",
        max_steps_default=1,
        wording="brief_precise",
        visual_support="per_task_rich",
        layout_density="spacious",
        validation_mode="enforce_with_fallback",
        numeric_scale=0.6,
        max_task_length_default=55,
        forbid_word_problems=True,
        require_enriched_ratio=0.0,
        prompt_positive=(
            "Liczby bardzo proste (np. 1–12 w klasie 1–2), jeden krok, język obok symboli, "
            "format stały jak w przykładach."
        ),
        prompt_negative="Bez długich poleceń i zadań wieloetapowych.",
        teacher_hint_pl="Prostsze liczby, większe odstępy, ilustracja przy każdym zadaniu (gdy włączona).",
        max_icon_count=8,
    ),
    "dysleksja": ProfilePedagogySpec(
        profile_id="dysleksja",
        profile_group="dysleksja",
        display_name="Dysleksia",
        goal_pl="Krótkie polecenia; poziom liczb jak w klasie.",
        task_shape="one_step_compact",
        max_steps_default=1,
        wording="minimal_text",
        visual_support="header",
        layout_density="readable",
        validation_mode="enforce_with_fallback",
        numeric_scale=1.0,
        max_task_length_default=52,
        forbid_word_problems=False,
        require_enriched_ratio=0.0,
        prompt_positive=(
            "Krótkie, powtarzalne polecenia (max 1 zdanie); liczby normalne dla klasy; "
            "nie upraszczaj matematyki — skróć tekst."
        ),
        prompt_negative="Bez długich zdań i synonimów dla tego samego pojęcia w jednej karcie.",
        teacher_hint_pl="Krótkie polecenia i czytelny układ; poziom liczb jak w klasie.",
        max_icon_count=8,
    ),
    "trudności w nauce": ProfilePedagogySpec(
        profile_id="trudności w nauce",
        profile_group="trudnosci",
        display_name="Trudności w nauce",
        goal_pl="Wolniejsze tempo, prostsze liczby, powtarzalny format.",
        task_shape="one_step_compact",
        max_steps_default=1,
        wording="scaffolded",
        visual_support="per_task_sparse",
        layout_density="spacious",
        validation_mode="enforce_with_fallback",
        numeric_scale=0.75,
        max_task_length_default=60,
        forbid_word_problems=True,
        require_enriched_ratio=0.0,
        prompt_positive=(
            "Proste liczby (np. 1–15), krótkie polecenia, jeden krok, powtarzalny format; "
            "można serię podobnych przykładów."
        ),
        prompt_negative="Bez skoków trudności między zadaniami.",
        teacher_hint_pl="Wolniejsze tempo, prostsze liczby; ilustracja przy zadaniu (gdy włączona).",
        max_icon_count=7,
    ),
    "trudności grafomotoryczne": ProfilePedagogySpec(
        profile_id="trudności grafomotoryczne",
        profile_group="grafomotoryka",
        display_name="Trudności grafomotoryczne",
        goal_pl="Mniej pisania, duże pola odpowiedzi, wybór i łączenie zamiast przepisywania.",
        task_shape="one_step_compact",
        max_steps_default=1,
        wording="brief_precise",
        visual_support="per_task_sparse",
        layout_density="spacious",
        validation_mode="enforce_with_fallback",
        numeric_scale=0.8,
        max_task_length_default=58,
        forbid_word_problems=True,
        require_enriched_ratio=0.0,
        prompt_positive=(
            "Krótkie polecenia, jedna odpowiedź na zadanie, minimalne pisanie; "
            "preferuj wybór wyniku, zaznaczanie lub wpisanie pojedynczej liczby."
        ),
        prompt_negative="Bez przepisywania treści, długich odpowiedzi i kilku działań w jednym zadaniu.",
        teacher_hint_pl="Duże pola odpowiedzi, mniej pisania, więcej zaznaczania/wyboru.",
        max_icon_count=7,
    ),
    "zdolny": ProfilePedagogySpec(
        profile_id="zdolny",
        profile_group="zdolny",
        display_name="Zdolny",
        goal_pl="Większe wyzwanie; część zadań wieloetapowych lub z uzasadnieniem.",
        task_shape="enriched_optional_chain",
        max_steps_default=3,
        wording="neutral",
        visual_support="header",
        layout_density="compact_with_reasoning",
        validation_mode="advisory",
        numeric_scale=1.15,
        max_task_length_default=90,
        forbid_word_problems=False,
        require_enriched_ratio=0.34,
        prompt_positive=(
            "Co najmniej jedna trzecia zadań może być trudniejsza lub dwuetapowa "
            '(np. „Policz: 2 + 3, wynik pomnóż przez 2 = ____") albo z pytaniem „Wyjaśnij sposób”.'
        ),
        prompt_negative="Nie upraszczaj poniżej poziomu klasy.",
        teacher_hint_pl="Nieco trudniejsze zadania i więcej treści na stronie.",
        max_icon_count=8,
    ),
}


def get_pedagogy_spec(profile_input: str | None) -> ProfilePedagogySpec:
    profile = get_profile(profile_input)
    spec = _PROFILE_SPECS.get(profile.id)
    if spec is not None:
        return spec
    lowered = profile.id.lower()
    for pid, s in _PROFILE_SPECS.items():
        if pid.lower() == lowered:
            return s
    return _PROFILE_SPECS["standardowy"]


def profile_group(profile_input: str | None) -> ProfileGroup:
    return get_pedagogy_spec(profile_input).profile_group


def teacher_hint_for_profile(profile_input: str | None) -> str:
    return get_pedagogy_spec(profile_input).teacher_hint_pl


def tighten_blueprint_max_result(
    blueprint_max: int | None,
    profile_input: str | None,
    *,
    grade: int,
) -> int | None:
    """Zawęża limit wyniku z blueprintu według profilu (przed promptem / filtrem)."""
    if blueprint_max is None:
        return None
    spec = get_pedagogy_spec(profile_input)
    scaled = int(blueprint_max * spec.numeric_scale)
    if spec.profile_group == "adhd" and grade <= 2:
        scaled = min(scaled, 20)
    if spec.profile_group == "dyskalkulia" and grade <= 3:
        scaled = min(scaled, 40 if grade == 3 else 20)
    if spec.profile_group == "trudnosci" and grade <= 3:
        scaled = min(scaled, 50 if grade == 3 else 25)
    return max(5, scaled)


def build_profile_prompt_section(profile_input: str | None) -> str:
    spec = get_pedagogy_spec(profile_input)
    profile = get_profile(profile_input)
    if spec.profile_group == "standardowy":
        return ""

    lines = [
        f"\nProfil ucznia: {spec.display_name}",
        f"Cel: {spec.goal_pl}",
        f"- {profile.task_instruction}",
        f"Wymagania profilu: {spec.prompt_positive}",
        f"Unikaj: {spec.prompt_negative}",
    ]
    if spec.forbid_word_problems:
        lines.append("- Nie generuj zadań tekstowych z narracją (imiona, sklep, historia).")
    if spec.max_steps_default == 1:
        lines.append("- Każde zadanie: dokładnie jedna operacja matematyczna.")
    if spec.require_enriched_ratio > 0:
        pct = int(spec.require_enriched_ratio * 100)
        lines.append(f"- Około {pct}% zadań może być wzbogaconych (dwa kroki lub krótkie uzasadnienie).")
    return "\n".join(lines)


def low_stimuli_boost_for_profile(profile_input: str | None) -> dict:
    """Różnicowane wzmocnienie layoutu PDF dla profili wspierających."""
    spec = get_pedagogy_spec(profile_input)
    common = {
        "title_font_size": 24,
        "metadata_font_size": 12,
        "section_font_size": 18,
        "margin": 60,
        "title_spacing": 32,
        "metadata_spacing": 26,
        "background_color": "#fafafa",
    }
    if spec.profile_group == "adhd":
        return {
            **common,
            "task_font_size": 16,
            "task_spacing": 18,
            "line_spacing": 24,
            "section_spacing": 28,
            "workspace_lines": 3,
        }
    if spec.profile_group == "grafomotoryka":
        return {
            **common,
            "task_font_size": 16,
            "task_spacing": 20,
            "line_spacing": 25,
            "section_spacing": 28,
            "workspace_lines": 1,
            "workspace_line_gap": 30,
        }
    if spec.profile_group == "dyskalkulia":
        return {
            **common,
            "task_font_size": 15,
            "task_spacing": 16,
            "line_spacing": 22,
            "section_spacing": 26,
            "workspace_lines": 5,
            "workspace_line_gap": 24,
        }
    if spec.profile_group == "trudnosci":
        return {
            **common,
            "task_font_size": 15,
            "task_spacing": 14,
            "line_spacing": 21,
            "section_spacing": 24,
            "workspace_lines": 4,
        }
    return {
        **common,
        "task_font_size": 16,
        "task_spacing": 14,
        "line_spacing": 22,
        "section_spacing": 24,
        "workspace_lines": 4,
    }


def layout_overrides_for_pedagogy(profile_input: str | None) -> dict:
    """Dodatkowe/nadpisujące layout overrides z polityki profilu."""
    spec = get_pedagogy_spec(profile_input)
    profile = get_profile(profile_input)
    base = dict(profile.layout_overrides or {})

    if spec.layout_density == "spacious":
        base.update(
            {
                "task_font_size": max(base.get("task_font_size", 14), 15),
                "line_spacing": max(base.get("line_spacing", 20), 22),
                "task_spacing": max(base.get("task_spacing", 14), 16),
                "workspace_lines": max(base.get("workspace_lines", 3), 4),
            }
        )
    elif spec.layout_density == "readable":
        base.setdefault("task_font_size", 13)
        base.setdefault("line_spacing", 18)
    elif spec.layout_density == "compact_with_reasoning":
        base.update(
            {
                "task_font_size": min(base.get("task_font_size", 12), 12),
                "line_spacing": min(base.get("line_spacing", 16), 16),
                "workspace_lines": max(base.get("workspace_lines", 2), 3),
            }
        )

    if spec.profile_group == "adhd":
        base["background_color"] = "#fafafa"
    elif spec.profile_group == "dyskalkulia":
        base["background_color"] = "#fafafa"
        base["workspace_lines"] = max(base.get("workspace_lines", 4), 5)
    elif spec.profile_group == "grafomotoryka":
        base["background_color"] = "#fbfbf8"
        base["workspace_lines"] = min(base.get("workspace_lines", 1), 1)
        base["workspace_line_gap"] = max(base.get("workspace_line_gap", 24), 30)
    elif spec.profile_group == "trudnosci":
        base["background_color"] = "#fafafa"

    return base


def visual_max_objects(profile_input: str | None) -> int:
    return get_pedagogy_spec(profile_input).max_icon_count


def uses_per_task_visuals(profile_input: str | None) -> bool:
    spec = get_pedagogy_spec(profile_input)
    return spec.visual_support in ("per_task_sparse", "per_task_rich")


def profile_fulfillment_labels(
    *,
    profile_id: str,
    validation_issue_count: int,
    enriched_count: int,
    total_tasks: int,
) -> tuple[str, str]:
    """Krótki opis spełnienia profilu dla panelu jakości."""
    spec = get_pedagogy_spec(profile_id)
    checks = 0
    passed = 0

    checks += 1
    if validation_issue_count == 0:
        passed += 1

    if spec.require_enriched_ratio > 0 and total_tasks > 0:
        checks += 1
        need = max(1, int(total_tasks * spec.require_enriched_ratio + 0.5))
        if enriched_count >= need:
            passed += 1

    if checks == 0:
        return "—", "brak kryteriów"
    label = f"Profil spełniony: {passed}/{checks} kryteriów"
    severity = "OK" if passed == checks else "częściowo"
    return label, severity
