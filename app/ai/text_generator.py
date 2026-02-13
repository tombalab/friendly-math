import os
from dotenv import load_dotenv
from openai import OpenAI

# Ładowanie zmiennych z .env
load_dotenv()

# Inicjalizacja klienta OpenAI
_client = None

def _get_client():
    """Lazy initialization OpenAI client."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY nie znaleziony w .env. "
                "Sprawdź czy masz plik .env z kluczem API."
            )
        _client = OpenAI(api_key=api_key)
    return _client

def _build_prompt(grade: str, topic: str, profile: str, n: int) -> str:
    """
    Buduje krótki, edukacyjny prompt dla jednego typu zadania.
    Day 6: prosty, bez finezji, skupiony na jednym typie.
    """
    # Mapowanie profilu na krótkie instrukcje
    profile_hints = {
        "dyskalkulia": "Używaj prostych liczb (1-20), krótkich poleceń, unikaj symboli.",
        "ADHD": "Krótkie, konkretne polecenia. Jeden krok na raz.",
        "standardowy": "Standardowe zadania dla klasy.",
        "zdolny": "Zadania z lekkim wyzwaniem.",
        "trudności w nauce": "Proste zadania, dużo miejsca na odpowiedź.",
        "dysleksja": "Krótkie polecenia, czytelne liczby."
    }
    
    profile_instruction = profile_hints.get(profile, "Standardowe zadania.")
    
    # Dla ułamków: zapis licznik/mianownik (np. 1/2, 3/4) – będzie wyświetlany szkolnie z kreską ułamkową
    fraction_instruction = (
        ' Dla tematu "ułamki zwykłe" używaj ułamków w formacie licznik/mianownik (np. 1/2, 3/4, 2/5).'
        if topic and "ułamk" in topic.lower()
        else ""
    )
    prompt = f"""Jesteś nauczycielem matematyki. Wygeneruj {n} zadań dla klasy {grade} na temat: {topic}.

    Wymagania:
    - {profile_instruction}
    - Każde zadanie w jednej linii.
    - Format: "Policz: [treść zadania] = ____" lub "Zaznacz [ułamek] ..." itp.
    - Używaj tylko liczb całkowitych (poza ułamkami).{fraction_instruction}
    - Zadania dostosowane do klasy {grade}.

    Wygeneruj tylko listę zadań, po jednym w linii, bez numeracji, bez dodatkowych komentarzy."""

    return prompt

def generate_tasks(profile, grade, topic, n=3):
    """
    Generuje zadania matematyczne używając OpenAI API.
    Day 6: prosty prompt, jeden typ zadania, edukacyjne.
    """
    try:
        client = _get_client()
        prompt = _build_prompt(grade=str(grade), topic=topic, profile=profile, n=n)
        
        # Wywołanie API (używamy gpt-3.5-turbo dla oszczędności kosztów)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Jesteś pomocnym nauczycielem matematyki."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        # Parsowanie odpowiedzi - każda linia to jedno zadanie
        tasks_text = response.choices[0].message.content.strip()
        tasks = [line.strip() for line in tasks_text.split("\n") if line.strip()]
        
        # Fallback jeśli AI zwróciło mniej zadań niż prosiłeś
        if len(tasks) < n:
            # Dodaj proste zadania placeholder
            while len(tasks) < n:
                tasks.append(f"Policz: {2 + len(tasks)} + {3 + len(tasks)} = ____")
        
        return {
            "tasks": tasks[:n],  # Upewniamy się, że nie ma więcej niż n zadań
            "profile": profile,
            "grade": grade,
            "topic": topic
        }
    
    except Exception as e:
        # Fallback na hardcoded zadania jeśli API nie działa
        return {
            "tasks": [
                "Policz: 3 + 4 = ____",
                "Policz: 7 − 2 = ____",
                "Policz: 5 + 5 = ____"
            ],
            "profile": profile,
            "grade": grade,
            "topic": topic,
            "_error": str(e)  # Opcjonalnie: możesz to wyświetlić w UI dla debugowania
        }

# Initial version for v0.4.0 testing - hardcoded
#
# def generate_tasks(profile, grade, topic, n=3):
#     return {
#         "tasks": [
#             "Policz: 3 + 4 = ____",
#             "Policz: 7 − 2 = ____",
#             "Policz: 5 + 5 = ____"
#         ],
#         "profile": profile,
#         "grade": grade,
#         "topic": topic
#    }
