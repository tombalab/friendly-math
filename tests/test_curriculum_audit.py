"""Curriculum smoke: fallback banks pass profile validators (Faza 5)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "curriculum_fallback_audit.py"


def test_fallback_curriculum_audit_passes():
    proc = subprocess.run(
        [sys.executable, str(AUDIT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
