"""Profile-aware task validators (P2.1 / P2.2)."""
from __future__ import annotations

from app.domain.structured_criteria import StructuredQualityCriteria
from app.validators.profile_policy import policy_for_profile
from app.validators.task_validator import validate_tasks, validate_tasks_for_profile


def test_adhd_rejects_long_word_problem():
    policy = policy_for_profile("ADHD", grade=1, topic_id="dodawanie")
    tasks = [
        "Ania miała 3 jabłka. Dostała 2 więcej. Ile ma teraz?",
    ]
    result = validate_tasks(tasks, policy)
    codes = {i.code for i in result.issues}
    assert "forbidden_phrase" in codes or "word_problem_load" in codes
    assert "format_prefix" in codes


def test_dyskalkulia_rejects_large_operand():
    policy = policy_for_profile("dyskalkulia", grade=2, topic_id="dodawanie")
    result = validate_tasks(["Policz: 15 + 2 = ____"], policy)
    assert any(i.code == "operand_too_large" for i in result.issues)


def test_bullet_prefix_not_counted_as_operation():
    policy = policy_for_profile("standardowy", grade=2, topic_id="dodawanie_do_20")
    result = validate_tasks(["- Policz: 4 + 7 = ____"], policy)
    assert not any(i.code == "too_many_operations" for i in result.issues)


def test_liczenie_po_uses_sequence_format_and_grade_range():
    policy = policy_for_profile("trudności w nauce", grade=3, topic_id="liczenie_po")
    result = validate_tasks(
        [
            "Uzupełnij: 900, 800, 700, __, __",
            "Uzupełnij: 20, 30, 40, __, __",
        ],
        policy,
    )
    codes = {i.code for i in result.issues}
    assert "format_prefix" not in codes
    assert "operand_too_large" not in codes


def test_liczenie_po_rejects_wrong_prefix():
    policy = policy_for_profile("standardowy", grade=2, topic_id="liczenie_po")
    result = validate_tasks(["Policz: 10, 20, 30, __, __"], policy)
    assert any(i.code == "format_prefix" for i in result.issues)


def test_dysleksja_rejects_narrative_phrase():
    policy = policy_for_profile("dysleksja", grade=6, topic_id="ułamki")
    result = validate_tasks(
        ["Ania zjadła 1/3 ciasta. Policz ile zostało."],
        policy,
    )
    assert any(i.code == "forbidden_phrase" for i in result.issues)


def test_zdolny_allows_two_step_style():
    policy = policy_for_profile("zdolny", grade=5, topic_id="dodawanie")
    result = validate_tasks(
        ["Policz: 2 + 3, wynik pomnóż przez 4 = ____"],
        policy,
    )
    assert result.ok or not any(i.code == "too_many_operations" for i in result.issues)


def test_reference_criteria_merge_overrides_profile_cap():
    ref = StructuredQualityCriteria(max_operand=10, max_result=10, allowed_operations=("+",))
    result = validate_tasks_for_profile(
        ["Policz: 12 + 1 = ____"],
        profile_id="standardowy",
        grade=5,
        topic_id="mnożenie",
        reference_criteria=ref,
    )
    assert any(i.code == "operand_too_large" for i in result.issues)


def test_format_consistency_detected():
    criteria = StructuredQualityCriteria(require_format_consistent=True)
    result = validate_tasks(
        ["Policz: 2 + 2 = ____", "Oblicz: 3 + 1 = ____"],
        criteria,
    )
    assert any(i.code == "format_inconsistent" for i in result.issues)


def test_fraction_denominator_limit():
    criteria = StructuredQualityCriteria(
        allow_fractions=True,
        max_denominator=8,
        allowed_operations=("+", "−", "-"),
        max_operations_per_task=1,
    )
    result = validate_tasks(["Policz: 1/2 + 1/9 = ____"], criteria)
    assert any(i.code == "denominator_too_large" for i in result.issues)
