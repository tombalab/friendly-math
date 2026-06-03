# Instalacja i powtarzalność (P2.3)

## Wymagania

- **Python 3.11+** (zalecane 3.11.x — zgodne ze Streamlit Cloud)
- Git
- Klucz **OPENAI_API_KEY** (tylko do generowania zadań w UI; smoke test działa offline)

## Szybki start

```bash
git clone https://github.com/tombalab/friendly-math.git
cd friendly-math

python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

Opcjonalnie — **dokładnie te same wersje** co w ostatnim zweryfikowanym środowisku:

```bash
pip install -r requirements-lock.txt
```

## Zmienne środowiskowe

```bash
cp .env.example .env
# Uzupełnij OPENAI_API_KEY=sk-...
```

## Czcionka PDF (polskie znaki)

Plik `assets/fonts/DejaVuSans.ttf` jest w repozytorium. Nie trzeba nic pobierać ręcznie po `git clone`.

Szczegóły: [assets/fonts/README.md](../assets/fonts/README.md).

## Zależności opcjonalne

| Pakiet | Rola |
|--------|------|
| **PyMuPDF** (`PyMuPDF` w requirements) | Podgląd PDF jako obrazy w Streamlit; bez niego działa tylko pobieranie pliku |
| **OpenAI** | Generowanie zadań i layoutu (poza profilami low-stimuli bez AI layout) |

## Observability (P2.4)

Domyślnie włączone logowanie zdarzeń generacji (jedna linia JSON na zdarzenie w terminalu):

```bash
# wyłączenie
set FRIENDLY_MATH_OBSERVABILITY=0   # Windows
export FRIENDLY_MATH_OBSERVABILITY=0  # Linux/macOS
```

W Streamlit: expander **„Zdarzenia generacji”** po wygenerowaniu karty. Nie loguje treści zadań ani `optional_context`.

## Smoke test (offline)

Z katalogu głównego repo:

```bash
python scripts/smoke_check.py
python scripts/curriculum_fallback_audit.py   # 72 tematy × 6 profili, bank fallbacków
```

Sprawdza: importy, font DejaVu, minimalny PDF z polskimi znakami, wybrane testy referencyjne (bez API).
Macierz produktu: [curriculum-matrix.md](curriculum-matrix.md).

## Uruchomienie aplikacji

```bash
streamlit run app/ui/app.py
```

http://localhost:8501

## Skrypty pomocnicze (offline)

```bash
python scripts/preview_pdfs.py      # przykładowe PDF do data/preview/pdfs/
python scripts/preview_icons.py     # ikony podglądu
```

## Polityka zależności

- **`requirements.txt`** — bezpośrednie zależności z sensownymi pinami (minor updates dozwolone tam, gdzie bezpieczne).
- **`requirements-lock.txt`** — pełny pin do odtworzenia środowiska (`pip freeze` po weryfikacji).
- Po zmianie `requirements.txt` uruchom `smoke_check` i zaktualizuj lock, jeśli instalujesz w nowym venv.

## Historia kart (P2.5)

Udane generacje trafiają do `data/history/<request_id>/` (`worksheet.pdf` + `meta.json`).
Katalog `data/out/worksheet.pdf` to nadal **ostatnia** karta (szybki podgląd).

Historia jest lokalna na tym komputerze — bez kont użytkowników. Opcjonalna **etykieta karty**
(np. „grupa A”) służy organizacji; nie wpisuj imion i nazwisk uczniów.

## Artefakty generowane (nie commituj)

- `data/out/` — ostatni PDF z UI
- `data/history/` — archiwum wygenerowanych kart
- `data/preview/` — podglądy z skryptów

Są w `.gitignore`.
