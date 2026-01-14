# profiles/base.py
# każdy profil dziedziczy po tej klasie.

class StudentProfile:
    name = "base"
    description = ""

    rules = []

    def render_rules(self):
        return "\n".join(f"- {rule}" for rule in self.rules)
