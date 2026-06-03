"""
Katalog profili PPP (P0.5).

Źródło prawdy dla UI Streamlit, metadanych PDF i polityki ilustracji.
Instancje profili pozostają w `app.generators.profiles`.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.generators.profiles.base import IllustrationMode, StudentProfile
from app.generators.profiles.registry import get_profile, all_profiles

# Kolejność w selectboxie (nauczycielski flow: od typowego do wsparcia).
PROFILE_DISPLAY_ORDER: tuple[str, ...] = (
    "standardowy",
    "dyskalkulia",
    "dysleksja",
    "trudności w nauce",
    "trudności grafomotoryczne",
    "ADHD",
    "zdolny",
)


@dataclass
class ResolvedProfile:
    profile_id: str
    ui_label: str
    pdf_label: str
    is_low_stimuli: bool
    illustration_mode: IllustrationMode
    profile: StudentProfile
    warnings: list[str] = field(default_factory=list)


def profile_ids_for_ui() -> list[str]:
    """Stabilne id profili widocznych w UI, w ustalonej kolejności."""
    out: list[str] = []
    for pid in PROFILE_DISPLAY_ORDER:
        p = get_profile(pid)
        if p.ui_visible:
            out.append(p.id)
    return out


def profile_selectbox_labels() -> dict[str, str]:
    """Mapa id -> etykieta w selectboxie (id jako wartość, label dla czytelności)."""
    return {pid: get_profile(pid).label_for_ui for pid in profile_ids_for_ui()}


def default_profile_id() -> str:
    return "standardowy"


def resolve_profile(profile_input: str | None) -> ResolvedProfile:
    """
    Rozwiązuje wejście z UI (id lub dopasowanie case-insensitive) do profilu.
    """
    profile = get_profile(profile_input)
    warnings: list[str] = []

    if profile_input and profile_input != profile.id:
        if profile_input.lower() != profile.id.lower():
            warnings.append(
                f"Nieznany profil „{profile_input}” — użyto profilu „{profile.label_for_ui}”."
            )

    if not profile.ui_visible and profile_input:
        warnings.append(
            f"Profil „{profile.label_for_ui}” nie jest standardowo dostępny w UI."
        )

    return ResolvedProfile(
        profile_id=profile.id,
        ui_label=profile.label_for_ui,
        pdf_label=profile.label_for_pdf,
        is_low_stimuli=profile.is_low_stimuli,
        illustration_mode=profile.illustration_mode,
        profile=profile,
        warnings=warnings,
    )


def uses_per_task_illustrations(profile_input: str | None) -> bool:
    from app.domain.visual_policy import uses_per_task_illustrations_from_catalog

    return uses_per_task_illustrations_from_catalog(profile_input)


def registry_ui_consistency_check() -> list[str]:
    """
    Zwraca listę problemów spójności registry ↔ katalog UI (do testów).
    Pusta lista = OK.
    """
    issues: list[str] = []
    registered = {p.id for p in all_profiles()}
    ordered = set(PROFILE_DISPLAY_ORDER)

    missing_in_order = registered - ordered
    if missing_in_order:
        issues.append(f"PROFILE_DISPLAY_ORDER brakuje: {sorted(missing_in_order)}")

    unknown_in_order = ordered - registered
    if unknown_in_order:
        issues.append(f"PROFILE_DISPLAY_ORDER nieznane id: {sorted(unknown_in_order)}")

    for pid in profile_ids_for_ui():
        p = get_profile(pid)
        if not p.ui_label:
            issues.append(f"Profil {pid!r} bez ui_label.")
        if not p.ui_summary:
            issues.append(f"Profil {pid!r} bez ui_summary.")

    return issues
