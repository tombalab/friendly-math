"""Central visual / low-stimuli policy from profile catalog (P1.1)."""
from __future__ import annotations

from app.domain.profile_catalog import ResolvedProfile, resolve_profile
from app.generators.profiles.base import IllustrationMode
from app.generators.profiles.registry import get_profile


def resolve_visual_policy(profile_input: str | None) -> tuple[IllustrationMode, bool]:
    """Returns (illustration_mode, low_stimuli_image_hint)."""
    profile = resolve_profile(profile_input)
    return profile.illustration_mode, profile.is_low_stimuli


def uses_per_task_illustrations_from_catalog(profile_input: str | None) -> bool:
    return resolve_profile(profile_input).illustration_mode == "per_task"


def low_stimuli_image_prompt_hint(profile_input: str | None) -> str:
    """Prompt fragment for OpenAI image generation — no hardcoded profile id sets."""
    if resolve_profile(profile_input).is_low_stimuli:
        return (
            "Use only 2-3 colors total. Use very simple shapes. "
            "Maximum 8 objects in the image."
        )
    return "Use 3-4 colors total. Keep composition uncluttered."


def is_low_stimuli_profile(profile_input: str | None) -> bool:
    return resolve_profile(profile_input).is_low_stimuli


def layout_overrides_for_profile(profile_input: str | None) -> dict:
    return dict(get_profile(profile_input).layout_overrides or {})


def policy_for_resolved(profile: ResolvedProfile) -> dict[str, object]:
    """Machine-readable policy snapshot for tests and quality panel."""
    return {
        "profile_id": profile.profile_id,
        "is_low_stimuli": profile.is_low_stimuli,
        "illustration_mode": profile.illustration_mode,
    }
