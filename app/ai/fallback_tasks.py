"""Deterministic topic-preserving task fallbacks (P0.2)."""
from __future__ import annotations

from app.ai.profile_fallback_banks import apply_profile_to_standard_bank

def _cycle_take(items: list[str], n: int) -> list[str]:
    if n <= 0:
        return []
    out: list[str] = []
    while len(out) < n:
        out.extend(items)
    return out[:n]


def _grade_band(grade: int) -> int:
    if grade <= 1:
        return 1
    if grade == 2:
        return 2
    return 3


def fallback_tasks_for_topic(
    topic_id: str,
    grade: int,
    n: int,
    profile_id: str = "standardowy",
) -> list[str] | None:
    """
    Return deterministic tasks that preserve the requested topic.

  Profile-specific banks (topic × grade × profile_group) override or transform
    the standard bank when defined in `profile_fallback_banks`.
    """
    bank = _bank_for(topic_id, grade)
    if not bank:
        return None
    bank = apply_profile_to_standard_bank(bank, topic_id, grade, profile_id)
    if not bank:
        return None
    return _cycle_take(bank, n)


def _bank_for(topic_id: str, grade: int) -> list[str] | None:
    band = _grade_band(grade)
    if topic_id == "liczenie_po":
        return {
            1: [
                "Uzupełnij: 2, 4, 6, __, __",
                "Uzupełnij: 1, 3, 5, __, __",
                "Uzupełnij: 10, 12, 14, __, __",
            ],
            2: [
                "Uzupełnij: 10, 20, 30, __, __",
                "Uzupełnij: 5, 10, 15, __, __",
                "Uzupełnij: 22, 24, 26, __, __",
            ],
            3: [
                "Uzupełnij: 100, 200, 300, __, __",
                "Uzupełnij: 250, 260, 270, __, __",
                "Uzupełnij: 1000, 900, 800, __, __",
            ],
        }[band]
    if topic_id == "porownywanie_liczb":
        return {
            1: [
                "Wstaw znak < , > lub =: 7 __ 9",
                "Wstaw znak < , > lub =: 12 __ 12",
                "Wstaw znak < , > lub =: 15 __ 8",
            ],
            2: [
                "Wstaw znak < , > lub =: 45 __ 54",
                "Wstaw znak < , > lub =: 80 __ 80",
                "Wstaw znak < , > lub =: 36 __ 63",
            ],
            3: [
                "Wstaw znak < , > lub =: 345 __ 354",
                "Wstaw znak < , > lub =: 700 __ 700",
                "Wstaw znak < , > lub =: 199 __ 200",
            ],
        }[band]
    if topic_id in ("dodawanie_do_20", "dodawanie"):
        return [
            "Policz: 3 + 4 = ____",
            "Policz: 8 + 2 = ____",
            "Policz: 10 + 5 = ____",
            "Policz: 7 + 6 = ____",
        ]
    if topic_id == "dodawanie_do_100":
        return [
            "Policz: 23 + 14 = ____",
            "Policz: 45 + 8 = ____",
            "Policz: 60 + 30 = ____",
            "Policz: 27 + 36 = ____",
        ]
    if topic_id == "dodawanie_do_1000":
        return [
            "Policz: 250 + 50 = ____",
            "Policz: 180 + 30 = ____",
            "Policz: 400 + 250 = ____",
            "Policz: 320 + 70 = ____",
        ]
    if topic_id in ("odejmowanie_do_20", "odejmowanie"):
        return [
            "Policz: 9 − 3 = ____",
            "Policz: 15 − 5 = ____",
            "Policz: 10 − 4 = ____",
            "Policz: 18 − 8 = ____",
        ]
    if topic_id == "odejmowanie_do_100":
        return [
            "Policz: 45 − 14 = ____",
            "Policz: 80 − 30 = ____",
            "Policz: 56 − 8 = ____",
            "Policz: 90 − 25 = ____",
        ]
    if topic_id == "odejmowanie_do_1000":
        return [
            "Policz: 350 − 50 = ____",
            "Policz: 600 − 250 = ____",
            "Policz: 480 − 130 = ____",
            "Policz: 900 − 400 = ____",
        ]
    if topic_id in ("tabliczka_mnozenia", "mnozenie"):
        return [
            "Policz: 7 × 8 = ____",
            "Policz: 6 × 9 = ____",
            "Policz: 4 × 7 = ____",
            "Policz: 8 × 5 = ____",
        ]
    if topic_id == "mnozenie_przez_10":
        return [
            "Policz: 3 × 10 = ____",
            "Policz: 10 × 7 = ____",
            "Policz: 9 × 10 = ____",
            "Policz: 10 × 4 = ____",
        ]
    if topic_id == "dzielenie":
        if grade >= 7:
            return [
                "Policz: 256 : 16 = ____",
                "Policz: 144 : 12 = ____",
                "Policz: 420 : 15 = ____",
                "Policz: 4,2 : 0,7 = ____",
            ]
        if grade >= 5:
            return [
                "Policz: 1250 : 25 = ____",
                "Policz: 720 : 9 = ____",
                "Policz: 144 : 12 = ____",
                "Policz: 4,8 : 2 = ____",
            ]
        return [
            "Policz: 10 : 2 = ____",
            "Policz: 20 : 4 = ____",
            "Policz: 9 : 3 = ____",
            "Policz: 15 : 5 = ____",
        ]
    if topic_id == "rownania_z_okienkiem":
        return [
            "Uzupełnij okienko: 3 + ☐ = 7",
            "Uzupełnij okienko: ☐ + 5 = 10",
            "Uzupełnij okienko: 12 − ☐ = 4",
            "Uzupełnij okienko: ☐ − 3 = 6",
        ]
    if topic_id == "ulamki":
        if grade >= 7:
            return [
                "Policz: 2/3 + 1/3 = ____",
                "Policz: 7/8 − 3/8 = ____",
                "Policz: 3 × 2/5 = ____",
                "Policz: 5/6 − 1/6 = ____",
            ]
        if grade >= 4:
            return [
                "Policz: 1/4 + 2/4 = ____",
                "Policz: 2/5 + 1/5 = ____",
                "Policz: 5/8 − 1/8 = ____",
                "Policz: 3/6 + 2/6 = ____",
            ]
        return {
            1: [
                "Zaznacz połowę: pokoloruj 1 z 2 części koła.",
                "Pokoloruj ćwierć: 1 z 4 części kwadratu.",
                "Podziel prostokąt na 4 równe części.",
            ],
            2: [
                "Zaznacz połowę: pokoloruj 1 z 2 części kwadratu.",
                "Pokoloruj ćwierć: 1 z 4 części koła.",
                "Ile to jest połowa z 10? ____",
            ],
            3: [
                "Ile to jest połowa z 20? ____",
                "Ile to jest ćwierć z 8? ____",
                "Ile to jest połowa z 50? ____",
            ],
        }[band]
    if topic_id == "pieniadze":
        return [
            "Ile to razem? 5 zł + 2 zł = ____ zł",
            "Zamień: 3 zł = ____ gr",
            "Ile reszty z 10 zł, gdy zapłacono 6 zł? ____ zł",
        ]
    if topic_id == "czas":
        return [
            "Która godzina, gdy mała wskazówka pokazuje 3, a duża 12? ____",
            "Zegar elektroniczny: 14:00 to godzina ____",
            "Ile godzin od 8:00 do 12:00? ____",
        ]
    if topic_id == "pomiary_dlugosci":
        return [
            "Zamień: 2 m = ____ cm",
            "Zamień: 1 cm = ____ mm",
            "Ile cm to 5 m? ____",
        ]
    if topic_id == "obwody":
        return [
            "Oblicz obwód kwadratu o boku 4 cm. Obwód = ____ cm",
            "Oblicz obwód prostokąta o bokach 3 cm i 5 cm. Obwód = ____ cm",
            "Oblicz obwód kwadratu o boku 10 cm. Obwód = ____ cm",
        ]
    if topic_id == "zadania_tekstowe":
        return [
            "Ania miała 5 jabłek. Kupiła 4 jabłka. Ile ma jabłek? Odpowiedź: ____",
            "W koszyku było 10 kasztanów. Zabrano 3. Ile zostało? Odpowiedź: ____",
            "Tomek ma 7 klocków, Kasia ma 6. Ile mają razem? Odpowiedź: ____",
        ]
    if topic_id == "rownania":
        if grade >= 7:
            return [
                "Rozwiąż: ☐ + 35 = 120",
                "Rozwiąż: 7 × ☐ = 28",
                "Rozwiąż: ☐ − 6,5 = 2,5",
                "Rozwiąż: 84 : ☐ = 7",
            ]
        return [
            "Rozwiąż: ☐ + 8 = 15",
            "Rozwiąż: 4 × ☐ = 24",
            "Rozwiąż: ☐ − 12 = 7",
            "Rozwiąż: 72 : ☐ = 8",
        ]
    if topic_id == "procenty":
        return [
            "Policz: 10% z 200 = ____",
            "Policz: 25% z 80 = ____",
            "Ile to jest 15% z 60? ____",
            "Policz: 12% z 350 = ____",
        ]
    if topic_id == "potegi":
        if grade >= 8:
            return [
                "Policz: 2⁴ = ____",
                "Policz: √36 = ____",
                "Policz: √81 = ____",
                "Policz: 5³ = ____",
            ]
        return [
            "Policz: 2³ = ____",
            "Policz: 5² = ____",
            "Policz: 10² = ____",
            "Policz: 3³ = ____",
        ]
    if topic_id == "pitagoras":
        if grade >= 8:
            return [
                "Przyprostokątne 9 cm i 12 cm. Przeciwprostokątna c = ____ cm",
                "Przyprostokątne 8 cm i 15 cm. Przeciwprostokątna c = ____ cm",
                "Przyprostokątne 6 cm i 8 cm. Przeciwprostokątna c = ____ cm",
                "Przeciwprostokątna 25 cm, przyprostokątna 7 cm. Druga przyprostokątna a = ____ cm",
            ]
        return [
            "Przyprostokątne 3 cm i 4 cm. Przeciwprostokątna c = ____ cm",
            "Przyprostokątne 6 cm i 8 cm. Przeciwprostokątna c = ____ cm",
            "Przyprostokątne 5 cm i 12 cm. Przeciwprostokątna c = ____ cm",
            "Przeciwprostokątna 13 cm, przyprostokątna 5 cm. Druga przyprostokątna a = ____ cm",
        ]
    return None
