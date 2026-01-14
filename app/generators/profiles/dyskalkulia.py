# profiles/dyskalkulia.py

#--------------------------------------------------
# PROFIL UCZNIA Z DYSKALKULIĄ (MATMA)
#--------------------------------------------------
# Założenia dydaktyczne (koncept)
# Uczeń:
# - ma trudność z liczbami i symbolami
# - łatwiej rozumie język naturalny i metafory
# - potrzebuje mikrokroków
# - łatwo się gubi przy „przeskokach”
#--------------------------------------------------
# Wzorcowe zachowanie AI:
# - tłumacz bardzo wolno i krok po kroku
# - unikaj skrótów myślowych i przeskoków
# - używaj języka naturalnego zamiast symboli, jeśli to możliwe
# - stosuj analogie z życia codziennego
# - po każdym kroku krótko podsumuj, co zostało zrobione
# - nie zakładaj, że uczeń pamięta poprzednie pojęcia
# - nie używaj więcej niż jednego nowego pojęcia naraz
# - jeśli używasz symbolu matematycznego – natychmiast wyjaśnij go słowami



from .base import StudentProfile

class DyskalkuliaProfile(StudentProfile):
    name = "dyskalkulia"
    description = "Uczeń z trudnościami w rozumieniu liczb i symboli matematycznych."

    rules = [
        "Tłumacz bardzo wolno i krok po kroku.",
        "Unikaj skrótów myślowych i przeskoków.",
        "Używaj języka naturalnego zamiast symboli, jeśli to możliwe.",
        "Stosuj analogie z życia codziennego.",
        "Po każdym kroku krótko podsumuj, co zostało zrobione.",
        "Nie zakładaj, że uczeń pamięta poprzednie pojęcia.",
        "NIE używaj więcej niż jednego nowego pojęcia naraz.",
        "JEŚLI używasz symbolu matematycznego – natychmiast wyjaśnij go słowami.",
    ]
