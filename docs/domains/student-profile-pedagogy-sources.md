# Źródła pedagogiczne profili ucznia

## Dokument bazowy

- **Tytuł:** *Mój uczeń i matematyka* — Renata Karsznia (ORE, Warszawa 2018)
- **Plik w repo:** [`.cursor/moj_uczen_i_matematyka.pdf`](../../.cursor/moj_uczen_i_matematyka.pdf)
- **Zakres:** nauczanie matematyki w SP (szczególnie klasy IV–VIII) ze uwzględnieniem uczniów ze SPE

## Zasady ogólne (dla wszystkich profili)

1. Materiały mają być **przejrzyste**: czytelna czcionka, rozmieszczenie treści, stonowane kolory, zrozumiały język.
2. Zadania na poziomie, z którym uczeń **poradzi sobie samodzielnie** (bez stałej pomocy dorosłego).
3. Nauczyciel powinien móc **dostosować** kartę do indywidualnych potrzeb — profile w Friendly Math to presety PPP, nie diagnoza.
4. Wizualizacja i modele konkretne (jabłka, pizza, monety, zegar, bryły) wspierają zrozumienie, gdy nie zastępują treści zadania.
5. Zadania tekstowe: analiza krok po kroku (dane → szukane → wzór → obliczenia → odpowiedź), ale **dawkowane**.

## Mapowanie profil → zasady z poradnika

| Profil Friendly Math | Odniesienie w poradniku | Implikacja w generatorze |
|----------------------|-------------------------|---------------------------|
| **ADHD** | Rozdz. 3.2 | Jedno zadanie naraz, krótkie polecenia, dynamiczny układ, wsparcie wizualne, unikanie rozpraszaczy |
| **dyskalkulia** | Julka / trudności z liczbami, wizualizacja | Małe liczby, jeden krok, konkretna reprezentacja, więcej miejsca na obliczenia |
| **dysleksja** | Trudności z dekodowaniem tekstu | Krótki tekst, powtarzalny format; **nie** obniżać poziomu matematyki |
| **trudności w nauce** | SPE ogólnie, wolniejsze tempo | Progresja mikrokrokami, powtórzenia, prostsze liczby |
| **zdolny** | Uczniowie uzdolnieni | Większe wyzwanie, czasem drugi krok lub uzasadnienie |
| **standardowy** | Typowa klasa | Blueprint tematu bez dodatkowego uproszczenia |

## ADHD (skrót z rozdz. 3.2)

- Jedno zadanie na raz, precyzyjne oczekiwania.
- Krótkie przerwy i kontrola postępu zapisu.
- Metody wizualne skuteczniejsze niż długi tekst.
- Unikać zbędnych szczegółów; można nawiązać do zainteresowań (np. sport).

## Dyskalkulia / trudności z liczbami

- Wizualizacja krok po kroku (np. grupy obiektów, siatka mnożenia).
- Powrót do wcześniejszych umiejętności, gdy brakuje podstaw (np. tabliczka → mnożenie pisemne).
- Konkretne modele: czekolada/ułamki, monety, zegar, bryły z patyczków.

## Zadania tekstowe (klasa IV+)

Poradnik zaleca m.in.:

- Wypisanie danych, szukanych, wzorów.
- Rozbicie na etapy zamiast jednego długiego polecenia.
- Praktyczne konteksty (zakupy, czas, prędkość) po sprawdzeniu, czy uczeń rozumie słownictwo.

## Uczeń zdolny

- Dodatkowe zadania i wyzwania w ramach tematu klasy.
- Zachęta do uzasadnienia / zapisania sposobu rozwiązania (egzamin wymaga ścieżki, nie tylko wyniku).

## Użycie w kodzie

Maszynowa polityka: [`app/domain/profile_pedagogy.py`](../../app/domain/profile_pedagogy.py).

Powiązane domeny: [student-profiles-ppp.md](student-profiles-ppp.md), [visual-assets.md](visual-assets.md).
