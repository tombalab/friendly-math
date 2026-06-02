# Recenzja karty przez nauczyciela (Phase 3)

## Cel

Porównać wygenerowaną kartę z **kartą wzorcową** (jeśli istnieje w `data/reference_worksheets/`)
i zapisać krótką ocenę lokalnie — bez kont i bez danych osobowych uczniów.

## W Streamlit

1. Wygeneruj kartę (zakładka **Generuj**).
2. Przejdź do **Recenzja** — aplikacja dopasuje wzorzec po klasie, temacie i profilu.
3. Oceń 1–5 i dodaj notatki (np. „grupa A”, „za trudne” — **nie** imiona uczniów).
4. Recenzja zapisuje się w `data/history/<request_id>/review.json`.

## Checklista (gdy brak wzorca)

- Temat i klasa zgodne z planem lekcji?
- Polecenia krótkie, jeden krok (profil PPP)?
- Liczby w sensownym zakresie?
- PDF: polskie znaki, czytelny układ, miejsce na obliczenia?
- Klucz odpowiedzi (jeśli włączony) — czy pomaga, czy wymaga ręcznej korekty?
- Ilustracje — czy pomagają, czy rozpraszają?

## Karty wzorcowe w repo

| Plik | Klasa | Temat | Profil |
|------|-------|-------|--------|
| `1_dodawanie_adhd.json` | 1 | dodawanie | ADHD |
| `1_liczenie_po_standardowy.json` | 1 | liczenie po | standardowy |
| `1_odejmowanie_do_20_dyskalkulia.json` | 1 | odejmowanie do 20 | dyskalkulia |
| `2_dodawanie_dyskalkulia.json` | 2 | dodawanie | dyskalkulia |
| `2_liczenie_po_trudnosci_w_nauce.json` | 2 | liczenie po | trudności w nauce |
| `2_porownywanie_liczb_standardowy.json` | 2 | porównywanie liczb | standardowy |
| `2_rowania_okienkiem_dyskalkulia.json` | 2 | równania z okienkiem | dyskalkulia |
| `3_dodawanie_do_1000_standardowy.json` | 3 | dodawanie do 1000 | standardowy |
| `3_odejmowanie_do_1000_dyskalkulia.json` | 3 | odejmowanie do 1000 | dyskalkulia |
| `4_dzielenie_dyskalkulia.json` | 4 | dzielenie | dyskalkulia |
| `4_tabliczka_mnozenia_adhd.json` | 4 | tabliczka mnożenia | ADHD |
| `4_ulamki_standardowy.json` | 4 | ułamki | standardowy |
| `5_dzielenie_standardowy.json` | 5 | dzielenie | standardowy |
| `5_mnozenie_standardowy.json` | 5 | mnożenie | standardowy |
| `5_rownania_standardowy.json` | 5 | równania | standardowy |
| `6_dzielenie_dyskalkulia.json` | 6 | dzielenie | dyskalkulia |
| `6_mnozenie_standardowy.json` | 6 | mnożenie | standardowy |
| `6_ulamki_dysleksja.json` | 6 | ułamki | dysleksja |
| `7_rownania_dyskalkulia.json` | 7 | równania | dyskalkulia |
| `7_ulamki_standardowy.json` | 7 | ułamki | standardowy |
| `8_dzielenie_dyskalkulia.json` | 8 | dzielenie | dyskalkulia |
| `8_rownania_standardowy.json` | 8 | równania | standardowy |

Nowe wzorce: skopiuj JSON, uzupełnij `quality_criteria` i `structured_criteria`.

## Prywatność

- Nie wpisuj imion, nazwisk ani opisów diagnoz klinicznych.
- Etykieta karty = pseudonim grupy lub data lekcji.
