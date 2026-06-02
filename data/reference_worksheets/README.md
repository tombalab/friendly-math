# Wzorcowe karty pracy (reference worksheets)

Folder zawiera ręcznie napisane przykłady „dobrych" kart pracy w formacie JSON.
Służą jako:

1. **Punkt odniesienia jakości** — czego oczekujemy od generatora dla danego profilu/klasy/tematu.
2. **Materiał do few-shot prompts** — przykłady, które można wstrzyknąć do prompta zamiast aktualnych „przykładów inline" w `text_generator.py`.
3. **Dane do oceny** — porównanie tego, co generuje AI, z tym, co napisałby nauczyciel.

## Format pliku

Każdy plik to jeden JSON. Konwencja nazwy: `{grade}_{topic}_{profile}.json`
(np. `2_dodawanie_dyskalkulia.json`).

```json
{
  "metadata": {
    "title": "Karta pracy – klasa 2 – dodawanie",
    "grade": 2,
    "topic": "dodawanie",
    "profile": "dyskalkulia",
    "author": "Imię Nazwisko",
    "source": "własna / podręcznik X / nauczyciel Y",
    "notes": "Krótki komentarz: na co zwrócić uwagę w tej karcie."
  },
  "tasks": [
    "Policz: 3 + 4 = ____",
    "..."
  ],
  "answers": ["7", "..."],
  "quality_criteria": [
    "Liczby w zakresie klasy.",
    "Polecenia krótkie, jeden krok.",
    "..."
  ],
  "structured_criteria": {
    "max_operand": 12,
    "max_result": 20,
    "allowed_operations": ["+"],
    "max_operations_per_task": 1,
    "max_task_length": 50,
    "require_format_prefix": "Policz:",
    "require_format_consistent": true
  }
}
```

Pole `structured_criteria` (P2.2) uzupełnia listę tekstową — te same progi sprawdza
`app/validators/task_validator.py` w testach referencyjnych i po generacji w `WorksheetService`.

## Po co to teraz

Bez tych przykładów nie da się sensownie oceniać jakości generowanych kart
— „lepiej" / „gorzej" jest subiektywne. Z 5–10 wzorcami możemy:

- Robić proste porównanie A/B (wzorzec vs AI) ręcznie.
- Później (faza 2) – włączyć je do automatycznego eval pipeline'u.
- Wstrzykiwać konkretne zadania jako few-shot dla danego profilu (lepiej niż obecne stałe inline w `text_generator.py`).

## Jak dodać nową kartę

1. Skopiuj jeden z istniejących plików.
2. Wpisz nową treść (zadania, odpowiedzi, metadane).
3. Pole `quality_criteria` opisz po swojemu – to pomaga przy późniejszym tworzeniu
   automatycznych testów oceniających generowane karty.
