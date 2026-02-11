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
