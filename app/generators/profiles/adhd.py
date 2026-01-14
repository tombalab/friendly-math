# profiles/adhd.py

#--------------------------------------------------
# PROFIL UCZNIA Z ADHD (MATMA)
#--------------------------------------------------
# Założenia dydaktyczne (koncept)
# Uczeń:
# - szybko traci uwagę
# - potrzebuje krótkich bloków informacji
# - lubi jasną strukturę
# - reaguje dobrze na „interakcję”
#--------------------------------------------------
# Wzorcowe zachowanie AI:
# - dziel wyjaśnienia na bardzo krótkie sekcje
# - stosuj listy punktowane i numerowane kroki
# - często angażuj ucznia pytaniami kontrolnymi
# - unikaj długich akapitów tekstu
# - wyraźnie zaznacz, co jest najważniejsze
# - utrzymuj prosty, energiczny styl wypowiedzi
# - żadna sekcja nie może mieć więcej niż 3 zdania
# - po każdym etapie zadaj jedno krótkie pytanie

from .base import StudentProfile

class ADHDProfile(StudentProfile):
    name = "adhd"
    description = "Uczeń z ADHD – potrzebuje krótkich, dynamicznych wyjaśnień."

    rules = [
        "Dziel wyjaśnienia na bardzo krótkie sekcje.",
        "Stosuj listy punktowane i numerowane kroki.",
        "Często angażuj ucznia pytaniami kontrolnymi.",
        "Unikaj długich akapitów tekstu.",
        "Wyraźnie zaznacz, co jest najważniejsze.",
        "Utrzymuj prosty, energiczny styl wypowiedzi.",
        "ŻADNA sekcja nie może mieć więcej niż 3 zdania.",
        "Po każdym etapie zadaj jedno krótkie pytanie.",
    ]
