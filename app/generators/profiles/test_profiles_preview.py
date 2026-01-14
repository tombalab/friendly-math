"""
Test porównawczy presetów ucznia (PPP)
Cel: sprawdzić, jak profile wpływają na prompt systemowy
"""

from app.generators.profiles.dyskalkulia import DyskalkuliaProfile
from app.generators.profiles.adhd import ADHDProfile
from app.backend.prompts.system_with_profile import build_system_prompt


def run_profile_test():
    base_prompt = """
Jesteś Friendly Math – cierpliwym nauczycielem matematyki.
Twoim celem jest tłumaczyć matematykę w sposób zrozumiały,
bez oceniania i presji.
"""

    problem = "Oblicz 3 × (4 + 2)"

    profiles = [
        DyskalkuliaProfile(),
        ADHDProfile(),
    ]

    for profile in profiles:
        print("\n" + "=" * 60)
        print(f"PROFIL: {profile.name.upper()}")
        print("=" * 60)

        system_prompt = build_system_prompt(base_prompt, profile)

        print("\n--- SYSTEM PROMPT ---\n")
        print(system_prompt)

        print("\n--- ZADANIE ---\n")
        print(problem)


if __name__ == "__main__":
    run_profile_test()
