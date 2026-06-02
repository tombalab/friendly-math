"""
TOPIC_BLUEPRINTS – centralny rejestr „co znaczy temat X dla klasy Y".

Każdy blueprint zawiera:
- `instruction`:  instrukcję, którą wkleimy do prompta (zakres liczb, formaty),
- `examples`:     2-4 przykładowe zadania (few-shot),
- `max_result`:   górny limit wyniku do walidacji numerycznej (opcjonalny),
- `format_hint`:  jak ma wyglądać linia zadania (dla parserów/odpowiedzi).

Pokrycie zgodne z podstawą programową edukacji wczesnoszkolnej (klasy 1–3),
[zpe.gov.pl/podstawa-programowa/edukacja-wczesnoszkolna]. Dla klas 4-8 zostawiamy
ogólne ścieżki (dodawanie/odejmowanie/mnożenie/dzielenie/ułamki/równania).

Klucze (topic): zgodne z opcjami w UI (selectbox „Zakres materiału").
Klucze (grade): int 1-8. Dla ciągłości – jeśli blueprint nie ma wpisu dla danej
klasy, używamy najbliższego niższego (downgrade) lub wpisu „default" tematu.
"""
from __future__ import annotations

from typing import Optional, TypedDict


class Blueprint(TypedDict, total=False):
    instruction: str
    examples: str
    max_result: int
    format_hint: str


# --------------------------------------------------------------------
# Pomocnicze – wspólne formaty/przykłady
# --------------------------------------------------------------------

_BOX = "☐"  # symbol „okienka" dla równań typu 3 + ☐ = 7


def _ex(*lines: str) -> str:
    """Składa kilka linii przykładów w blok few-shot."""
    return "\n".join(f"- {line}" for line in lines)


# --------------------------------------------------------------------
# Rejestr: topic -> grade -> Blueprint
# --------------------------------------------------------------------

TOPIC_BLUEPRINTS: dict[str, dict[int, Blueprint]] = {

    # ----- Dodawanie -----
    "dodawanie do 20": {
        1: {
            "instruction": (
                "Dodawanie w zakresie 0–20, BEZ przekraczania progu dziesiątkowego "
                "w klasie 1 jeśli to możliwe. Liczby jednocyfrowe lub +10. "
                "Format: „Policz: a + b = ____”."
            ),
            "examples": _ex(
                "Policz: 3 + 4 = ____",
                "Policz: 8 + 2 = ____",
                "Policz: 10 + 5 = ____",
                "Policz: 7 + 6 = ____",
            ),
            "max_result": 20,
        },
        2: {
            "instruction": "Dodawanie w zakresie 0–20, w tym z przekroczeniem progu 10.",
            "examples": _ex(
                "Policz: 7 + 8 = ____",
                "Policz: 9 + 6 = ____",
                "Policz: 12 + 7 = ____",
                "Policz: 5 + 9 = ____",
            ),
            "max_result": 20,
        },
        3: {
            "instruction": (
                "Powtórka i automatyzacja dodawania w zakresie 0–20 dla klasy 3. "
                "Krótkie przykłady pamięciowe, jeden krok, w tym przekroczenie progu 10. "
                "Format: „Policz: a + b = ____”."
            ),
            "examples": _ex(
                "Policz: 8 + 7 = ____",
                "Policz: 9 + 8 = ____",
                "Policz: 12 + 6 = ____",
                "Policz: 14 + 5 = ____",
            ),
            "max_result": 20,
        },
    },

    "dodawanie do 100": {
        2: {
            "instruction": (
                "Dodawanie liczb dwucyfrowych w zakresie 0–100. Można mieszać: "
                "liczba dwucyfrowa + jednocyfrowa, liczba dwucyfrowa + dziesiątka, "
                "dwucyfrowa + dwucyfrowa."
            ),
            "examples": _ex(
                "Policz: 23 + 14 = ____",
                "Policz: 45 + 8 = ____",
                "Policz: 60 + 30 = ____",
                "Policz: 27 + 36 = ____",
            ),
            "max_result": 100,
        },
        3: {
            "instruction": (
                "Dodawanie liczb dwucyfrowych w zakresie 0–100, w tym z przekraczaniem "
                "pełnych dziesiątek (typu 38 + 47)."
            ),
            "examples": _ex(
                "Policz: 38 + 47 = ____",
                "Policz: 56 + 29 = ____",
                "Policz: 72 + 18 = ____",
                "Policz: 85 + 7 = ____",
            ),
            "max_result": 100,
        },
    },

    "dodawanie do 1000": {
        3: {
            "instruction": (
                "Dodawanie liczb trzycyfrowych w prostych przykładach (np. 250 + 50, "
                "180 + 30, 400 + 250). Unikaj złożonych pisemnych algorytmów."
            ),
            "examples": _ex(
                "Policz: 250 + 50 = ____",
                "Policz: 180 + 30 = ____",
                "Policz: 400 + 250 = ____",
                "Policz: 320 + 70 = ____",
            ),
            "max_result": 1000,
        },
    },

    # ----- Odejmowanie -----
    "odejmowanie do 20": {
        1: {
            "instruction": (
                "Odejmowanie w zakresie 0–20, najlepiej bez przekraczania progu 10 "
                "w klasie 1. Wynik zawsze ≥ 0."
            ),
            "examples": _ex(
                "Policz: 9 − 3 = ____",
                "Policz: 15 − 5 = ____",
                "Policz: 10 − 4 = ____",
                "Policz: 18 − 8 = ____",
            ),
            "max_result": 20,
        },
        2: {
            "instruction": (
                "Odejmowanie w zakresie 0–20, w tym z przekroczeniem progu 10 "
                "(np. 13 − 7). Wynik zawsze ≥ 0."
            ),
            "examples": _ex(
                "Policz: 13 − 7 = ____",
                "Policz: 15 − 8 = ____",
                "Policz: 11 − 4 = ____",
                "Policz: 17 − 9 = ____",
            ),
            "max_result": 20,
        },
        3: {
            "instruction": (
                "Powtórka i automatyzacja odejmowania w zakresie 0–20 dla klasy 3. "
                "Krótkie przykłady pamięciowe, jeden krok, w tym przekroczenie progu 10. "
                "Wynik zawsze ≥ 0."
            ),
            "examples": _ex(
                "Policz: 16 − 7 = ____",
                "Policz: 18 − 9 = ____",
                "Policz: 14 − 6 = ____",
                "Policz: 20 − 8 = ____",
            ),
            "max_result": 20,
        },
    },

    "odejmowanie do 100": {
        2: {
            "instruction": (
                "Odejmowanie liczb dwucyfrowych w zakresie 0–100 w prostych przykładach. "
                "Wynik ≥ 0."
            ),
            "examples": _ex(
                "Policz: 45 − 14 = ____",
                "Policz: 80 − 30 = ____",
                "Policz: 56 − 8 = ____",
                "Policz: 90 − 25 = ____",
            ),
            "max_result": 100,
        },
        3: {
            "instruction": (
                "Odejmowanie liczb dwucyfrowych w zakresie 0–100, w tym z pożyczaniem "
                "(typu 62 − 28). Wynik ≥ 0."
            ),
            "examples": _ex(
                "Policz: 62 − 28 = ____",
                "Policz: 73 − 49 = ____",
                "Policz: 84 − 37 = ____",
                "Policz: 100 − 45 = ____",
            ),
            "max_result": 100,
        },
    },

    "odejmowanie do 1000": {
        3: {
            "instruction": (
                "Odejmowanie liczb trzycyfrowych w prostych przykładach (np. 350 − 50, "
                "600 − 250). Wynik ≥ 0."
            ),
            "examples": _ex(
                "Policz: 350 − 50 = ____",
                "Policz: 600 − 250 = ____",
                "Policz: 480 − 130 = ____",
                "Policz: 900 − 400 = ____",
            ),
            "max_result": 1000,
        },
    },

    # ----- Mnożenie -----
    "tabliczka mnożenia": {
        2: {
            "instruction": (
                "Mnożenie w zakresie tabliczki mnożenia – tylko czynniki 1–5 dla klasy 2 "
                "(np. 2×3, 4×5, 3×3). Format: „Policz: a × b = ____”."
            ),
            "examples": _ex(
                "Policz: 2 × 3 = ____",
                "Policz: 4 × 5 = ____",
                "Policz: 3 × 3 = ____",
                "Policz: 5 × 4 = ____",
            ),
            "max_result": 25,
        },
        3: {
            "instruction": (
                "Mnożenie w PEŁNYM zakresie tabliczki mnożenia – czynniki 1–10. "
                "Format: „Policz: a × b = ____”."
            ),
            "examples": _ex(
                "Policz: 7 × 8 = ____",
                "Policz: 6 × 9 = ____",
                "Policz: 4 × 7 = ____",
                "Policz: 8 × 5 = ____",
            ),
            "max_result": 100,
        },
    },

    "mnożenie przez 10": {
        2: {
            "instruction": (
                "Mnożenie liczby jednocyfrowej (1–9) przez 10. Format: "
                "„Policz: a × 10 = ____” lub „Policz: 10 × a = ____”."
            ),
            "examples": _ex(
                "Policz: 3 × 10 = ____",
                "Policz: 10 × 7 = ____",
                "Policz: 9 × 10 = ____",
                "Policz: 10 × 4 = ____",
            ),
            "max_result": 100,
        },
        3: {
            "instruction": (
                "Mnożenie liczby mniejszej od 20 przez 10 "
                "(np. 12 × 10, 10 × 15, 18 × 10). Wynik nie przekracza 200."
            ),
            "examples": _ex(
                "Policz: 12 × 10 = ____",
                "Policz: 10 × 15 = ____",
                "Policz: 18 × 10 = ____",
                "Policz: 10 × 11 = ____",
            ),
            "max_result": 200,
        },
    },

    # ----- Dzielenie -----
    "dzielenie": {
        2: {
            "instruction": (
                "Dzielenie w zakresie tabliczki mnożenia, ograniczone czynnikami 1–5 "
                "dla klasy 2 (np. 10 : 2, 20 : 4, 9 : 3). Wynik zawsze całkowity."
            ),
            "examples": _ex(
                "Policz: 10 : 2 = ____",
                "Policz: 20 : 4 = ____",
                "Policz: 9 : 3 = ____",
                "Policz: 15 : 5 = ____",
            ),
            "max_result": 25,
        },
        3: {
            "instruction": (
                "Dzielenie w PEŁNYM zakresie tabliczki mnożenia – dzielnik 1–10, "
                "dzielna ≤ 100, wynik zawsze całkowity (bez reszty)."
            ),
            "examples": _ex(
                "Policz: 56 : 7 = ____",
                "Policz: 72 : 9 = ____",
                "Policz: 48 : 6 = ____",
                "Policz: 81 : 9 = ____",
            ),
            "max_result": 100,
        },
    },

    # ----- Liczby i porównywanie -----
    "porównywanie liczb": {
        1: {
            "instruction": (
                "Porównywanie liczb w zakresie 0–20 znakami < , > lub =. "
                "Format: „Wstaw znak < , > lub =: a __ b”."
            ),
            "examples": _ex(
                "Wstaw znak < , > lub =: 7 __ 9",
                "Wstaw znak < , > lub =: 12 __ 12",
                "Wstaw znak < , > lub =: 15 __ 8",
                "Wstaw znak < , > lub =: 10 __ 14",
            ),
        },
        2: {
            "instruction": (
                "Porównywanie liczb w zakresie 0–100 znakami < , > lub =. "
                "Format: „Wstaw znak < , > lub =: a __ b”."
            ),
            "examples": _ex(
                "Wstaw znak < , > lub =: 45 __ 54",
                "Wstaw znak < , > lub =: 80 __ 80",
                "Wstaw znak < , > lub =: 36 __ 63",
                "Wstaw znak < , > lub =: 99 __ 100",
            ),
        },
        3: {
            "instruction": (
                "Porównywanie liczb w zakresie 0–1000 znakami < , > lub =. "
                "Format: „Wstaw znak < , > lub =: a __ b”."
            ),
            "examples": _ex(
                "Wstaw znak < , > lub =: 345 __ 354",
                "Wstaw znak < , > lub =: 700 __ 700",
                "Wstaw znak < , > lub =: 199 __ 200",
                "Wstaw znak < , > lub =: 489 __ 498",
            ),
        },
    },

    "liczenie po": {
        1: {
            "instruction": (
                "Uzupełnij ciąg liczb (liczenie po 1 lub po 2 w zakresie 0–20) – "
                "podaj 4–5 liczb i postaw puste pole na ostatnich pozycjach. "
                "Format: „Uzupełnij: 2, 4, 6, __, __”."
            ),
            "examples": _ex(
                "Uzupełnij: 2, 4, 6, __, __",
                "Uzupełnij: 10, 12, 14, __, __",
                "Uzupełnij: 1, 3, 5, __, __",
                "Uzupełnij: 18, 16, 14, __, __",
            ),
        },
        2: {
            "instruction": (
                "Uzupełnij ciąg liczb po 2, po 5 lub po 10 w zakresie 0–100. "
                "Format: „Uzupełnij: a, b, c, __, __”."
            ),
            "examples": _ex(
                "Uzupełnij: 10, 20, 30, __, __",
                "Uzupełnij: 5, 10, 15, __, __",
                "Uzupełnij: 50, 48, 46, __, __",
                "Uzupełnij: 22, 24, 26, __, __",
            ),
        },
        3: {
            "instruction": (
                "Uzupełnij ciąg liczb po 10 lub po 100 w zakresie 0–1000. "
                "Format: „Uzupełnij: a, b, c, __, __”."
            ),
            "examples": _ex(
                "Uzupełnij: 100, 200, 300, __, __",
                "Uzupełnij: 250, 260, 270, __, __",
                "Uzupełnij: 800, 810, 820, __, __",
                "Uzupełnij: 1000, 900, 800, __, __",
            ),
        },
    },

    # ----- Równania z okienkiem -----
    "równania z okienkiem": {
        1: {
            "instruction": (
                f"Równania z niewiadomą w postaci okienka {_BOX} w zakresie 0–20. "
                f"Format: „Uzupełnij okienko: a + {_BOX} = c” lub "
                f"„Uzupełnij okienko: {_BOX} − b = c”."
            ),
            "examples": _ex(
                f"Uzupełnij okienko: 3 + {_BOX} = 7",
                f"Uzupełnij okienko: {_BOX} + 5 = 10",
                f"Uzupełnij okienko: 12 − {_BOX} = 4",
                f"Uzupełnij okienko: {_BOX} − 3 = 6",
            ),
            "max_result": 20,
        },
        2: {
            "instruction": (
                f"Równania z niewiadomą w okienku {_BOX} w zakresie 0–100, "
                f"z dodawaniem, odejmowaniem, mnożeniem przez liczbę 1-5."
            ),
            "examples": _ex(
                f"Uzupełnij okienko: 35 + {_BOX} = 50",
                f"Uzupełnij okienko: {_BOX} − 8 = 24",
                f"Uzupełnij okienko: 4 × {_BOX} = 20",
                f"Uzupełnij okienko: {_BOX} + 17 = 40",
            ),
            "max_result": 100,
        },
        3: {
            "instruction": (
                f"Równania z niewiadomą w okienku {_BOX} – wszystkie 4 działania, "
                f"liczby do 100. Format: „Uzupełnij okienko: …”."
            ),
            "examples": _ex(
                f"Uzupełnij okienko: 56 − {_BOX} = 23",
                f"Uzupełnij okienko: {_BOX} : 6 = 8",
                f"Uzupełnij okienko: 7 × {_BOX} = 56",
                f"Uzupełnij okienko: 25 + {_BOX} = 60",
            ),
            "max_result": 100,
        },
    },

    # ----- Ułamki -----
    "ułamki": {
        # Klasy 1-3: tylko intuicyjne pojęcia (połowa, ćwierć)
        2: {
            "instruction": (
                "Intuicyjne pojęcia ułamków – połowa, ćwierć, cztery równe części. "
                "Bez zapisu a/b, tylko zdania typu „Zaznacz połowę…”, "
                "„Pokoloruj ćwierć…”, „Podziel na 4 równe części”. "
                "Format zdaniowy, jeden krok."
            ),
            "examples": _ex(
                "Zaznacz połowę: pokoloruj 1 z 2 części kwadratu.",
                "Pokoloruj ćwierć: 1 z 4 części koła.",
                "Podziel kwadrat na 4 równe części.",
                "Ile to jest połowa z 10? ____",
            ),
        },
        3: {
            "instruction": (
                "Intuicyjne pojęcia: połowa, ćwierć, dwa i pół. Pytania typu "
                "„Ile to jest połowa z 20?”, „Ile to ćwierć z 8?”."
            ),
            "examples": _ex(
                "Ile to jest połowa z 20? ____",
                "Ile to jest ćwierć z 8? ____",
                "Ile to jest połowa z 50? ____",
                "Ile to są dwa i pół jabłka, gdy jedno = 4 plasterki? ____ plasterków",
            ),
            "max_result": 1000,
        },
        # Klasy 4+: ułamki w zapisie a/b (jak dotąd)
        4: {
            "instruction": (
                "Ułamki zwykłe w zapisie licznik/mianownik (np. 1/2, 3/4, 2/5). "
                "Operacje na ułamkach o tych samych mianownikach."
            ),
            "examples": _ex(
                "Policz: 1/4 + 1/4 = ____",
                "Policz: 2/5 + 1/5 = ____",
                "Policz: 3/8 + 2/8 = ____",
                "Policz: 5/6 − 2/6 = ____",
            ),
        },
    },

    # ----- Pieniądze -----
    "pieniądze": {
        2: {
            "instruction": (
                "Obliczenia pieniężne na monetach i banknotach: złote i grosze. "
                "Format zdaniowy: „Ile to razem? 5 zł + 2 zł 50 gr = ____” lub "
                "„Zamień: 3 zł = ____ gr”."
            ),
            "examples": _ex(
                "Ile to razem? 5 zł + 2 zł = ____ zł",
                "Zamień: 3 zł = ____ gr",
                "Ile reszty z 10 zł, gdy zapłacono 6 zł? ____ zł",
                "Ile to razem? 50 gr + 50 gr = ____ zł",
            ),
        },
        3: {
            "instruction": (
                "Obliczenia pieniężne w zakresie do 100 zł, z groszami. "
                "Zamiana zł na gr i odwrotnie (1 zł = 100 gr)."
            ),
            "examples": _ex(
                "Zamień: 2 zł 50 gr = ____ gr",
                "Ile to razem? 12 zł 80 gr + 5 zł 20 gr = ____ zł",
                "Ile reszty z 50 zł, gdy zapłacono 37 zł? ____ zł",
                "Zamień: 350 gr = ____ zł ____ gr",
            ),
        },
    },

    # ----- Czas -----
    "czas": {
        1: {
            "instruction": (
                "Odczytywanie pełnych godzin na zegarze ze wskazówkami. "
                "Format zdaniowy."
            ),
            "examples": _ex(
                "Która godzina, gdy mała wskazówka pokazuje 3, a duża 12? ____",
                "Zegar elektroniczny: 14:00 to godzina ____",
                "Która godzina za godzinę po 9:00? ____",
                "Ile godzin od 8:00 do 12:00? ____",
            ),
        },
        2: {
            "instruction": (
                "Odczytywanie godzin i połowy/kwadransa na zegarze. Proste obliczenia "
                "czasu w godzinach i minutach."
            ),
            "examples": _ex(
                "Która godzina: pół do 5? Zapisz cyframi: ____",
                "Ile minut od 8:15 do 8:45? ____",
                "Zegar: 13:30 to ____ po południu",
                "Lekcja trwa 45 minut. Zaczęła się o 9:00 – kiedy się skończy? ____",
            ),
        },
        3: {
            "instruction": (
                "Obliczenia czasu w godzinach, minutach i sekundach. Doba = 24 godziny. "
                "Liczby rzymskie do XII (zegar)."
            ),
            "examples": _ex(
                "Ile sekund w 2 minutach? ____",
                "Ile minut w 3 godzinach? ____",
                "Zapisz cyfrą rzymską godzinę 7: ____",
                "Pociąg jechał od 10:25 do 11:50. Ile czasu jechał? ____",
            ),
        },
    },

    # ----- Długości / obwody -----
    "pomiary długości": {
        1: {
            "instruction": (
                "Mierzenie i porównywanie długości w centymetrach (cm). "
                "Proste zdaniowe."
            ),
            "examples": _ex(
                "Ołówek ma 12 cm, kredka 8 cm. O ile cm ołówek jest dłuższy? ____",
                "Ile cm mają razem dwa odcinki po 5 cm? ____",
                "Odcinek 20 cm podzielono na 2 równe części. Każda ma ____ cm",
                "Co jest dłuższe: 30 cm czy 1 m? ____",
            ),
        },
        2: {
            "instruction": (
                "Pomiary długości w cm, mm, m. Zamiana jednostek: 1 m = 100 cm, "
                "1 cm = 10 mm."
            ),
            "examples": _ex(
                "Zamień: 2 m = ____ cm",
                "Zamień: 1 cm = ____ mm",
                "Ile cm to 5 m? ____",
                "Wstążka ma 80 cm. Odcięto 30 cm. Ile zostało? ____ cm",
            ),
        },
        3: {
            "instruction": (
                "Długości: cm, mm, m, km. Zamiana jednostek i obliczenia, "
                "także dla wyrażeń dwumianowanych (np. 3 m 20 cm)."
            ),
            "examples": _ex(
                "Zamień: 3 m 20 cm = ____ cm",
                "Zamień: 1000 m = ____ km",
                "Ile mm to 5 cm? ____",
                "Trasa ma 2 km 500 m. Ile to metrów? ____",
            ),
        },
    },

    "obwody": {
        2: {
            "instruction": (
                "Obwód prostokąta i kwadratu o podanych bokach (w cm). "
                "Format zdaniowy. Wynik w cm."
            ),
            "examples": _ex(
                "Oblicz obwód kwadratu o boku 4 cm. Obwód = ____ cm",
                "Oblicz obwód prostokąta o bokach 3 cm i 5 cm. Obwód = ____ cm",
                "Oblicz obwód kwadratu o boku 10 cm. Obwód = ____ cm",
                "Oblicz obwód prostokąta o bokach 6 cm i 4 cm. Obwód = ____ cm",
            ),
        },
        3: {
            "instruction": (
                "Obwody prostokąta, kwadratu i trójkąta o podanych bokach (cm lub m)."
            ),
            "examples": _ex(
                "Oblicz obwód trójkąta o bokach 4 cm, 5 cm i 7 cm. Obwód = ____ cm",
                "Oblicz obwód prostokąta o bokach 12 cm i 8 cm. Obwód = ____ cm",
                "Oblicz obwód kwadratu o boku 15 cm. Obwód = ____ cm",
                "Oblicz obwód trójkąta równobocznego o boku 6 cm. Obwód = ____ cm",
            ),
        },
    },

    # ----- Zadania tekstowe -----
    "zadania tekstowe": {
        1: {
            "instruction": (
                "Proste zadania tekstowe (1 działanie) w zakresie 0–20. "
                "Życiowy kontekst (jabłka, klocki, kolega). Format: krótkie pytanie "
                "+ „Wynik: ____” w nowej linii nie jest wymagany – wystarczy "
                "„Odpowiedź: ____ szt.” na końcu.”"
            ),
            "examples": _ex(
                "Ania miała 5 jabłek. Kupiła 4 jabłka. Ile ma jabłek? Odpowiedź: ____",
                "W koszyku było 10 kasztanów. Dziecko zabrało 3. Ile zostało? Odpowiedź: ____",
                "Tomek ma 7 klocków, Kasia ma 6. Ile mają razem? Odpowiedź: ____",
                "Na drzewie siedziało 12 ptaków. 5 odleciało. Ile zostało? Odpowiedź: ____",
            ),
            "max_result": 20,
        },
        2: {
            "instruction": (
                "Proste zadania tekstowe (1–2 działania) w zakresie 0–100. "
                "Kontekst codzienny."
            ),
            "examples": _ex(
                "W pudełku jest 24 ołówków, w drugim 18. Ile razem? Odpowiedź: ____",
                "Ola miała 50 zł. Wydała 23 zł. Ile zostało? Odpowiedź: ____ zł",
                "W klasie jest 4 rzędy po 6 ławek. Ile ławek razem? Odpowiedź: ____",
                "Z 60 cukierków rozdano po równo 5 dzieciom. Po ile dostały? Odpowiedź: ____",
            ),
            "max_result": 100,
        },
        3: {
            "instruction": (
                "Zadania tekstowe proste i wybrane złożone (1–3 działania) "
                "w zakresie 0–1000. Mogą zawierać pieniądze, długości, czas."
            ),
            "examples": _ex(
                "Książka kosztuje 24 zł, zeszyt 8 zł. Ile zapłacisz za 2 książki i 3 zeszyty? Odpowiedź: ____ zł",
                "Pociąg wyjechał o 9:15 i jechał 2 godziny 30 minut. O której dojechał? Odpowiedź: ____",
                "W sadzie jest 8 rzędów po 12 jabłoni. Ile drzew razem? Odpowiedź: ____",
                "Z deski długości 3 m odcięto 80 cm. Ile zostało? Odpowiedź: ____ cm",
            ),
            "max_result": 1000,
        },
    },

    # ----- Stare tematy (zachowane dla klas 4+) -----
    "dodawanie": {
        # Fallback dla starych klas (4-8) – tu zachowujemy stary behavior.
        4: {
            "instruction": "Dodawanie liczb wielocyfrowych odpowiednio do klasy.",
            "examples": _ex(
                "Policz: 234 + 156 = ____",
                "Policz: 1245 + 678 = ____",
            ),
        },
    },
    "odejmowanie": {
        4: {
            "instruction": "Odejmowanie liczb wielocyfrowych odpowiednio do klasy.",
            "examples": _ex(
                "Policz: 456 − 178 = ____",
                "Policz: 1000 − 345 = ____",
            ),
        },
    },
    "mnożenie": {
        4: {
            "instruction": "Mnożenie liczb dwucyfrowych przez jednocyfrowe (zapis pamięciowy).",
            "examples": _ex(
                "Policz: 24 × 3 = ____",
                "Policz: 56 × 4 = ____",
            ),
        },
    },
    "równania": {
        # Klasy 4+: jednokrokowe równania z okienkiem ☐ (zgodne z kluczem odpowiedzi)
        4: {
            "instruction": (
                f"Proste równania jednokrokowe z niewiadomą w okienku {_BOX}. "
                "Format: „Rozwiąż: … = …” — bez litery x. "
                "Dozwolone działania: +, −, ×, : (dzielenie bez reszty)."
            ),
            "examples": _ex(
                f"Rozwiąż: {_BOX} + 8 = 15",
                f"Rozwiąż: 4 × {_BOX} = 24",
                f"Rozwiąż: {_BOX} − 12 = 7",
                f"Rozwiąż: 72 : {_BOX} = 8",
            ),
            "max_result": 100,
        },
    },
}


# --------------------------------------------------------------------
# Lookup z downgrade'em (jeśli brak wpisu dla danej klasy, schodzimy w dół)
# --------------------------------------------------------------------


def get_blueprint(topic: str, grade: int) -> Optional[Blueprint]:
    """
    Zwraca blueprint dla danego tematu i klasy.

    Strategia:
    1. Jeśli temat ma wpis dla `grade` – zwróć go.
    2. W przeciwnym razie – zwróć blueprint dla najbliższej NIŻSZEJ klasy w tym temacie.
    3. Jeśli nic nie pasuje (np. klasa 1 a temat ma wpisy od klasy 4+) – zwróć None.
    """
    topic_norm = (topic or "").strip().lower()
    grades = TOPIC_BLUEPRINTS.get(topic_norm)
    if not grades:
        return None
    if grade in grades:
        return grades[grade]
    # Najbliższa niższa klasa, dla której mamy wpis.
    lower = [g for g in grades if g <= grade]
    if lower:
        return grades[max(lower)]
    return None


def available_topics(grade: int) -> list[str]:
    """Zwraca listę tematów dostępnych dla danej klasy (przydatne do UI)."""
    out = []
    for topic, grades in TOPIC_BLUEPRINTS.items():
        # Dostępny jeśli istnieje jakikolwiek wpis dla tej lub niższej klasy
        if any(g <= grade for g in grades):
            out.append(topic)
    return out
