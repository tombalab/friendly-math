"""
Reference-driven offline quality tests (P1.2).

Loads every JSON in `data/reference_worksheets/` and checks schema, answers,
PDF rendering, and visual policy without calling OpenAI.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.domain.profile_catalog import resolve_profile
from app.domain.topic_catalog import resolve_topic, should_skip_images
from app.generators.answers import compute_answer_key
from app.generators.images import (
    generate_worksheet_image,
    generate_worksheet_images_for_tasks,
)
from app.pdf.fonts import resolve_polish_font_path
from app.domain.structured_criteria import StructuredQualityCriteria
from app.pdf.generator import WorksheetMeta, build_worksheet_pdf_bytes
from app.validators.task_validator import validate_tasks

ROOT = Path(__file__).resolve().parents[1]
REF_DIR = ROOT / "data" / "reference_worksheets"

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_REQUIRED_METADATA = ("title", "grade", "topic", "profile")

# Jawne luki w auto-kluczu (różne mianowniki / interpretacja nauczyciela).
_ACCEPTED_UNSUPPORTED_ANSWERS: dict[str, frozenset[int]] = {
    "6_ulamki_dysleksja.json": frozenset({0, 4}),
}


def list_reference_files() -> list[Path]:
    return sorted(REF_DIR.glob("*.json"))


def load_reference(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_schema(path: Path, data: dict[str, Any]) -> None:
    assert "metadata" in data, f"{path.name}: brak metadata"
    meta = data["metadata"]
    assert isinstance(meta, dict), f"{path.name}: metadata musi być obiektem"
    for key in _REQUIRED_METADATA:
        assert key in meta, f"{path.name}: metadata.{key} jest wymagane"
    assert isinstance(meta["grade"], int), f"{path.name}: grade musi być int"
    assert isinstance(meta["topic"], str) and meta["topic"].strip(), (
        f"{path.name}: topic nie może być pusty"
    )
    assert isinstance(meta["profile"], str) and meta["profile"].strip(), (
        f"{path.name}: profile nie może być pusty"
    )

    tasks = data.get("tasks")
    assert isinstance(tasks, list) and tasks, f"{path.name}: tasks musi być niepustą listą"
    assert all(isinstance(t, str) and t.strip() for t in tasks), (
        f"{path.name}: każde zadanie musi być niepustym stringiem"
    )

    answers = data.get("answers")
    assert isinstance(answers, list), f"{path.name}: answers musi być listą"
    assert len(answers) == len(tasks), (
        f"{path.name}: answers ({len(answers)}) != tasks ({len(tasks)})"
    )
    assert all(isinstance(a, str) for a in answers), f"{path.name}: answers muszą być stringami"

    criteria = data.get("quality_criteria")
    assert isinstance(criteria, list) and criteria, (
        f"{path.name}: quality_criteria musi być niepustą listą"
    )
    assert all(isinstance(c, str) and c.strip() for c in criteria), (
        f"{path.name}: każde quality_criteria musi być niepustym stringiem"
    )

    structured = data.get("structured_criteria")
    assert structured is not None, (
        f"{path.name}: structured_criteria jest wymagane (P2.2)"
    )
    parsed = StructuredQualityCriteria.from_mapping(structured)
    assert parsed is not None


def _is_png(data: bytes) -> bool:
    return len(data) >= len(_PNG_MAGIC) and data.startswith(_PNG_MAGIC)


def test_all_reference_files_present():
    files = list_reference_files()
    assert files, "Brak plików JSON w data/reference_worksheets/"
    assert len(files) >= 35


def test_all_reference_schema_integrity():
    for path in list_reference_files():
        _validate_schema(path, load_reference(path))


def test_all_reference_structured_criteria_pass():
    """Zadania wzorcowe spełniają własne kryteria maszynowe (P2.2)."""
    for path in list_reference_files():
        data = load_reference(path)
        criteria = StructuredQualityCriteria.from_mapping(data["structured_criteria"])
        result = validate_tasks(data["tasks"], criteria)
        assert result.ok, (
            f"{path.name}: naruszenie structured_criteria — "
            + "; ".join(f"[{i.code}] {i.message}" for i in result.issues)
        )


def test_all_reference_answer_keys():
    for path in list_reference_files():
        data = load_reference(path)
        meta = data["metadata"]
        key = compute_answer_key(
            data["tasks"],
            topic_label=meta["topic"],
            grade=meta["grade"],
        )
        accepted_gaps = _ACCEPTED_UNSUPPORTED_ANSWERS.get(path.name, frozenset())

        if not accepted_gaps:
            assert key.supported_count == len(data["tasks"]), (
                f"{path.name}: oczekiwano pełnego klucza, "
                f"otrzymano {key.supported_count}/{len(data['tasks'])}"
            )
            assert [a.value for a in key.items] == data["answers"]
        else:
            unsupported = {
                i for i, item in enumerate(key.items) if item.status != "supported"
            }
            assert unsupported == set(accepted_gaps), (
                f"{path.name}: nieoczekiwane luki {unsupported}, "
                f"oczekiwano {set(accepted_gaps)}"
            )
            for i, (item, expected) in enumerate(zip(key.items, data["answers"])):
                if i in accepted_gaps:
                    assert item.status != "supported"
                else:
                    assert item.status == "supported", f"{path.name} zadanie {i + 1}"
                    assert item.value == expected


def test_all_reference_pdf_smoke():
    font_path, _ = resolve_polish_font_path()
    assert font_path is not None, "Brak DejaVuSans.ttf — wymagane do testów PDF"

    for path in list_reference_files():
        data = load_reference(path)
        meta = data["metadata"]
        resolved_profile = resolve_profile(meta["profile"])
        resolved_topic = resolve_topic(meta["topic"], meta["grade"])

        worksheet_meta = WorksheetMeta(
            title=meta["title"],
            grade=str(meta["grade"]),
            topic_range=resolved_topic.label_pl,
            student_profile=resolved_profile.pdf_label,
            student_profile_id=resolved_profile.profile_id,
        )
        answer_key = compute_answer_key(
            data["tasks"],
            topic_id=resolved_topic.topic_id,
            grade=meta["grade"],
        )

        result = build_worksheet_pdf_bytes(
            meta=worksheet_meta,
            tasks=data["tasks"],
            answer_key=answer_key,
            include_workspace=True,
        )

        assert len(result.pdf_bytes) > 500, f"{path.name}: PDF za mały"
        assert result.pdf_bytes[:4] == b"%PDF", f"{path.name}: nieprawidłowy nagłówek PDF"
        font_warnings = [w for w in result.warnings if w.code == "pdf_font_missing"]
        assert font_warnings == [], f"{path.name}: brak czcionki polskiej — {font_warnings}"

        _assert_pdf_contains_metadata(result.pdf_bytes, meta, path.name)


def _assert_pdf_contains_metadata(pdf_bytes: bytes, meta: dict[str, Any], label: str) -> None:
    """Sprawdza tekst metadanych w PDF, gdy dostępny PyMuPDF."""
    try:
        import fitz  # type: ignore
    except ModuleNotFoundError:
        return

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        text = "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()

    assert str(meta["grade"]) in text, f"{label}: brak klasy w PDF"
    assert "Karta odpowiedzi" in text or "Odpowiedzi" in text, (
        f"{label}: brak strony odpowiedzi"
    )
    assert "Klucz automatyczny" in text, f"{label}: brak podsumowania klucza w PDF"


def test_visual_skip_for_algebraic_equations_topic():
    """Temat „równania” (kl. 4+) ma skip_images w katalogu."""
    assert should_skip_images("równania") is True
    header = generate_worksheet_image(
        "równania",
        profile="standardowy",
        grade=5,
    )
    per_task = generate_worksheet_images_for_tasks(
        ["Rozwiąż: ☐ + 8 = 15"],
        topic="równania",
        profile="dyskalkulia",
        grade=5,
    )
    assert header == b""
    assert per_task == [b""]


def test_visual_box_equations_per_task_intentionally_empty():
    """Równania z okienkiem nie mają bezpiecznej ilustracji per-zadanie."""
    per_task = generate_worksheet_images_for_tasks(
        ["Uzupełnij okienko: 3 + ☐ = 7"],
        topic="równania z okienkiem",
        profile="dyskalkulia",
        grade=2,
    )
    assert per_task == [b""]


def test_visual_reference_adhd_per_task_renders():
    data = load_reference(REF_DIR / "1_dodawanie_adhd.json")
    meta = data["metadata"]
    images = generate_worksheet_images_for_tasks(
        data["tasks"],
        topic=meta["topic"],
        profile=meta["profile"],
        grade=meta["grade"],
    )
    assert len(images) == len(data["tasks"])
    assert all(_is_png(img) for img in images), "ADHD: oczekiwano PNG dla małych działań"


def test_visual_reference_dyskalkulia_per_task_renders():
    data = load_reference(REF_DIR / "2_dodawanie_dyskalkulia.json")
    meta = data["metadata"]
    images = generate_worksheet_images_for_tasks(
        data["tasks"],
        topic=meta["topic"],
        profile=meta["profile"],
        grade=meta["grade"],
    )
    assert len(images) == len(data["tasks"])
    rendered = [i for i, img in enumerate(images) if _is_png(img)]
    skipped = [i for i, img in enumerate(images) if img == b""]
    assert len(rendered) >= 6, "dyskalkulia: większość zadań powinna mieć ilustrację"
    # 9 + 1 przekracza a_max=8 w _SAFE_LIMITS — świadome pominięcie.
    assert 6 in skipped, "dyskalkulia: 9+1 poza bezpiecznym zakresem ilustracji"


def test_visual_reference_standardowy_header_renders():
    data = load_reference(REF_DIR / "5_mnozenie_standardowy.json")
    meta = data["metadata"]
    header = generate_worksheet_image(
        topic=meta["topic"],
        profile=meta["profile"],
        grade=meta["grade"],
    )
    assert _is_png(header), "standardowy/mnożenie: oczekiwano ilustracji nagłówka"


def test_visual_reference_ulamki_header_renders():
    data = load_reference(REF_DIR / "6_ulamki_dysleksja.json")
    meta = data["metadata"]
    header = generate_worksheet_image(
        topic=meta["topic"],
        profile=meta["profile"],
        grade=meta["grade"],
    )
    assert _is_png(header), "ułamki: oczekiwano ilustracji nagłówka (pizza)"


def test_visual_large_multiplication_skipped_per_task():
    """Zadanie poza _SAFE_LIMITS nie powinno mieć mylącej ilustracji per-zadanie."""
    task = "Policz: 9 × 13 = ____"
    images = generate_worksheet_images_for_tasks(
        [task],
        topic="mnożenie",
        profile="dyskalkulia",
        grade=5,
    )
    assert images == [b""]
