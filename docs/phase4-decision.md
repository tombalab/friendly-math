# Faza 4 — decyzja produktowa: klasy 7–8 (opcja B)

**Data:** 2026-06-02  
**Decyzja:** **B — rozbudowa** (nie ukrywamy klas 7–8 w UI)

## Cel

Rozszerzyć Friendly Math o zakres egzaminacyjny VII–VIII zamiast traktować te klasy wyłącznie jako powtórkę rachunku z klasy 6 (`downgraded` blueprint).

## Zakres tej iteracji (MVP opcji B)

### Wdrożone w kodzie

| Obszar | Zakres |
|--------|--------|
| Blueprinty `exact` | Klasy **7–8** dla: `dodawanie`, `odejmowanie`, `mnożenie`, `dzielenie`, `ułamki`, `równania` |
| Nowe tematy UI (tylko kl. 7–8) | `procenty`, `potęgi`, `pitagoras` |
| Fallbacki | Banki zadań dla nowych tematów; większe liczby dla dzielenia 7–8 |
| Klucz odpowiedzi | `partial` dla procentów, potęg, Pitagorasa (proste formaty) |
| UI | Zaktualizowany baner MVP dla kl. 7–8 |

### Świadomie poza tą iteracją (kolejne epiki)

- Liczby całkowite (oś, wartość bezwzględna) jako osobny temat
- Statystyka, geometria przestrzenna, funkcje
- Pełne pokrycie PP VII–VIII (potęgi ujemne, logarytmy, pełna algebra)
- Wzorce referencyjne dla wszystkich nowych par klasa×temat 7–8

## Zasady uczciwości (nadal obowiązują)

1. Baner w sidebarze dla kl. 7–8 informuje o **rozszerzonym MVP**, nie o „pełnej zgodności z PP”.
2. Tematy `partial` — podpowiedź przy „Dołącz odpowiedzi”.
3. Nowe tematy wymagają testów referencyjnych przed obietnicą „gotowe do druku bez recenzji”.

## Kryterium sukcesu Fazy 4 (techniczne)

- `resolve_topic(..., grade=7|8)` → `blueprint_status == "exact"` dla wszystkich tematów widocznych w UI dla tej klasy.
- `python scripts/curriculum_fallback_audit.py` → 0 failing.
- Test `test_grade_7_8_topics_have_exact_blueprints` przechodzi.

## Następny krok po tej iteracji

1. Karty wzorcowe: `7_procenty`, `8_potegi`, `7_pitagoras` (+ uzupełnienie rdzenia 4–6).
2. Fallbacki zależne od klasy (nie tylko 7–8) dla `dodawanie` / `mnożenie` itd.
3. Ewentualnie temat **liczby całkowite** (kl. 7).
