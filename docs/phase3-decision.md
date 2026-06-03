# Phase 3 — checkpoint decyzyjny (P3.1)

Data przeglądu: _______________  
Uczestnik: _______________

## Co już działa w Streamlit v1.2

- Generowanie z `WorksheetService` + panel jakości
- Historia lokalna (`data/history/`)
- Recenzja z dopasowaniem do kart wzorcowych
- Smoke test offline + CI

## Pytania (wypełnij po 2–4 tygodniach użytkowania)

1. Czy karty są **wystarczająco dobre do druku** bez ręcznej poprawki większości zadań?
2. Czy nauczyciele **wracają** do historii i recenzji?
3. Czy brakuje: kont, udostępniania, wielu użytkowników, szkoły jako tenant?
4. Czy Streamlit Cloud wystarcza do deploy, czy potrzebny własny hosting?

## Opcje

| Opcja | Kiedy sensowna |
|--------|----------------|
| **Zostać przy Streamlit** | Jakość OK, mało użytkowników, szybkie iteracje |
| **Streamlit + lepszy deploy** | Potrzeba stabilnego URL, secrets, backup historii |
| **Platforma (FastAPI/Next)** | Wiele szkół, konta, współdzielenie, RLS |
| **Odłożyć chat/głos/AI obrazy** | Dopóki worksheet nie jest powtarzalnie dobry |

## Decyzja

- [ ] Kontynuujemy Streamlit jako główny produkt (min. 3 miesiące)
- [ ] Planujemy migrację platformy — wymagania: _______________
- [ ] Zatrzymujemy rozwój — powód: _______________

## Zasada techniczna

Każda przyszła platforma opakowuje **`WorksheetService`** i testy z `tests/`, nie kopiuje logiki z `app/ui/app.py`.
