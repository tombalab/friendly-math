# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/)
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Faza 1: `docs/curriculum-matrix.md` — kontrakt topic_id × klasa × blueprint × klucz × wzorzec
- Skrypty `scripts/curriculum_fallback_audit.py`, `scripts/curriculum_matrix_report.py`; test audytu
- Faza 0: komunikat MVP dla klas 4–8, ostrzeżenia przy „Dołącz odpowiedzi” (tematy partial/none)
- Phase 3: zakładki **Generuj / Historia / Recenzja** w Streamlit
- Filtry historii (klasa, temat), status jakości, zapis recenzji (`review.json`)
- Dopasowanie do kart wzorcowych (`app/review/`)
- 18 nowych kart wzorcowych (łącznie 22, klasy 1–8)
- Dokumenty PP 2025/2026, `docs/teacher-review.md`, `docs/phase3-decision.md`, macierz w `docs/curriculum-matrix-plan.canvas.tsx`

### Changed
- Walidatory profil×temat: limity zależne od tematu (mnożenie kl. 5, porównania, zadania tekstowe bez fałszywych `word_problem_load`)
- Blueprinty kl. 3 dla dodawania/odejmowania do 20; ułamki 4–8 w fallbacku jako `Policz: a/b + …`
- Temat **równania** (4–8): generator i fallback używają okienka ☐ zamiast `x`; pełny klucz odpowiedzi jak we wzorcach
- Sidebar: temat i checkbox odpowiedzi poza formularzem — podpowiedzi reagują na wybór
- Panel jakości: baner statusu OK/uwagi/błąd, osobna sekcja walidacji zadań
- UI v1.2.0 w stopce, layout `wide`, checklista ograniczeń MVP

---

## [1.2.0] – 2026-06-02 – Streamlit v2 jakość P1–P2

### Added
- `WorksheetService`, kontrakty `WorksheetRequest`/`WorksheetResult`, panel jakości (P1.3–P1.6)
- Centralna polityka ilustracji i jedna warstwa layoutu PDF (P1.1, P1.5)
- Walidatory zadań wg profilu + `structured_criteria` w kartach referencyjnych (P2.1, P2.2)
- Observability: `request_id`, zdarzenia JSON, panel debug w Streamlit (P2.4)
- Lokalna historia kart w `data/history/<request_id>/`, sidebar z archiwum (P2.5)
- `requirements-lock.txt`, `scripts/smoke_check.py`, `docs/install.md`, CI smoke (P2.3)

### Changed
- `liczenie po` — pełne wsparcie klucza odpowiedzi i osobna polityka walidacji sekwencji
- Walidator ignoruje bullet `-` w zadaniach; generator czyści prefiksy list
- Deduplikacja powtarzających się ostrzeżeń w `WorksheetService`
- `README.md` — instalacja i smoke; `.gitignore` — `data/history/`

---

## [1.1.0] – 2026-06-01 – Streamlit v2 jakość P0

### Added
- Katalog tematów (`topic_id`, blueprint, możliwości odpowiedzi i ilustracji)
- Katalog profili PPP w UI (w tym dysleksja)
- Uczciwe fallbacki zadań zachowujące temat + blokada przy nieznanym temacie
- Przejrzysty klucz odpowiedzi ze statusami i podsumowaniem
- Font DejaVu + ostrzeżenia PDF/Streamlit
- Karty referencyjne i testy offline (`tests/test_reference_worksheets.py`)
- Dokumentacja architektury i backlogu (`docs/`)

### Changed
- Generator PDF zwraca `PdfBuildResult` ze strukturalnymi ostrzeżeniami
- Streamlit pokazuje degradację generacji przed PDF

---

## [1.0.0] – 2025-01-23 – MVP v1.0.0 (release)

### Added
- **Klucz odpowiedzi** — opcjonalna strona „Odpowiedzi” w PDF (checkbox „Dołącz stronę z odpowiedziami”); wyniki dla prostych zadań a op b, pozostałe „—”
- Moduł `app/generators/answers.py` — `compute_answers(tasks)` (regex)
- **Podgląd PDF w przeglądarce** — strony PDF jako obrazy (PyMuPDF, opcjonalnie); przycisk Pobierz PDF zawsze dostępny
- **Deploy na Streamlit Cloud** — opis w README (Secrets: OPENAI_API_KEY)

### Changed
- **UI**: formularz w **panelu bocznym** (sidebar), wyniki (zadania + PDF) w oknie głównym; sensowne domyślne, opisy pól, stopka „Friendly Math v1.0”
- **Obsługa błędów** — brak OPENAI_API_KEY lub timeout → komunikat w UI; zadania zastępcze przy błędzie API
- **Ilustracje (v1.0)** — celowo mniej ambitne, zawsze czytelne: max 10 kół w sumie (dodawanie/odejmowanie), mnożenie max 5×5, dzielenie max 8 elementów / 2 grupy, ułamki max 2 koła; równania — schemat „lewa = prawa”
- Sekcja JSON (request) ukryta w UI

### Technical
- `build_worksheet_pdf_bytes(..., answers=Optional[list[str]])`
- `app/ui/app.py`: opcjonalny import fitz (PyMuPDF), `_pdf_bytes_to_images()`, `st.image(..., width="stretch")`
- `app/generators/images.py`: limity max_circles, rows/cols, n_total/n_groups, n_fracs
- requirements.txt: PyMuPDF

---
## [0.8.0] – Day 10 & 11: Testy, ilustracje per zadanie, ułamki szkolne

### Added (Day 10 – testy ręczne)
- Scenariusze testowe (Klasa 2 dodawanie/dyskalkulia, Klasa 5 mnożenie/standardowy, Klasa 1 dodawanie/ADHD)
- Checklisty wizualne i funkcjonalne dla generowanego PDF
- Dokumentacja wyników testów (potwierdzenie działania PDF v1)

### Added (Day 11 – ilustracje per zadanie)
- **Ilustracja przy każdym zadaniu** – generator `generate_worksheet_images_for_tasks(tasks, topic, profile)` zwraca listę PNG (jedna na zadanie)
- **Opcja „Ilustracja w karcie”** w UI – dla profili standardowy/zdolny (dla dyskalkulia/ADHD/trudności ilustracje zawsze włączone)
- Ilustracje **zgodne z treścią zadania**: dodawanie (dwie grupy kół), odejmowanie (kółka z przekreśleniem X na „zabranych”), mnożenie (siatka wiersze×kolumny), dzielenie (grupy obok siebie), ułamki (koło podzielone na części, zaznaczone zgodnie z ułamkiem)
- **Ułamki zwykłe w zapisie szkolnym** w PDF – licznik nad kreską, kreska ułamkowa, mianownik pod kreską (zamiast 1/2)
- Parsowanie ułamków z treści zadania (`_parse_fraction_from_task`) oraz liczb (`_parse_numbers_from_task`) do generowania ilustracji

### Changed
- PDF: parametr `task_images: list[bytes]` – gdy podany, przy każdym zadaniu rysowana jest ilustracja (pełna szerokość treści); gdy brak – opcjonalnie jedna ilustracja u góry
- Ilustracje: wewnętrzny padding i `_circle_size_to_fit`, żeby skrajne kółka nie były ucinane
- Prompt dla tematu „ułamki”: instrukcja zapisu ułamków w formacie licznik/mianownik (np. 1/2, 3/4)

### Technical
- `app/generators/images.py`: `_parse_fraction_from_task()`, `_circle_size_to_fit()`, rozszerzona logika tematów w `generate_worksheet_images_for_tasks`
- `app/pdf/generator.py`: `_split_line_into_segments()`, `_draw_fraction()`, `_draw_task_line_with_fractions()` – rysowanie ułamków z kreską
- `app/ai/text_generator.py`: warunkowa instrukcja dla ułamków w `_build_prompt`

---
## [0.7.0] – PDF v1: Readable worksheet (Day 9)

### Added
- Page background color support (from layout, e.g., light gray `#fafafa` for low-stimuli profiles)
- Visual separator line below "Tasks" section
- Dynamic text wrapping (adjusted to page width and font size, 60–85 characters)
- Footer with page numbers ("Friendly Math — strona X")

### Changed
- PDF generator upgraded from v0 to v1 (readable, print-ready worksheet)
- Background color applied to all pages (including new pages when tasks overflow)
- Text wrapping now adapts to font size (larger fonts = fewer characters per line)

### Technical
- Function `_draw_page_background()` for consistent background rendering
- Function `_draw_footer()` for page numbering
- Dynamic `max_chars` calculation based on available width and font size

---
## [0.6.0] – Worksheet image generator (Day 8)

### Added
- Worksheet image generator (Pillow, low-stimuli style)
- One illustration per PDF (simple shapes: circles, rectangles)
- Topic-linked graphics (addition → groups, multiplication → 2×3 grid, fractions → half circle, etc.)
- Optional image in PDF below metadata (before “Tasks” section)

### Technical
- Module `app/generators/images.py` – `generate_worksheet_image(topic, profile)`
- Parameter `image_bytes` in `build_worksheet_pdf_bytes()` (ReportLab `drawImage`)

---
## [0.5.0] – PDF Export & AI Task Generation

### Added
- PDF export functionality (ReportLab)
- Polish character support (DejaVu Sans font)
- OpenAI API integration for task generation
- Dynamic task generation based on student profile
- PDF download button in Streamlit UI
- Automatic PDF file save to `data/out/worksheet.pdf`

### Changed
- Task generator now uses OpenAI API (GPT-3.5-turbo) instead of hardcoded tasks
- Prompts optimized for educational content (Day 6 improvements)
- Short, focused prompts for single task type

### Technical
- Added `app/pdf/generator.py` module
- Updated `app/ai/text_generator.py` with OpenAI integration
- Environment variable support for API keys (`.env`)

---
## [0.4.0] – First public MVP

### Added
- First public MVP of Friendly Math
- Streamlit UI with student profile selection
- End-to-end flow: input → task generation → output
- Placeholder task generator (text-only)

### Notes
- This version uses a simplified task generator (no real AI yet)
- UI and architecture prepared for future AI integration

---

## [0.3.0] – Student Profiles (PPP)

### Added
- Pupil Profile Presets (PPP) architecture
- Student profiles: Dyskalkulia, ADHD
- Dynamic system prompt adaptation based on selected student profile
- Profile prompt preview script (no UI or LLM required)

### Changed
- System prompt extended with pedagogical constraints

### Fixed
- Formatting issues in student profile rules

---

## [0.2.0] – Core App Structure & Prompt Foundations

### Added
- Initial Streamlit UI structure
- Core application layout (UI / backend / generators)
- Prompt handling foundation for math task generation
- Basic task and image generator modules
- Example datasets and worksheet samples

### Changed
- Project structure reorganized for scalability
- Clear separation of UI, backend logic, and content generators

### Notes
- This release establishes the technical foundation for future personalization
- No student profiles or adaptive behavior introduced yet

---

## [0.1.0] – Initial Streamlit UI & Input Flow

### Added
- First functional Streamlit user interface
- Input form for grade, topic, number of tasks, and student profile
- JSON-based request generation
- Basic input validation for grades 1–3

---

## [0.0.1] – Project Initialization & Environment Setup

### Added
- Initial project structure
- README documentation
- Local development environment setup (Conda + pip)
