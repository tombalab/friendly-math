# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/)
and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Added
- AI-powered task generation
- Export to PDF and DOCX formats

### Changed
- —

### Planned
- Deployment to Streamlit Cloud

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
