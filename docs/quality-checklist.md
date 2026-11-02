# Checklista jakości karty pracy (Q6)

Miara jakości ma dwie części: automatyczną (test złotych kart) i ręczną (wydruk).
Karta jest „dobra”, gdy przechodzi obie.

## Złote karty

Sześć wzorców docelowych z polem `golden` w `data/reference_worksheets/`:

| Plik | Pasmo | Profil | Co pokazuje | Strony ucznia |
|------|-------|--------|-------------|---------------|
| `1_czas_adhd.json` | kl. 1–3 | ADHD | motyw kosmosu, zegar przy każdym zadaniu, zmiana aktywności | ≤ 2 |
| `2_dodawanie_dyskalkulia.json` | kl. 1–3 | dyskalkulia | spokojny szablon, ramka dziesiątkowa, oś liczbowa | ≤ 2 |
| `3_dzielenie_standardowy.json` | kl. 1–3 | standardowy | siatka zadań, jedna pomoc (talerze) | ≤ 2 |
| `4_tabliczka_mnozenia_adhd.json` | kl. 4–6 | ADHD | bez motywu przygody, pole „Wynik”, opcje wyboru | 1 |
| `6_ulamki_dysleksja.json` | kl. 4–6 | dysleksja | ułamki piętrowe, klucz z jawnymi lukami | ≤ 2 |
| `8_rownania_standardowy.json` | kl. 7–8 | standardowy | szablon „Szkolny”, „Część A/B/C” | 1 |

Pole `golden` zawiera: `max_student_pages`, `template`, `visual_kinds` (rodzaj pomocy
przy każdym zadaniu, `null` = bez pomocy) i `why` (co ta karta ma pokazać).

## Część automatyczna

`python -m pytest tests/test_golden_worksheets.py` generuje każdą złotą kartę offline
(pełny `WorksheetService`, zadania z wzorca zamiast OpenAI) i sprawdza
(`app/review/golden.py`):

- [ ] liczba stron ucznia ≤ `max_student_pages`;
- [ ] na karcie ucznia nie ma nazwy profilu ani słów „ADHD”, „dyskalkulia”, „dysleksja”, „grafomotoryka”, „PPP”, „orzeczenie”, „Profil”, „Strategia”, „Rola grafiki”;
- [ ] pierwsza strona ma pole „Imię i nazwisko”;
- [ ] każde zadanie ma numer na karcie ucznia i każda strona ucznia ma co najmniej jedno zadanie (np. nie ma strony z samą samooceną);
- [ ] zadania na karcie to zadania wzorca (fallback ani walidacja ich nie podmieniły);
- [ ] karta odpowiedzi istnieje i jest oznaczona „dla nauczyciela”;
- [ ] szablon i pomoce wizualne są takie jak we wzorcu.

Podgląd: `python scripts/render_golden.py` zapisuje PDF i PNG do `data/preview/golden/`.

## Część ręczna (wydruk A4, czarno-biały i kolorowy)

Uczeń:
- [ ] Polecenie pasuje do zadania (np. „Otocz kółkiem” tylko przy opcjach do otoczenia).
- [ ] Każde miejsce na odpowiedź jest jednoznaczne: luka, kratka albo opcje, nie dwa naraz.
- [ ] Dystraktory w opcjach są sensowne (np. godzina 1–12, nie 0).
- [ ] Pomoc wizualna używa liczb z zadania i nie zdradza wyniku.
- [ ] Czcionka czytelna z odległości ręki; ogonki polskich znaków na wydruku.
- [ ] Grafika czytelna w druku czarno-białym (kolory składników rozróżnialne odcieniem).
- [ ] Brak pustej strony i brak nagłówka sekcji samotnie na dole strony.
- [ ] Wygląd pasuje do wieku: kl. 1–3 z motywem, kl. 7–8 bez „Misji” i dekoracji.

Nauczyciel:
- [ ] Klucz odpowiedzi pokazuje treść zadania obok odpowiedzi.
- [ ] Brak odpowiedzi w kluczu jest wyjaśniony (nie samo „—”).
- [ ] Ostrzeżenia w panelu jakości mówią, co sprawdzić przed drukiem.

## Jak dodać złotą kartę

1. Wybierz wzorzec z `data/reference_worksheets/`, który pokazuje coś, czego zestaw jeszcze nie ma (pasmo klas, profil, rodzaj pomocy).
2. Dopisz pole `golden` i uruchom `python scripts/render_golden.py`.
3. Obejrzyj PNG według części ręcznej. Dopiero wtedy wpisz oczekiwania do `golden`.

Zestaw ma 5–6 kart; test pilnuje pokrycia trzech pasm klas oraz profili ADHD, dyskalkulia i standardowy.
