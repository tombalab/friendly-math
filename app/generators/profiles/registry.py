# profiles/registry.py
#
# Centralny rejestr profili PPP. Generator tekstu (text_generator)
# i generator layoutu (layout_generator) korzystają z `get_profile(id)`,
# żeby uniknąć duplikacji ifów po stringach.

from __future__ import annotations

from typing import Dict, Iterable

from .base import StudentProfile
from .adhd import ADHDProfile
from .dyskalkulia import DyskalkuliaProfile
from .dysleksja import DysleksjaProfile
from .grafomotoryka import GrafomotorykaProfile
from .standardowy import StandardowyProfile
from .trudnosci import TrudnosciProfile
from .zdolny import ZdolnyProfile


_PROFILES: Dict[str, StudentProfile] = {
    p.id: p
    for p in (
        StandardowyProfile(),
        DyskalkuliaProfile(),
        ADHDProfile(),
        DysleksjaProfile(),
        TrudnosciProfile(),
        GrafomotorykaProfile(),
        ZdolnyProfile(),
    )
}


def get_profile(profile_id: str | None) -> StudentProfile:
    """
    Zwraca instancję profilu po `id` (np. "dyskalkulia", "ADHD", "trudności w nauce").
    Dla nieznanych/None zwraca StandardowyProfile (bezpieczny fallback).
    """
    if not profile_id:
        return _PROFILES["standardowy"]
    # Dopasowanie odporne na regiśnięcie znaku (UI wcześniej używało "adhd"/"ADHD" wymiennie).
    if profile_id in _PROFILES:
        return _PROFILES[profile_id]
    lowered = profile_id.lower()
    for pid, prof in _PROFILES.items():
        if pid.lower() == lowered:
            return prof
    return _PROFILES["standardowy"]


def all_profiles() -> Iterable[StudentProfile]:
    """Zwraca wszystkie zarejestrowane profile (do testów / UI)."""
    return _PROFILES.values()


def registered_profile_ids() -> list[str]:
    return list(_PROFILES.keys())
