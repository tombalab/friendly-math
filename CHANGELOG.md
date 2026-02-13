# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/)
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- 

### Changed
-

### Planned
- 


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
