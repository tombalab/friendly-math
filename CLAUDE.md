# Friendly Math — kontekst dla Claude Code

Aplikacja Streamlit dla nauczyciela i terapeuty: generuje polskie karty pracy z matematyki (PDF A4) dla klas 1–8, z profilami PPP (ADHD, dyskalkulia, dysleksja i inne). Wersja bieżąca to MVP v1.5.0. Produkt zostaje na Streamlit, dopóki jakość kart nie jest wiarygodna.

Źródło prawdy to kod i testy. `docs/architecture-and-domain.md` i część `docs/domains/` opisują starszy stan (UI jako orkiestrator, brak historii). Przy sprzeczności trzymaj się kodu.

## Twarde ograniczenia

- Zostań przy Streamlit i Pythonie. Nie dodawaj FastAPI, Next.js, Supabase, czatu, głosu ani kont użytkowników.
- Nie przebudowuj architektury „dla porządku”. Jedna sesja = jeden punkt z `docs/prioritized-tasks.md`.
- Nie zapisuj danych osobowych uczniów. Etykieta karty to organizacja (np. „grupa A”), nie imię i nazwisko.
- Domyślne ilustracje są deterministyczne (`app/generators/images.py`, `icons.py`). Generowanie obrazów przez model zostaw eksperymentem, nie ścieżką produktową.
- Teksty dla nauczyciela i treść kart są po polsku, z polskimi znakami. Identyfikatory w kodzie (`topic_id`, `profile_id`) zostają stabilne i po angielsku lub w snake_case.
- Nie commituj `.env`, `data/out/`, `data/history/`, `data/preview/`.
- Gałąź robocza to `dev`. `main` jest pod deploy na Streamlit Cloud. Nie pushuj, dopóki użytkownik o to nie poprosi.
- Nie zmieniaj `git config`. Nie rób force push ani `--no-verify`.

## Jak uruchomić i sprawdzić

Python 3.11. Katalog roboczy: korzeń repozytorium. Windows (PowerShell):

```powershell
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python scripts\smoke_check.py
python -m pytest tests
streamlit run app/ui/app.py
```

Aplikacja: http://localhost:8501. Po zmianie kodu zrestartuj Streamlit.

- `OPENAI_API_KEY` w `.env` jest potrzebny tylko do generowania zadań w UI. Testy, smoke i audyt fallbacków mają działać offline, bez wywołań API.
- `python scripts/smoke_check.py` — importy, font DejaVu, minimalny PDF z polskimi znakami.
- `python scripts/curriculum_fallback_audit.py` — pokrycie banków fallbacków.
- `python -m pytest tests` — pełna suita. Przy małej zmianie odpal tylko dotknięte pliki, np. `python -m pytest tests/test_topic_catalog.py`.
- Font polskich znaków: `assets/fonts/DejaVuSans.ttf`. Brak fontu ma być jawnym ostrzeżeniem, nie cichym fallbackiem na font bez ogonków.
- Obserwowalność: `FRIENDLY_MATH_OBSERVABILITY=0` wyłącza log JSON. Logi nie mogą zawierać treści zadań ani `optional_context`.

Pełna instalacja: `docs/install.md`.

## Gdzie jest kod

Pipeline karty siedzi poza UI. Streamlit tylko zbiera formularz i pokazuje wynik.

1. UI: `app/ui/app.py` oraz panele w `app/ui/` (generacja, jakość, historia, recenzja, zdarzenia).
2. Orkiestracja: `app/worksheet/service.py` — `WorksheetService.generate(WorksheetRequest) -> WorksheetResult`.
3. Kontrakt wejścia i wyjścia: `app/domain/worksheet_contract.py`.
4. Tematy: `app/domain/topic_catalog.py` (stabilne `topic_id`) i `app/ai/topic_blueprints.py`.
5. Profile PPP: `app/domain/profile_catalog.py`, `app/domain/profile_pedagogy.py`, klasy w `app/generators/profiles/`.
6. Zadania: `app/ai/text_generator.py`, fallbacki w `app/ai/fallback_tasks.py` i `app/ai/profile_fallback_banks.py`. Prompty: `app/backend/prompts/`.
7. Walidacja profilu: `app/validators/`.
8. Odpowiedzi: `app/generators/answers.py`. Ilustracje: `app/generators/images.py`, `icons.py`. Layout: `app/domain/worksheet_layout.py`, `app/ai/layout_generator.py`.
9. PDF: `app/pdf/generator.py`, `app/pdf/fonts.py`.
10. Historia lokalna: `app/history/store.py` → `data/history/<request_id>/`. Ostatni PDF: `data/out/worksheet.pdf`.
11. Wzorce jakości: `data/reference_worksheets/*.json`.

Gdy temat, klasa albo profil nie da się uczciwie obsłużyć, zatrzymaj generację albo zwróć wyraźne ostrzeżenie w `WorksheetResult`. Nie podstawiaj cicho zadań z innego tematu i nie drukuj „—” w kluczu odpowiedzi bez wyjaśnienia.

## Jak pracować w sesji

- Najpierw przeczytaj zadanie w `docs/prioritized-tasks.md` i tylko te dokumenty domenowe, których dotyczy zmiana (`docs/domains/`).
- Zachowaj obecny flow nauczyciela: klasa, temat, liczba zadań, profil, ilustracje, miejsce na obliczenia, klucz odpowiedzi.
- Nowe reguły tematu i profilu dawaj do katalogów, nie do rozproszonych list stringów w UI.
- Testy nowych zachowań pisz offline. Wzorce z `data/reference_worksheets/` traktuj jako kontrakt jakości, nie jako dekorację.
- Po zmianie uruchom odpowiednie testy i streść, co się zmieniło oraz czego nie sprawdziłeś (szczególnie żywe wywołanie OpenAI i wygląd PDF w przeglądarce).
- Zależności: `requirements.txt` to piny bezpośrednie, `requirements-lock.txt` to pełny lock. Po zmianie zależności odpal smoke i zaktualizuj lock tylko wtedy, gdy środowisko zostało zweryfikowane.

## Wersjonowanie

- Semver: patch = poprawki, minor = nowe funkcje lub zmiany jakości PDF, major = zmiana platformy albo flow nauczyciela.
- Każda zmiana na `dev` dopisuje linijkę do `[Unreleased]` w `CHANGELOG.md` w tym samym commicie.
- Wydanie (tylko na prośbę użytkownika): `[Unreleased]` → `[X.Y.Z] – data`, `APP_VERSION` w `app/ui/app.py`, status w `README.md`; merge `dev` → `main` (`--no-ff`), tag `vX.Y.Z` na commicie scalającym, push tagu, GitHub Release z notkami z CHANGELOG.

## Czego jeszcze nie robić

Lista w `docs/prioritized-tasks.md`, sekcja „What Not To Do Yet”. Skrót: brak nowej platformy, brak czatu i głosu, brak obrazów AI jako domyślnych, brak danych osobowych, brak refaktoru bez efektu widocznego dla nauczyciela.
