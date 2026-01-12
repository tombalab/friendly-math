# Friendly Math v1 🧮

**Friendly Math v1** to inteligentny generator i trener matematyki,
zaprojektowany z myślą o uczniach szkoły podstawowej,
ze szczególnym uwzględnieniem uczniów z opiniami i orzeczeniami PPP
(np. dyskalkulia, ADHD, trudności w koncentracji).

Projekt koncentruje się na tworzeniu **czytelnych, niskobodziecowych kart pracy PDF**
oraz wspieraniu procesu uczenia się matematyki w sposób przyjazny i zrozumiały.

---

## 🎯 Cel v1

- wspieranie uczniów z trudnościami w nauce matematyki,
- ułatwienie pracy nauczycielom i terapeutom,
- szybkie generowanie kart pracy dopasowanych do potrzeb ucznia,
- tworzenie materiałów edukacyjnych gotowych do druku (PDF A4).

---

## 👤 Co może zrobić użytkownik (v1)

Użytkownik (nauczyciel / terapeuta) może:
- wybrać klasę i zakres materiału,
- określić liczbę zadań,
- wybrać typ zadań (np. rachunki, zadania tekstowe),
- określić profil ucznia (funkcjonalny, bez danych osobowych),
- wygenerować kartę pracy w formacie PDF (A4),
- opcjonalnie wygenerować wersję z odpowiedziami.

---

## 🧠 Jak to działa (v1)

1. Użytkownik wprowadza parametry karty pracy.
2. System:
   - generuje zadania matematyczne,
   - tworzy proste grafiki wspierające rozumienie,
   - układa treść w czytelny, niskobodziecowy layout.
3. Wynikiem jest gotowa karta pracy PDF do wydruku.

---

## 🏗️ Architektura v1

Aplikacja składa się z:
- interfejsu webowego (Streamlit),
- logiki generowania treści (AI),
- modułu generowania grafiki,
- modułu składu i eksportu PDF.


![Friendly Math v1 – Architecture Diagram](docs/architecture/Friendly_Math_Architecture_v1.png)

---

## 🛠️ Technologie (v1)

- Python
- Streamlit
- OpenAI API
- Pillow
- ReportLab

---

## 🚧 Status projektu

Projekt w fazie **v1 / MVP**  
Celem jest walidacja pomysłu i jakości generowanych materiałów edukacyjnych.

---

## 🔮 Kierunek rozwoju (zarys)

Kolejne wersje mogą obejmować:
- interaktywną pracę ucznia online,
- podpowiedzi krok po kroku,
- analizę błędów,
- adaptacyjny poziom trudności.

