"""Test ochronny P1.1: polityka profili nie może wracać jako surowe listy id rozsiane po kodzie."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Moduły, które legalnie znają id profili.
ALLOWED = {
    "app/generators/profiles",  # definicje profili i rejestr
    "app/domain/profile_catalog.py",  # katalog UI
    "app/domain/profile_pedagogy.py",  # centralna specyfikacja pedagogiczna
    "app/ai/profile_fallback_banks.py",  # banki zadań kluczowane id profilu
    # TODO(P2.6): progi walidacji per profil do przeniesienia do specyfikacji.
    "app/validators/profile_policy.py",
}

_PROFILE_IDS = (
    "standardowy",
    "dyskalkulia",
    "dysleksja",
    "ADHD",
    "adhd",
    "trudności w nauce",
    "trudności grafomotoryczne",
    "zdolny",
)
# Porównanie zmiennej profilu (nie grupy profilu) z surowym id, np. `profile_id in ("ADHD", ...)`.
_RAW_COMPARISON = re.compile(
    r"\b(?!\w*group)(?:\w*profile\w*|pid)\b(?:\.lower\(\))?\s*(?:==|!=|\bin\b|\bnot in\b)\s*"
    r"[\(\[\{]?\s*\"(?:" + "|".join(re.escape(p) for p in _PROFILE_IDS) + r")\""
)


def _is_allowed(rel: str) -> bool:
    return any(rel == a or rel.startswith(a + "/") for a in ALLOWED)


def test_no_raw_profile_id_comparisons_outside_profile_modules():
    offenders: list[str] = []
    for path in sorted((ROOT / "app").rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        if _is_allowed(rel):
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if _RAW_COMPARISON.search(line):
                offenders.append(f"{rel}:{lineno}: {line.strip()}")
    assert not offenders, (
        "Polityka profilu powinna pochodzić z katalogu/specyfikacji, nie z surowych id:\n"
        + "\n".join(offenders)
    )


def test_guard_regex_catches_typical_regressions():
    assert _RAW_COMPARISON.search('if profile_id in ("dyskalkulia", "ADHD"):')
    assert _RAW_COMPARISON.search('low = profile == "trudności w nauce"')
    assert _RAW_COMPARISON.search('if pid == "adhd":')
    assert not _RAW_COMPARISON.search('if spec.profile_group == "dyskalkulia":')
    assert not _RAW_COMPARISON.search('if profile_group in ("dyskalkulia", "grafomotoryka"):')
