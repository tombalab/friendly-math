"""
Day 12: Test różnicowania profili - porównanie zadań dla różnych profili.
Uruchom: python test_profiles.py
"""
import sys
from pathlib import Path

# Dodaj ścieżkę do app
sys.path.insert(0, str(Path(__file__).parent))

from app.ai.text_generator import generate_tasks


def test_profiles():
    """Test generowania zadań dla różnych profili."""
    
    # Scenariusze testowe zgodnie z planem Day 12
    test_cases = [
        {"profile": "dyskalkulia", "grade": "2", "topic": "dodawanie", "n": 3},
        {"profile": "ADHD", "grade": "3", "topic": "mnożenie", "n": 3},
        {"profile": "zdolny", "grade": "4", "topic": "odejmowanie", "n": 3},
        {"profile": "trudności w nauce", "grade": "2", "topic": "dodawanie", "n": 3},
        {"profile": "standardowy", "grade": "3", "topic": "dodawanie", "n": 3},
    ]
    
    print("=" * 80)
    print("Day 12: Test różnicowania profili - porównanie zadań")
    print("=" * 80)
    print()
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}: {case['profile'].upper()}")
        print(f"Klasa: {case['grade']}, Temat: {case['topic']}, Liczba zadań: {case['n']}")
        print(f"{'='*80}")
        
        try:
            result = generate_tasks(
                profile=case["profile"],
                grade=case["grade"],
                topic=case["topic"],
                n=case["n"]
            )
            
            tasks = result.get("tasks", [])
            if result.get("_error"):
                print(f"⚠️  Błąd: {result['_error']}")
            
            print(f"\nWygenerowane zadania ({len(tasks)}):")
            for j, task in enumerate(tasks, 1):
                # Analiza zadania
                task_len = len(task)
                has_numbers = any(c.isdigit() for c in task)
                num_count = sum(c.isdigit() for c in task)
                
                print(f"  {j}. {task}")
                print(f"     (długość: {task_len} znaków, liczb: {num_count})")
            
            # Podsumowanie dla profilu
            avg_len = sum(len(t) for t in tasks) / len(tasks) if tasks else 0
            print(f"\n📊 Podsumowanie:")
            print(f"   Średnia długość zadania: {avg_len:.1f} znaków")
            print(f"   Liczba zadań: {len(tasks)}")
            
        except Exception as e:
            print(f"❌ Błąd podczas generowania: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print("\n" + "=" * 80)
    print("Test zakończony. Porównaj różnice w:")
    print("  - długości poleceń (ADHD powinno być krótsze)")
    print("  - trudności liczb (dyskalkulia: 1-12, zdolny: większe)")
    print("  - formacie (ADHD: wyraźny format 'Policz: X op Y = ____')")
    print("  - złożoności (zdolny: może mieć dwa kroki)")
    print("=" * 80)


if __name__ == "__main__":
    test_profiles()
