"""
v1.0: Proste wyciąganie odpowiedzi do klucza (tylko działania a op b).
"""
import re


def compute_answers(tasks: list[str]) -> list[str]:
    """
    Dla każdego zadania próbuje wyciągnąć wynik prostego działania (a op b).
    Zwraca listę stringów: wynik lub "—" gdy nie da się obliczyć.
    """
    return [_answer_for_task(t) for t in tasks]


def _answer_for_task(task: str) -> str:
    """Jedno zadanie: szuka wzorca 'liczba operator liczba', zwraca wynik lub '—'."""
    # Operator: + - − × * · / : ÷ (bez spacji w środku)
    m = re.search(r"(\d+)\s*([+*×·\-−/:÷])\s*(\d+)", task)
    if not m:
        return "—"
    try:
        a, b = int(m.group(1)), int(m.group(3))
        op = m.group(2).strip()
    except (ValueError, IndexError):
        return "—"
    if op in ("+",):
        return str(a + b)
    if op in ("-", "−"):
        return str(a - b)
    if op in ("*", "×", "·"):
        return str(a * b)
    if op in ("/", ":", "÷"):
        return str(a // b) if b != 0 else "—"
    return "—"
