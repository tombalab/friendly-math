# Macierz zgodności z podstawą programową (kontrakt produktu)

Źródło decyzji UI, generatora i recenzji. Wizualizacja i wnioski strategiczne: [`curriculum-matrix-plan.canvas.tsx`](curriculum-matrix-plan.canvas.tsx).

**Dokumenty PP:** [`podstawa-programowa-edukacja-wczesnoszkolna-matematyka-2025-2026.md`](podstawa-programowa-edukacja-wczesnoszkolna-matematyka-2025-2026.md), [`podstawa-programowa-matematyka-sp-iv-viii-2025-2026.md`](podstawa-programowa-matematyka-sp-iv-viii-2025-2026.md).

**Kod:** `app/domain/topic_catalog.py`, `app/ai/topic_blueprints.py`, `app/ai/fallback_tasks.py`, `data/reference_worksheets/`.

---

## Legenda

| Kolumna | Znaczenie |
|---------|-----------|
| **Blueprint** | `exact` — szablon dla tej klasy; `downgraded` — używana wersja z niższej klasy; `missing` — brak szablonu (temat niewidoczny w UI) |
| **Klucz** | `full` / `partial` / `none` — automatyczny klucz odpowiedzi (`TopicCapabilities.answer_support`) |
| **Fallback** | Bank deterministyczny przy degradacji AI (`fallback_tasks.py`) |
| **Wzorzec** | Co najmniej jedna karta w `data/reference_worksheets/` dla pary klasa+temat |
| **Status PP** | Ocena względem wymagań PP (nie tylko techniczna dostępność w UI) |

**MVP kl. 4–8:** w UI widocznych jest 6 tematów rachunkowych. Klasy 4–6 mają teraz blueprinty `exact`; klasy 7–8 nadal korzystają z `downgraded` i wymagają decyzji produktowej. Komunikat w sidebarze: `upper_grades_mvp_caption_pl()`.

---

## Macierz: opcje UI × klasa (72 kombinacje)

Ostatnia weryfikacja: audyt fallbacków × 6 profili — **0 ostrzeżeń walidatora** (`python scripts/curriculum_fallback_audit.py`).

| Klasa | topic_id | Temat UI | Blueprint | Klucz | Fallback | Wzorzec | Status PP |
|------:|----------|----------|-----------|-------|:--------:|:-------:|-------------|
| 1 | `liczenie_po` | liczenie po | exact | full | tak | tak | Dobre |
| 1 | `porownywanie_liczb` | porównywanie liczb | exact | full | tak | — | Dobre; brak wzorca |
| 1 | `dodawanie_do_20` | dodawanie do 20 | exact | full | tak | tak | Dobre |
| 1 | `odejmowanie_do_20` | odejmowanie do 20 | exact | full | tak | tak | Dobre |
| 1 | `rownania_z_okienkiem` | równania z okienkiem | exact | full | tak | — | Dobre; brak wzorca |
| 1 | `czas` | czas | exact | partial | tak | tak | Częściowe |
| 1 | `pomiary_dlugosci` | pomiary długości | exact | partial | tak | — | Częściowe |
| 1 | `zadania_tekstowe` | zadania tekstowe | exact | partial | tak | tak | Częściowe |
| 2 | `liczenie_po` | liczenie po | exact | full | tak | tak | Dobre |
| 2 | `porownywanie_liczb` | porównywanie liczb | exact | full | tak | tak | Dobre |
| 2 | `dodawanie_do_20` | dodawanie do 20 | exact | full | tak | tak | Dobre |
| 2 | `dodawanie_do_100` | dodawanie do 100 | exact | full | tak | tak | Dobre |
| 2 | `odejmowanie_do_20` | odejmowanie do 20 | exact | full | tak | — | Dobre |
| 2 | `odejmowanie_do_100` | odejmowanie do 100 | exact | full | tak | — | Dobre |
| 2 | `tabliczka_mnozenia` | tabliczka mnożenia | exact | full | tak | — | Dobre |
| 2 | `mnozenie_przez_10` | mnożenie przez 10 | exact | full | tak | — | Dobre |
| 2 | `dzielenie` | dzielenie | exact | full | tak | — | Dobre |
| 2 | `rownania_z_okienkiem` | równania z okienkiem | exact | full | tak | tak | Dobre |
| 2 | `ulamki` | ułamki | exact | partial | tak | — | Częściowe |
| 2 | `pieniadze` | pieniądze | exact | partial | tak | tak | Częściowe |
| 2 | `czas` | czas | exact | partial | tak | — | Częściowe |
| 2 | `pomiary_dlugosci` | pomiary długości | exact | partial | tak | tak | Częściowe |
| 2 | `obwody` | obwody | exact | partial | tak | tak | Częściowe |
| 2 | `zadania_tekstowe` | zadania tekstowe | exact | partial | tak | tak | Częściowe |
| 3 | `liczenie_po` | liczenie po | exact | full | tak | — | Dobre |
| 3 | `porownywanie_liczb` | porównywanie liczb | exact | full | tak | — | Dobre |
| 3 | `dodawanie_do_20` | dodawanie do 20 | exact | full | tak | tak | Powtórka kl. 1–2 |
| 3 | `dodawanie_do_100` | dodawanie do 100 | exact | full | tak | tak | Dobre |
| 3 | `dodawanie_do_1000` | dodawanie do 1000 | exact | full | tak | tak | Dobre |
| 3 | `odejmowanie_do_20` | odejmowanie do 20 | exact | full | tak | tak | Powtórka |
| 3 | `odejmowanie_do_100` | odejmowanie do 100 | exact | full | tak | tak | Dobre |
| 3 | `odejmowanie_do_1000` | odejmowanie do 1000 | exact | full | tak | tak | Dobre |
| 3 | `tabliczka_mnozenia` | tabliczka mnożenia | exact | full | tak | — | Dobre |
| 3 | `mnozenie_przez_10` | mnożenie przez 10 | exact | full | tak | — | Dobre |
| 3 | `dzielenie` | dzielenie | exact | full | tak | — | Dobre |
| 3 | `rownania_z_okienkiem` | równania z okienkiem | exact | full | tak | — | Dobre |
| 3 | `ulamki` | ułamki | exact | partial | tak | — | Częściowe |
| 3 | `pieniadze` | pieniądze | exact | partial | tak | tak | Częściowe |
| 3 | `czas` | czas | exact | partial | tak | — | Częściowe |
| 3 | `pomiary_dlugosci` | pomiary długości | exact | partial | tak | — | Częściowe |
| 3 | `obwody` | obwody | exact | partial | tak | — | Częściowe |
| 3 | `zadania_tekstowe` | zadania tekstowe | exact | partial | tak | tak | Częściowe |
| 4 | `dzielenie` | dzielenie | exact | full | tak | tak | MVP rachunek |
| 4 | `ulamki` | ułamki | exact | partial | tak | tak | MVP |
| 4 | `dodawanie` | dodawanie | exact | full | tak | — | MVP |
| 4 | `odejmowanie` | odejmowanie | exact | full | tak | — | MVP |
| 4 | `mnozenie` | mnożenie | exact | full | tak | tak | MVP |
| 4 | `rownania` | równania | exact | full | tak | — | MVP (☐) |
| 5–6 | `dzielenie` … `rownania` | 6 tematów | exact | full/partial | tak | częściowo | MVP rachunkowe — lepsze dopasowanie per klasa |
| 7–8 | `dzielenie` … `rownania` | 6 tematów | downgraded* | full/partial | tak | częściowo | MVP — nie pełne PP |

\* Dla klas 7–8 tematy ogólne korzystają z blueprintów klasy 6 do czasu decyzji produktowej.

Szczegóły wierszy 5–8: `python scripts/curriculum_matrix_report.py --markdown`.

---

## Luki PP poza katalogiem tematów

| Obszar PP | Klasy | W produkcie |
|-----------|-------|-------------|
| Geometria (figury, symetria, kąty) | 1–3 | Brak osobnych tematów (tylko `obwody`) |
| Masa, temperatura, pojemność | 1–3 | Brak |
| Liczby całkowite, oś liczbowa | 4–8 | Brak |
| Procenty, statystyka, potęgi, pierwiastki | 4–8 | Brak |
| Geometria płaska/przestrzenna, Pitagoras | 4–8 | Brak |

---

## Plan fazowy (skrót)

| Faza | Stan | Następny krok |
|------|------|----------------|
| **0. Uczciwość MVP** | Zrobione | Równania ☐, baner 4–8, ostrzeżenia klucza; walidatory profil×temat |
| **1. Macierz PP** | Ten dokument | Utrzymywać przy zmianach katalogu; raport: `curriculum_matrix_report.py` |
| **2. Domknięcie 1–3** | Zrobione (rdzeń) | 35 wzorców; dalsze luki: geometria, masa, kl. 1 czas/pomiary |
| **3. Stabilizacja 4–6** | Zrobione (blueprinty) | Ewentualnie rozszerzyć fallbacki i wzorce 4–6 |
| **4. Decyzja 7–8** | Plan | Zawęzić UI lub dodać zakres egzaminacyjny |
| **5. Curriculum smoke** | Częściowo | `curriculum_fallback_audit.py` (CI — do podpięcia) |

---

## Priorytet Fazy 2 (wzorce referencyjne)

Brak kart JSON (klasa × temat) — najpierw:

1. **Praktyczne:** `pieniadze`, `czas`, `pomiary_dlugosci`, `obwody` (kl. 2–3)
2. **Tekstowe:** `zadania_tekstowe` (kl. 1–3)
3. **Ułamki intuicyjne:** `ulamki` (kl. 2–3, partial key)
4. **Uzupełnienie rachunku:** porównywanie kl. 1/3, tabliczka, dzielenie kl. 3, równania z okienkiem kl. 1/3

Aktualnie **35** wzorców dla rdzenia I–III (Faza 2 — minimum osiągnięte).

---

## Odświeżanie tabeli

```bash
python scripts/curriculum_matrix_report.py --markdown
python scripts/curriculum_fallback_audit.py
```

Przy zmianie `topic_catalog` lub blueprintów zaktualizuj sekcję macierzy i uruchom audyt.
