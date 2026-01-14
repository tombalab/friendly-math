# prompts/system_with_profile.py

#--------------------------------------------------
# Budowanie promptu systemu z profilem ucznia
#--------------------------------------------------
# Parametry:
# - base_prompt: prompt bazowy
# - profile: profil ucznia
#--------------------------------------------------
# Zwraca:
# - prompt systemu z profilem ucznia
#--------------------------------------------------
# Funkcja tworzy prompt dla modelu AI.
# Bazowy prompt + profil ucznia → jeden spójny tekst.
# AI dzięki temu wie:
#   - jaki ma styl wypowiedzi, tempo, sposób tłumaczenia
#   - które zasady zastosować w odpowiedziach
#--------------------------------------------------


def build_system_prompt(base_prompt: str, profile):
    profile_section = f"""
PROFIL UCZNIA: {profile.name}

Zasady pracy z tym uczniem:
{profile.render_rules()}
"""

    return base_prompt + "\n\n" + profile_section
