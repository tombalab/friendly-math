> 📌 **Notatka (czerwiec 2026):** Friendly Math pozostaje aplikacją Streamlit,
> a obecny cel to dopracowanie jakości kart pracy PDF przed większą zmianą platformy.
> Plan rozwoju: zobacz sekcję [Roadmap](#roadmap-high-level) oraz dokumenty w `docs/`.

---

⚠️ **Status projektu: MVP v1.3.0**  
  
Aktualna wersja aplikacji to **funkcjonalne MVP v1.3.0**:
 - działający interfejs Streamlit z zakładkami **Generuj / Historia / Recenzja**,
 - pełny flow: parametry → generacja zadań → walidacja profilu → ilustracje → layout → PDF,
 - profile PPP wpływające na treść zadań, walidację, ilustracje i układ PDF,
 - **opcja „Dołącz odpowiedzi”** — strukturalny klucz odpowiedzi, gdy temat jest wspierany,
 - **panel jakości**: źródło zadań, walidacja, spełnienie profilu, ilustracje, PDF i zdarzenia,
 - **historia lokalna** kart w `data/history/` z metadanymi i diagnostyką ilustracji,
 - eksport do PDF A4 z polskimi znakami, poprawionym łamaniem stron i czytelniejszymi ilustracjami.
  
Karty referencyjne i przykłady jakości: `data/reference_worksheets/`.


---

# Friendly Math 🧮

**Friendly Math** to inteligentna aplikacja wspierająca naukę matematyki
uczniów szkoły podstawowej, ze szczególnym uwzględnieniem uczniów
z opiniami i orzeczeniami PPP (np. dyskalkulia, ADHD, trudności w koncentracji).

Aplikacja umożliwia szybkie generowanie **czytelnych, niskobodziecowych kart pracy (PDF)**,
dostosowanych do indywidualnych potrzeb ucznia.

## ✅ Co działa w wersji v1.3.0 (MVP)

- **Panel generowania**: klasa 1–8, temat, liczba zadań, profil ucznia, ilustracje, miejsce na obliczenia i odpowiedzi.
- **Zakres tematów**: działania arytmetyczne, ułamki, równania, zadania tekstowe, pieniądze, czas, obwody, pomiary długości, procenty, potęgi i Pitagoras.
- **Profile PPP**: standardowy, ADHD, dyskalkulia, dysleksja, trudności w nauce, zdolny.
- **Jakość profilu**: walidatory i fallbacki pilnują m.in. długości treści, zakresu liczb, liczby kroków i wzbogacenia zadań.
- **Ilustracje**: deterministyczne ikony i sceny per zadanie lub w nagłówku, z raportem pokrycia i `skip_reason`.
- **PDF quality v1.3**: zawijanie tekstu po realnej szerokości fontu, łamanie strony przed całym blokiem zadania, ostrzejsze PNG, mały header przy niskim pokryciu ilustracji.
- **Historia i recenzja**: zapis lokalny wygenerowanych kart, filtrowanie historii, status jakości i pliki recenzji.
- **Testy i audyty**: testy referencyjne, walidatory, smoke check oraz audyt fallbacków curriculum.

Karty referencyjne: `data/reference_worksheets/`.  
Po zmianie kodu **zrestartuj Streamlit**.

---

## 🎯 Cel projektu (v1.3)

- wspieranie uczniów z trudnościami w nauce matematyki,
- ułatwienie pracy nauczycielom i terapeutom,
- generowanie kart pracy dopasowanych do profilu ucznia,
- tworzenie materiałów edukacyjnych gotowych do druku (PDF A4).

---

## 👤 Co może zrobić użytkownik

Użytkownik (nauczyciel / terapeuta) może:
- wybrać klasę i zakres materiału,
- określić liczbę i typ zadań,
- wybrać **profil ucznia** (funkcjonalny, bez danych osobowych),
- wygenerować kartę pracy w formacie PDF (A4),
- opcjonalnie wygenerować wersję z odpowiedziami,
- wrócić do wcześniejszych kart w historii i ocenić ich jakość.

---

## 🧠 Profile uczniów (PPP)

Friendly Math wykorzystuje **profile uczniów (Pupil Profile Presets)**,
które wpływają na sposób tłumaczenia i konstruowania zadań.

Obsługiwane profile:
- standardowy,
- ADHD,
- dyskalkulia,
- dysleksja,
- trudności w nauce,
- zdolny.

Profile **nie przechowują danych osobowych** i służą wyłącznie
do dostosowania stylu dydaktycznego.

---

## 🏗️ Jak to działa

1. Użytkownik wprowadza parametry karty pracy.
2. System:
   - rozwiązuje temat i profil ucznia,
   - generuje lub dobiera zadania zastępcze zgodne z tematem,
   - egzekwuje politykę profilu i waliduje zadania,
   - generuje ilustracje i raport pokrycia,
   - dobiera layout zależny od profilu i ilustracji,
   - buduje PDF oraz opcjonalny klucz odpowiedzi.
3. Wynikiem jest gotowa karta pracy PDF do wydruku i zapis w historii lokalnej.

---

# EN Technical Overview

## Architecture

The application consists of:
- Streamlit-based web UI,
- worksheet orchestration service,
- curriculum topic and student profile catalogs,
- profile-aware AI prompts, deterministic fallbacks, and validators,
- deterministic image generation utilities,
- PDF layout and export module,
- local worksheet history and review tools.

Więcej o domenach i architekturze: [docs/architecture-and-domain.md](docs/architecture-and-domain.md).

---

## Student Profiles (PPP – Technical)

Student profiles are implemented as **pedagogical presets** used by prompts,
fallbacks, validators, visuals, and PDF layout.

Profiles currently supported:
- standardowy
- ADHD
- dyskalkulia
- dysleksja
- trudności w nauce
- zdolny

Profiles are implemented in domain catalogs and pedagogy specs, then consumed by
task generation, validation, image policy, and layout resolution.

---

## Tech Stack

- Python 3.11
- Streamlit
- OpenAI API
- Pillow, ReportLab
- PyMuPDF (opcjonalnie — podgląd PDF jako obrazy w UI)
- pytest

---

## Deploy na Streamlit Cloud

1. Wypchnij repozytorium na GitHub.
2. Wejdź na [share.streamlit.io](https://share.streamlit.io), zaloguj się przez GitHub.
3. **New app** → wybierz repo `friendly-math`, branch `main`, plik główny: `app/ui/app.py`, ścieżka: `app/ui/app.py`.
4. W **Advanced settings** ustaw **Python version**: 3.11.
5. W sekcji **Secrets** dodaj (np. TOML):
   ```toml
   OPENAI_API_KEY = "sk-..."
   ```
6. Deploy — aplikacja będzie dostępna pod linkiem `https://...streamlit.app`.

Uwaga: bez `OPENAI_API_KEY` w Secrets aplikacja uruchomi się, ale generowanie zadań wyświetli komunikat o braku klucza.

---

## Release / Git

Z katalogu projektu:

```bash
git status
python -m pytest tests/
git add README.md CHANGELOG.md app/ tests/
git commit -m "Release v1.3.0: PDF quality and profile-aware worksheets."
git push origin dev
```

Główna gałąź deployu to `main`; prace rozwojowe są prowadzone na `dev`.

---

## Project Status

**v1.3.0 — PDF quality i profile-aware worksheets**

The current focus is on validating:
- pedagogical assumptions,
- usability for teachers and therapists,
- quality of generated worksheets.

---

## Roadmap (high-level)

Future versions may include:
- stronger reference-quality evaluation,
- better automated review of generated worksheets,
- interactive student mode,
- step-by-step hints,
- error analysis,
- adaptive difficulty levels.

---

## Local Development Setup

Pełna instrukcja (venv/conda, font, smoke, lockfile): **[docs/install.md](docs/install.md)**.

```bash
git clone https://github.com/tombalab/friendly-math.git
cd friendly-math

python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # uzupełnij OPENAI_API_KEY

python scripts/smoke_check.py   # offline: importy, font, PDF
streamlit run app/ui/app.py
```

Aplikacja: http://localhost:8501