#!/usr/bin/env python3
"""
Offline smoke check for clean installs (P2.3).

Verifies imports, bundled Polish font, and minimal PDF generation without OpenAI.

Usage (from repo root):
    python scripts/smoke_check.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _check_python_version() -> None:
    if sys.version_info < (3, 11):
        raise SystemExit(
            f"Python 3.11+ required, got {sys.version_info.major}.{sys.version_info.minor}"
        )


def _check_imports() -> None:
    import streamlit  # noqa: F401
    import openai  # noqa: F401
    import dotenv  # noqa: F401
    import reportlab  # noqa: F401
    from PIL import Image  # noqa: F401
    import fitz  # noqa: F401

    from app.domain.worksheet_layout import resolve_worksheet_layout
    from app.domain.profile_catalog import resolve_profile
    from app.pdf.fonts import resolve_polish_font_path, register_polish_font
    from app.pdf.generator import WorksheetMeta, build_worksheet_pdf_bytes
    from app.worksheet.service import WorksheetService
    from app.domain.worksheet_contract import WorksheetRequest

    del resolve_worksheet_layout, resolve_profile, resolve_polish_font_path
    del register_polish_font, WorksheetMeta, build_worksheet_pdf_bytes
    del WorksheetService, WorksheetRequest


def _check_font() -> None:
    from app.pdf.fonts import resolve_polish_font_path, register_polish_font

    path, source = resolve_polish_font_path()
    if path is None or not path.is_file():
        raise SystemExit("DejaVuSans.ttf missing — see assets/fonts/README.md")
    if source != "bundled":
        raise SystemExit(f"Expected bundled font, got source={source!r}")
    reg = register_polish_font()
    if not reg.ok:
        raise SystemExit(f"Font registration failed: {reg.warning}")


def _check_pdf() -> None:
    from app.domain.profile_catalog import resolve_profile
    from app.domain.worksheet_layout import resolve_worksheet_layout
    from app.pdf.generator import WorksheetMeta, build_worksheet_pdf_bytes

    profile = resolve_profile("standardowy")
    layout = resolve_worksheet_layout(profile, grade=2, number_of_tasks=2)
    meta = WorksheetMeta(
        title="Smoke — klasa 2",
        grade="2",
        topic_range="dodawanie do 20",
        student_profile=profile.pdf_label,
        student_profile_id=profile.profile_id,
    )
    result = build_worksheet_pdf_bytes(
        meta=meta,
        tasks=["Policz: 2 + 3 = ____", "Policz: Łódź — ąęść = ____"],
        layout=layout,
        include_workspace=False,
    )
    if len(result.pdf_bytes) < 500 or result.pdf_bytes[:4] != b"%PDF":
        raise SystemExit("PDF smoke failed — invalid output")
    font_warn = [w for w in result.warnings if w.code == "pdf_font_missing"]
    if font_warn:
        raise SystemExit(f"PDF font warnings: {font_warn}")


def _check_offline_tests() -> None:
    from tests import test_pdf_font as pdf_font
    from tests import test_layout_policy as layout_policy
    from tests import test_reference_worksheets as ref
    from tests import test_task_validators as task_val

    pdf_font.test_font_file_available_in_repo()
    pdf_font.test_register_polish_font_ok()
    pdf_font.test_pdf_build_polish_diacritics_no_font_warning()
    layout_policy.test_low_stimuli_profiles_from_catalog_not_hardcoded_sets()
    layout_policy.test_illustration_mode_per_profile()
    ref.test_all_reference_schema_integrity()
    ref.test_all_reference_structured_criteria_pass()
    task_val.test_adhd_rejects_long_word_problem()
    task_val.test_dyskalkulia_rejects_large_operand()


def main() -> int:
    print("smoke: python version …", end=" ")
    _check_python_version()
    print("ok")

    print("smoke: imports …", end=" ")
    _check_imports()
    print("ok")

    print("smoke: font …", end=" ")
    _check_font()
    print("ok")

    print("smoke: pdf …", end=" ")
    _check_pdf()
    print("ok")

    print("smoke: offline tests …", end=" ")
    _check_offline_tests()
    print("ok")

    print("\n[ok] smoke_check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
