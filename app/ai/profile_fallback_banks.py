"""Profile-specific deterministic task banks (plan naprawczy profili)."""
from __future__ import annotations

import re

from app.domain.profile_pedagogy import ProfileGroup, profile_group


def _profile_band(topic_id: str, grade: int) -> int:
    """Mapowanie klasy na pasmo banku (ułamki mają osobne pasma 4–8)."""
    if topic_id == "ulamki":
        if grade <= 2:
            return 2
        if grade == 3:
            return 3
        if grade <= 6:
            return 4
        return 5
    if grade <= 1:
        return 1
    if grade == 2:
        return 2
    return 3


# topic_id -> grade_band -> profile_group -> lista zadań
_OVERRIDES: dict[str, dict[int, dict[str, list[str]]]] = {
    "dodawanie_do_20": {
        1: {
            "adhd": [
                "Policz: 2 + 3 = ____",
                "Policz: 4 + 1 = ____",
                "Policz: 5 + 2 = ____",
                "Policz: 3 + 4 = ____",
                "Policz: 6 + 1 = ____",
                "Policz: 2 + 6 = ____",
            ],
            "dyskalkulia": [
                "Policz: 1 + 8 = ____",
                "Policz: 2 + 7 = ____",
                "Policz: 4 + 5 = ____",
                "Policz: 3 + 2 = ____",
                "Policz: 5 + 1 = ____",
                "Policz: 6 + 2 = ____",
            ],
            "trudnosci": [
                "Policz: 4 + 5 = ____",
                "Policz: 3 + 4 = ____",
                "Policz: 6 + 2 = ____",
                "Policz: 5 + 3 = ____",
                "Policz: 7 + 2 = ____",
            ],
            "dysleksja": [
                "Policz: 5 + 3 = ____",
                "Policz: 2 + 6 = ____",
                "Policz: 4 + 4 = ____",
                "Policz: 1 + 9 = ____",
                "Policz: 6 + 7 = ____",
            ],
            "zdolny": [
                "Policz: 9 + 8 = ____",
                "Policz: 7 + 6 = ____",
                "Policz: 2 + 3, wynik pomnóż przez 2 = ____",
                "Policz: 4 + 5 = ____",
                "Policz: 6 + 7 = ____",
            ],
        },
        2: {
            "adhd": [
                "Policz: 7 + 2 = ____",
                "Policz: 8 + 1 = ____",
                "Policz: 6 + 3 = ____",
                "Policz: 9 + 1 = ____",
                "Policz: 5 + 4 = ____",
            ],
            "dyskalkulia": [
                "Policz: 7 + 5 = ____",
                "Policz: 8 + 4 = ____",
                "Policz: 6 + 6 = ____",
                "Policz: 9 + 3 = ____",
            ],
            "zdolny": [
                "Policz: 12 + 7 = ____",
                "Policz: 9 + 8 = ____",
                "Policz: 3 + 4, wynik pomnóż przez 2 = ____",
            ],
        },
    },
    "tabliczka_mnozenia": {
        2: {
            "adhd": [
                "Policz: 3 × 4 = ____",
                "Policz: 2 × 5 = ____",
                "Policz: 4 × 2 = ____",
                "Policz: 5 × 2 = ____",
                "Policz: 3 × 3 = ____",
            ],
            "dyskalkulia": [
                "Policz: 2 × 5 = ____",
                "Policz: 3 × 4 = ____",
                "Policz: 4 × 3 = ____",
                "Policz: 5 × 2 = ____",
            ],
            "trudnosci": [
                "Policz: 4 × 3 = ____",
                "Policz: 5 × 2 = ____",
                "Policz: 3 × 4 = ____",
            ],
            "zdolny": [
                "Policz: 7 × 8 = ____",
                "Policz: 6 × 9 = ____",
                "Policz: 2 × 5, wynik dodaj 10 = ____",
            ],
        },
        3: {
            "adhd": [
                "Policz: 4 × 5 = ____",
                "Policz: 3 × 6 = ____",
                "Policz: 5 × 3 = ____",
            ],
            "zdolny": [
                "Policz: 8 × 7 = ____",
                "Policz: 9 × 6 = ____",
            ],
        },
    },
    "odejmowanie_do_20": {
        1: {
            "adhd": [
                "Policz: 9 − 3 = ____",
                "Policz: 8 − 2 = ____",
                "Policz: 10 − 4 = ____",
                "Policz: 7 − 2 = ____",
            ],
            "dyskalkulia": [
                "Policz: 8 − 2 = ____",
                "Policz: 10 − 3 = ____",
                "Policz: 9 − 4 = ____",
            ],
        },
    },
    "liczenie_po": {
        1: {
            "trudnosci": [
                "Uzupełnij: 2, 4, 6, __, __",
                "Uzupełnij: 1, 3, 5, __, __",
                "Uzupełnij: 5, 10, 15, __, __",
            ],
            "adhd": [
                "Uzupełnij: 2, 4, 6, __, __",
                "Uzupełnij: 1, 3, 5, __, __",
            ],
        },
        2: {
            "trudnosci": [
                "Uzupełnij: 5, 10, 15, __, __",
                "Uzupełnij: 10, 20, 30, __, __",
                "Uzupełnij: 2, 4, 6, __, __",
            ],
            "adhd": [
                "Uzupełnij: 2, 4, 6, __, __",
                "Uzupełnij: 10, 12, 14, __, __",
            ],
        },
    },
    "ulamki": {
        2: {
            "adhd": [
                "Zaznacz połowę: pokoloruj 1 z 2 części kwadratu.",
                "Pokoloruj ćwierć: 1 z 4 części koła.",
            ],
            "dyskalkulia": [
                "Zaznacz połowę: pokoloruj 1 z 2 części koła.",
                "Pokoloruj ćwierć: 1 z 4 części kwadratu.",
            ],
            "trudnosci": [
                "Ile to jest połowa z 10? ____",
                "Ile to jest ćwierć z 8? ____",
            ],
        },
        3: {
            "adhd": [
                "Ile to jest połowa z 10? ____",
                "Ile to jest ćwierć z 8? ____",
            ],
            "dyskalkulia": [
                "Ile to jest połowa z 20? ____",
                "Ile to jest ćwierć z 8? ____",
            ],
            "zdolny": [
                "Ile to jest połowa z 20? ____",
                "Ile to jest ćwierć z 12? ____",
            ],
            "trudnosci": [
                "Ile to jest połowa z 16? ____",
                "Ile to jest ćwierć z 12? ____",
            ],
        },
        4: {
            "adhd": [
                "Policz: 1/4 + 2/4 = ____",
                "Policz: 2/5 + 1/5 = ____",
                "Policz: 3/6 − 1/6 = ____",
                "Policz: 4/6 + 1/6 = ____",
            ],
            "dyskalkulia": [
                "Policz: 1/4 + 2/4 = ____",
                "Policz: 2/5 + 1/5 = ____",
                "Policz: 4/6 − 1/6 = ____",
                "Policz: 1/3 + 1/3 = ____",
                "Policz: 5/6 − 2/6 = ____",
            ],
            "trudnosci": [
                "Policz: 1/4 + 2/4 = ____",
                "Policz: 2/5 + 1/5 = ____",
                "Policz: 3/6 + 1/6 = ____",
                "Policz: 4/6 − 1/6 = ____",
            ],
            "zdolny": [
                "Policz: 7/10 − 3/10 = ____",
                "Policz: 4/9 + 2/9 = ____",
                "Policz: 3/4 + 1/4, wynik pomnóż przez 2 = ____",
            ],
        },
        5: {
            "adhd": [
                "Policz: 2/3 + 1/3 = ____",
                "Policz: 5/6 − 1/6 = ____",
                "Policz: 4/5 − 2/5 = ____",
            ],
            "dyskalkulia": [
                "Policz: 2/3 + 1/3 = ____",
                "Policz: 5/6 − 1/6 = ____",
                "Policz: 3/4 − 1/4 = ____",
            ],
            "trudnosci": [
                "Policz: 2/3 + 1/3 = ____",
                "Policz: 5/6 − 1/6 = ____",
                "Policz: 7/8 − 3/8 = ____",
            ],
            "zdolny": [
                "Policz: 7/8 − 3/8 = ____",
                "Policz: 3 × 2/5 = ____",
                "Policz: 5/6 − 1/6, wynik dodaj 1/6 = ____",
            ],
        },
    },
    "pieniadze": {
        2: {
            "adhd": [
                "Ile razem? 3 zł + 2 zł = ____ zł",
                "Ile razem? 4 zł + 1 zł = ____ zł",
                "Zamień: 2 zł = ____ gr",
                "Ile reszty z 10 zł, gdy zapłacono 6 zł? ____ zł",
            ],
            "dyskalkulia": [
                "Ile razem? 5 zł + 2 zł = ____ zł",
                "Ile razem? 3 zł + 4 zł = ____ zł",
                "Zamień: 2 zł = ____ gr",
                "Ile reszty z 10 zł, gdy zapłacono 6 zł? ____ zł",
            ],
            "trudnosci": [
                "Ile razem? 5 zł + 3 zł = ____ zł",
                "Ile razem? 4 zł + 4 zł = ____ zł",
                "Zamień: 3 zł = ____ gr",
            ],
            "zdolny": [
                "Ile zostaje z 15 zł po wydaniu 9 zł (wyjaśnij sposób)? Odpowiedź: ____ zł",
                "Ile razem? 8 zł + 7 zł = ____ zł",
            ],
        },
        3: {
            "adhd": [
                "Ile razem? 10 zł + 5 zł = ____ zł",
                "Zamień: 5 zł = ____ gr",
                "Ile reszty z 20 zł, gdy zapłacono 12 zł? ____ zł",
            ],
            "dyskalkulia": [
                "Ile razem? 12 zł + 8 zł = ____ zł",
                "Ile razem? 25 zł + 15 zł = ____ zł",
                "Zamień: 5 zł = ____ gr",
                "Ile reszty z 50 zł, gdy zapłacono 32 zł? ____ zł",
            ],
            "zdolny": [
                "Ile razem? 35 zł + 28 zł = ____ zł",
                "Zamień: 10 zł = ____ gr",
                "Ile zostaje z 50 zł po zapłacie 32 zł (wyjaśnij sposób)? Odpowiedź: ____ zł",
            ],
        },
    },
    "czas": {
        1: {
            "adhd": [
                "Która godzina, gdy mała wskazówka pokazuje 3, a duża 12? ____",
                "Która godzina, gdy mała wskazówka pokazuje 6, a duża 12? ____",
                "Która godzina, gdy mała wskazówka pokazuje 9, a duża 12? ____",
            ],
            "dyskalkulia": [
                "Która godzina, gdy mała wskazówka pokazuje 2, a duża 12? ____",
                "Która godzina, gdy mała wskazówka pokazuje 5, a duża 12? ____",
            ],
            "trudnosci": [
                "Która godzina, gdy mała wskazówka pokazuje 4, a duża 12? ____",
                "Która godzina, gdy mała wskazówka pokazuje 8, a duża 12? ____",
            ],
        },
        2: {
            "adhd": [
                "Która godzina, gdy mała wskazówka pokazuje 3, a duża 12? ____",
                "Ile godzin od 8:00 do 10:00? ____",
            ],
            "dyskalkulia": [
                "Która godzina, gdy mała wskazówka pokazuje 7, a duża 12? ____",
                "Ile godzin od 9:00 do 11:00? ____",
            ],
            "zdolny": [
                "Zegar elektroniczny: 14:00 to godzina ____",
                "Ile godzin od 8:00 do 12:00? Wyjaśnij sposób. ____",
            ],
        },
        3: {
            "adhd": [
                "Zegar elektroniczny: 10:00 to godzina ____",
                "Ile godzin od 7:00 do 9:00? ____",
            ],
            "trudnosci": [
                "Ile godzin od 8:00 do 11:00? ____",
                "Zegar elektroniczny: 15:00 to godzina ____",
            ],
        },
    },
    "obwody": {
        2: {
            "adhd": [
                "Obwód kwadratu o boku 4 cm = ____ cm",
                "Obwód prostokąta o bokach 3 cm i 5 cm = ____ cm",
            ],
            "dyskalkulia": [
                "Obwód kwadratu o boku 4 cm. Obwód = ____ cm",
                "Obwód prostokąta o bokach 3 cm i 5 cm. Obwód = ____ cm",
            ],
            "trudnosci": [
                "Obwód kwadratu o boku 5 cm. Obwód = ____ cm",
                "Obwód prostokąta o bokach 4 cm i 6 cm. Obwód = ____ cm",
            ],
            "zdolny": [
                "Obwód kwadratu o boku 10 cm. Obwód = ____ cm",
                "Obwód prostokąta o bokach 6 cm i 8 cm. Obwód = ____ cm",
            ],
        },
        3: {
            "adhd": [
                "Obwód kwadratu o boku 6 cm. Obwód = ____ cm",
                "Obwód prostokąta o bokach 4 cm i 7 cm. Obwód = ____ cm",
            ],
            "dyskalkulia": [
                "Obwód kwadratu o boku 8 cm. Obwód = ____ cm",
                "Obwód prostokąta o bokach 5 cm i 9 cm. Obwód = ____ cm",
            ],
        },
    },
    "pomiary_dlugosci": {
        2: {
            "adhd": [
                "Zamień: 2 m = ____ cm",
                "Zamień: 1 cm = ____ mm",
            ],
            "dyskalkulia": [
                "Zamień: 1 m = ____ cm",
                "Zamień: 2 cm = ____ mm",
            ],
            "trudnosci": [
                "Zamień: 3 m = ____ cm",
                "Ile cm to 2 m? ____",
            ],
        },
        3: {
            "adhd": [
                "Zamień: 3 m = ____ cm",
                "Ile cm to 4 m? ____",
            ],
            "zdolny": [
                "Ile cm to 5 m? ____",
                "Zamień: 250 cm = ____ m",
            ],
        },
    },
    "zadania_tekstowe": {
        1: {
            "adhd": [
                "Ania miała 3 jabłka. Dostała 2. Ile ma? Odpowiedź: ____",
                "Na talerzu było 8 ciastek. Zjedzono 3. Ile zostało? Odpowiedź: ____",
                "Tomek ma 4 klocki. Kasia ma 3. Ile razem? Odpowiedź: ____",
            ],
            "dyskalkulia": [
                "Ania miała 5 jabłek. Kupiła 4 jabłka. Ile ma jabłek? Odpowiedź: ____",
                "W koszyku było 10 kasztanów. Zabrano 3. Ile zostało? Odpowiedź: ____",
            ],
            "trudnosci": [
                "Masz 6 jabłek. Dodaj 3. Ile razem? Odpowiedź: ____",
                "Było 9 klocków. Zabierz 4. Ile zostało? Odpowiedź: ____",
            ],
            "dysleksja": [
                "Masz 4 jabłka. Dodaj 3. Ile razem? Odpowiedź: ____",
                "Było 7 guzików. Zabierz 2. Ile zostało? Odpowiedź: ____",
            ],
            "zdolny": [
                "Masz 8 jabłek. Dodaj 5. Ile razem? Wyjaśnij sposób. Odpowiedź: ____",
                "Było 10 klocków. Zabierz 3. Ile zostało? Odpowiedź: ____",
            ],
        },
        2: {
            "standardowy": [
                "Ania miała 5 jabłek. Kupiła 4 jabłka. Ile ma jabłek? Odpowiedź: ____",
                "W koszyku było 10 kasztanów. Zabrano 3. Ile zostało? Odpowiedź: ____",
            ],
            "adhd": [
                "Masz 5 jabłek. Dodaj 4. Ile razem? Odpowiedź: ____",
                "Było 10 kasztanów. Zabierz 3. Ile zostało? Odpowiedź: ____",
            ],
            "dyskalkulia": [
                "Ania miała 5 jabłek. Kupiła 4 jabłka. Ile ma jabłek? Odpowiedź: ____",
                "W koszyku było 10 kasztanów. Zabrano 3. Ile zostało? Odpowiedź: ____",
            ],
            "trudnosci": [
                "Masz 7 klocków. Dodaj 5. Ile razem? Odpowiedź: ____",
                "Było 12 crayonów. Zabierz 5. Ile zostało? Odpowiedź: ____",
            ],
            "dysleksja": [
                "Masz 5 jabłek. Dodaj 4. Ile razem? Odpowiedź: ____",
                "Było 10 kasztanów. Zabierz 3. Ile zostało? Odpowiedź: ____",
            ],
            "zdolny": [
                "Masz 12 zł. Kupujesz za 7 zł. Ile zostaje? Wyjaśnij sposób. Odpowiedź: ____",
                "3 pudełka po 4 cukierki. Ile cukierków? Odpowiedź: ____",
            ],
        },
        3: {
            "standardowy": [
                "W skrzyni było 120 klocków. Dodano 45. Ile jest teraz? Odpowiedź: ____",
                "Na półce było 200 książek. Zabrano 75. Ile zostało? Odpowiedź: ____",
            ],
            "adhd": [
                "W pudełku było 50 klocków. Dodano 20. Ile jest? Odpowiedź: ____",
                "Na półce było 80 książek. Zabrano 25. Ile zostało? Odpowiedź: ____",
            ],
            "dyskalkulia": [
                "W koszyku było 60 jabłek. Dodano 15. Ile jest? Odpowiedź: ____",
                "Było 90 kasztanów. Zabrano 30. Ile zostało? Odpowiedź: ____",
            ],
            "trudnosci": [
                "W skrzyni było 80 klocków. Dodano 20. Ile jest? Odpowiedź: ____",
                "Na półce było 100 książek. Zabrano 35. Ile zostało? Odpowiedź: ____",
            ],
            "dysleksja": [
                "W skrzyni było 120 klocków. Dodano 45. Ile jest? Odpowiedź: ____",
                "Na półce było 200 książek. Zabrano 75. Ile zostało? Odpowiedź: ____",
            ],
            "zdolny": [
                "Pierwsza grupa ma 150 uczniów, druga 120. Ile razem? Wyjaśnij sposób. Odpowiedź: ____",
                "W magazynie było 500 kg ryżu. Sprzedano 180 kg. Ile zostało? Odpowiedź: ____",
            ],
        },
    },
}


def profile_bank_for_topic(
    topic_id: str,
    grade: int,
    pg: ProfileGroup,
) -> list[str] | None:
    """Zwraca bank profilowy lub None, gdy brak nadpisania."""
    if pg == "standardowy":
        return None

    band = _profile_band(topic_id, grade)
    topic_map = _OVERRIDES.get(topic_id)
    if not topic_map:
        return None
    band_map = topic_map.get(band)
    if not band_map:
        return None
    bank = band_map.get(pg)
    if bank is not None:
        return bank if bank else []  # jawna pusta lista = zakaz narracji
    return None


def apply_profile_to_standard_bank(
    bank: list[str],
    topic_id: str,
    grade: int,
    profile_id: str,
) -> list[str]:
    """
    Transformuje standardowy bank, gdy brak jawnego nadpisania.
    """
    pg = profile_group(profile_id)
    override = profile_bank_for_topic(topic_id, grade, pg)
    if override is not None:
        return override

    if pg == "standardowy":
        return bank

    if pg == "zdolny":
        enriched = _maybe_enrich_bank(bank, topic_id)
        if enriched:
            return enriched

    if topic_id == "ulamki" and pg in ("adhd", "dyskalkulia", "trudnosci", "grafomotoryka"):
        shrunk = _shrink_fraction_bank(bank, pg, grade)
        if shrunk:
            return shrunk

    if pg in ("adhd", "dyskalkulia", "trudnosci", "grafomotoryka"):
        shrunk = _shrink_arithmetic_bank(bank, pg, grade)
        if shrunk:
            return shrunk

    if pg == "dysleksja":
        return [_shorten_wording(t) for t in bank]

    return bank


def _maybe_enrich_bank(bank: list[str], topic_id: str) -> list[str] | None:
    enrich_topics = (
        "dodawanie_do_20",
        "dodawanie",
        "mnozenie",
        "tabliczka_mnozenia",
        "ulamki",
        "pieniadze",
        "zadania_tekstowe",
    )
    if topic_id not in enrich_topics:
        return None
    out: list[str] = []
    for i, t in enumerate(bank):
        if i % 3 == 2 and "," not in t:
            if topic_id == "ulamki" and "Policz:" in t:
                m = re.match(
                    r"Policz:\s*(\d+)/(\d+)\s*([+\-−])\s*(\d+)/(\d+)\s*=", t
                )
                if m and m.group(2) == m.group(5) and m.group(3) in ("+", "−", "-"):
                    n1, d, op, n2 = m.group(1), m.group(2), m.group(3), m.group(4)
                    out.append(f"Policz: {n1}/{d} {op} {n2}/{d}, wynik pomnóż przez 2 = ____")
                    continue
            if topic_id == "zadania_tekstowe" and "Odpowiedź:" in t and "Wyjaśnij" not in t:
                out.append(
                    t.replace("Odpowiedź:", "Wyjaśnij sposób. Odpowiedź:", 1)
                )
                continue
            if "Policz:" in t:
                m = re.match(r"Policz:\s*(\d+)\s*([+\-−×x*])\s*(\d+)\s*=", t)
                if m and m.group(2) in ("+", "−", "-"):
                    a, b = int(m.group(1)), int(m.group(3))
                    op = m.group(2)
                    if op == "+":
                        out.append(f"Policz: {a} {op} {b}, wynik pomnóż przez 2 = ____")
                    else:
                        out.append(f"Policz: {a} {op} {b} = ____")
                    continue
        out.append(t)
    return out


def _shrink_arithmetic_bank(
    bank: list[str],
    pg: ProfileGroup,
    grade: int,
) -> list[str] | None:
    max_op = 10 if pg == "adhd" else 12 if pg == "dyskalkulia" else 15
    if grade >= 3:
        max_op = min(max_op + 5, 20)

    out: list[str] = []
    for t in bank:
        m = re.search(r"Policz:\s*(\d+)\s*([+\-−×x*÷/:])\s*(\d+)", t)
        if not m:
            if pg in ("adhd", "dyskalkulia", "trudnosci") and _looks_like_word_problem(t):
                continue
            out.append(t)
            continue
        a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
        if a > max_op or b > max_op:
            continue
        if op in ("+", "−", "-") and a + b > max_op + 8:
            continue
        if op in ("×", "x", "*") and a * b > 100:
            continue
        out.append(t)
    return out if out else None


def _shrink_fraction_bank(
    bank: list[str],
    pg: ProfileGroup,
    grade: int,
) -> list[str] | None:
    """Filtruje ułamki z banku standardowego (mianownik / licznik zgodnie z profilem)."""
    max_den = 6 if pg == "dyskalkulia" else 8 if pg == "adhd" else 10
    max_num = 6 if pg == "adhd" else 8
    out: list[str] = []
    for t in bank:
        fracs = re.findall(r"(\d+)\s*/\s*(\d+)", t)
        if not fracs:
            if pg in ("adhd", "trudnosci", "grafomotoryka") and any(
                w in t.casefold() for w in ("połowa", "ćwierć", "pokoloruj", "zaznacz")
            ):
                out.append(t)
            elif pg == "dyskalkulia" and "połowa" in t.casefold():
                out.append(t)
            continue
        if all(int(d) <= max_den and int(n) <= max_num for n, d in fracs):
            if "×" in t or "x" in t.lower():
                if pg == "adhd":
                    continue
            out.append(t)
    return out if out else None


def _looks_like_word_problem(task: str) -> bool:
    lowered = task.casefold()
    markers = ("ania", "tomek", "kupił", "kupiła", "miał", "miała", "w sklepie", "jabłek")
    return any(m in lowered for m in markers)


def _shorten_wording(task: str) -> str:
    """Skraca typowe narracje bez zmiany liczb."""
    replacements = (
        ("Ania miała ", "Masz "),
        ("Kupiła ", "Dodaj "),
        ("kupiła ", "dodaj "),
        ("Zabrano ", "Odejmij "),
        ("zabrano ", "odejmij "),
        ("Ile ma jabłek?", "Ile razem?"),
        ("Ile zostało?", "Ile zostaje?"),
    )
    out = task
    for old, new in replacements:
        out = out.replace(old, new)
    return out
