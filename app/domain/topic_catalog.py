"""
Centralny katalog tematów (P0.1).

Stabilne `topic_id`, etykiety PL, aliasy, klasy, powiązanie z blueprintem
oraz metadane możliwości (odpowiedzi, ilustracje).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

from app.ai.topic_blueprints import get_blueprint

AnswerSupport = Literal["full", "partial", "none"]
BlueprintStatus = Literal["exact", "downgraded", "missing", "unknown"]


@dataclass(frozen=True)
class TopicCapabilities:
    """Wspólne flagi zachowania generatorów dla danego tematu."""

    answer_support: AnswerSupport
    # Rodzina ilustracji (klucze _SAFE_LIMITS / TOPIC_THEMES w images.py).
    visual_family: Optional[str] = None
    # Brak ilustracji nagłówka i per-zadanie (np. równania algebraiczne).
    skip_images: bool = False
    supports_per_task_visuals: bool = True
    supports_header_visual: bool = True


@dataclass(frozen=True)
class TopicDefinition:
    topic_id: str
    label_pl: str
    blueprint_key: str
    grades_min: int
    grades_max: int
    capabilities: TopicCapabilities
    aliases: tuple[str, ...] = ()


@dataclass
class ResolvedTopic:
    topic_id: str
    label_pl: str
    blueprint_key: str
    grade: int
    blueprint_status: BlueprintStatus
    capabilities: TopicCapabilities
    warnings: list[str] = field(default_factory=list)

    @property
    def has_blueprint(self) -> bool:
        return self.blueprint_status in ("exact", "downgraded")


def _cap(
    answer: AnswerSupport,
    visual: Optional[str] = None,
    *,
    skip_images: bool = False,
    per_task: bool = True,
    header: bool = True,
) -> TopicCapabilities:
    if skip_images:
        per_task = False
        header = False
    return TopicCapabilities(
        answer_support=answer,
        visual_family=visual,
        skip_images=skip_images,
        supports_per_task_visuals=per_task,
        supports_header_visual=header,
    )


# ---------------------------------------------------------------------------
# Rejestr tematów — topic_id jest stabilnym identyfikatorem domenowym.
# blueprint_key musi odpowiadać kluczowi w TOPIC_BLUEPRINTS (lowercase PL).
# ---------------------------------------------------------------------------

TOPIC_CATALOG: dict[str, TopicDefinition] = {
    "liczenie_po": TopicDefinition(
        topic_id="liczenie_po",
        label_pl="liczenie po",
        blueprint_key="liczenie po",
        grades_min=1,
        grades_max=3,
        capabilities=_cap("full"),
        aliases=("liczenie",),
    ),
    "porownywanie_liczb": TopicDefinition(
        topic_id="porownywanie_liczb",
        label_pl="porównywanie liczb",
        blueprint_key="porównywanie liczb",
        grades_min=1,
        grades_max=3,
        capabilities=_cap("full"),
    ),
    "dodawanie_do_20": TopicDefinition(
        topic_id="dodawanie_do_20",
        label_pl="dodawanie do 20",
        blueprint_key="dodawanie do 20",
        grades_min=1,
        grades_max=3,
        capabilities=_cap("full", "dodawanie"),
    ),
    "dodawanie_do_100": TopicDefinition(
        topic_id="dodawanie_do_100",
        label_pl="dodawanie do 100",
        blueprint_key="dodawanie do 100",
        grades_min=2,
        grades_max=3,
        capabilities=_cap("full", "dodawanie"),
    ),
    "dodawanie_do_1000": TopicDefinition(
        topic_id="dodawanie_do_1000",
        label_pl="dodawanie do 1000",
        blueprint_key="dodawanie do 1000",
        grades_min=3,
        grades_max=3,
        capabilities=_cap("full", "dodawanie"),
    ),
    "odejmowanie_do_20": TopicDefinition(
        topic_id="odejmowanie_do_20",
        label_pl="odejmowanie do 20",
        blueprint_key="odejmowanie do 20",
        grades_min=1,
        grades_max=3,
        capabilities=_cap("full", "odejmowanie"),
    ),
    "odejmowanie_do_100": TopicDefinition(
        topic_id="odejmowanie_do_100",
        label_pl="odejmowanie do 100",
        blueprint_key="odejmowanie do 100",
        grades_min=2,
        grades_max=3,
        capabilities=_cap("full", "odejmowanie"),
    ),
    "odejmowanie_do_1000": TopicDefinition(
        topic_id="odejmowanie_do_1000",
        label_pl="odejmowanie do 1000",
        blueprint_key="odejmowanie do 1000",
        grades_min=3,
        grades_max=3,
        capabilities=_cap("full", "odejmowanie"),
    ),
    "tabliczka_mnozenia": TopicDefinition(
        topic_id="tabliczka_mnozenia",
        label_pl="tabliczka mnożenia",
        blueprint_key="tabliczka mnożenia",
        grades_min=2,
        grades_max=3,
        capabilities=_cap("full", "mnożenie"),
    ),
    "mnozenie_przez_10": TopicDefinition(
        topic_id="mnozenie_przez_10",
        label_pl="mnożenie przez 10",
        blueprint_key="mnożenie przez 10",
        grades_min=2,
        grades_max=3,
        capabilities=_cap("full", "mnożenie"),
    ),
    "dzielenie": TopicDefinition(
        topic_id="dzielenie",
        label_pl="dzielenie",
        blueprint_key="dzielenie",
        grades_min=2,
        grades_max=8,
        capabilities=_cap("full", "dzielenie"),
    ),
    "rownania_z_okienkiem": TopicDefinition(
        topic_id="rownania_z_okienkiem",
        label_pl="równania z okienkiem",
        blueprint_key="równania z okienkiem",
        grades_min=1,
        grades_max=3,
        capabilities=_cap("full", per_task=False, header=False),
    ),
    "ulamki": TopicDefinition(
        topic_id="ulamki",
        label_pl="ułamki",
        blueprint_key="ułamki",
        grades_min=2,
        grades_max=8,
        capabilities=_cap("partial", "ułamki"),
    ),
    "pieniadze": TopicDefinition(
        topic_id="pieniadze",
        label_pl="pieniądze",
        blueprint_key="pieniądze",
        grades_min=2,
        grades_max=3,
        capabilities=_cap("none"),
    ),
    "czas": TopicDefinition(
        topic_id="czas",
        label_pl="czas",
        blueprint_key="czas",
        grades_min=1,
        grades_max=3,
        capabilities=_cap("none"),
    ),
    "pomiary_dlugosci": TopicDefinition(
        topic_id="pomiary_dlugosci",
        label_pl="pomiary długości",
        blueprint_key="pomiary długości",
        grades_min=1,
        grades_max=3,
        capabilities=_cap("none"),
    ),
    "obwody": TopicDefinition(
        topic_id="obwody",
        label_pl="obwody",
        blueprint_key="obwody",
        grades_min=2,
        grades_max=3,
        capabilities=_cap("none"),
    ),
    "zadania_tekstowe": TopicDefinition(
        topic_id="zadania_tekstowe",
        label_pl="zadania tekstowe",
        blueprint_key="zadania tekstowe",
        grades_min=1,
        grades_max=3,
        capabilities=_cap("none"),
    ),
    "dodawanie": TopicDefinition(
        topic_id="dodawanie",
        label_pl="dodawanie",
        blueprint_key="dodawanie",
        grades_min=4,
        grades_max=8,
        capabilities=_cap("full", "dodawanie"),
    ),
    "odejmowanie": TopicDefinition(
        topic_id="odejmowanie",
        label_pl="odejmowanie",
        blueprint_key="odejmowanie",
        grades_min=4,
        grades_max=8,
        capabilities=_cap("full", "odejmowanie"),
    ),
    "mnozenie": TopicDefinition(
        topic_id="mnozenie",
        label_pl="mnożenie",
        blueprint_key="mnożenie",
        grades_min=4,
        grades_max=8,
        capabilities=_cap("full", "mnożenie"),
    ),
    "rownania": TopicDefinition(
        topic_id="rownania",
        label_pl="równania",
        blueprint_key="równania",
        grades_min=4,
        grades_max=8,
        capabilities=_cap("full", skip_images=True),
    ),
}

# Kolejność wyświetlania w UI (zgodna z dotychczasowym selectboxem).
TOPIC_DISPLAY_ORDER: tuple[str, ...] = (
    "liczenie_po",
    "porownywanie_liczb",
    "dodawanie_do_20",
    "dodawanie_do_100",
    "dodawanie_do_1000",
    "odejmowanie_do_20",
    "odejmowanie_do_100",
    "odejmowanie_do_1000",
    "tabliczka_mnozenia",
    "mnozenie_przez_10",
    "dzielenie",
    "rownania_z_okienkiem",
    "ulamki",
    "pieniadze",
    "czas",
    "pomiary_dlugosci",
    "obwody",
    "zadania_tekstowe",
    "dodawanie",
    "odejmowanie",
    "mnozenie",
    "rownania",
)


def _normalize(text: str) -> str:
    return (text or "").strip().lower()


def _lookup_index() -> dict[str, str]:
    """Mapuje znormalizowany label/alias/id -> topic_id."""
    idx: dict[str, str] = {}
    for tid, defn in TOPIC_CATALOG.items():
        idx[_normalize(tid)] = tid
        idx[_normalize(defn.label_pl)] = tid
        idx[_normalize(defn.blueprint_key)] = tid
        for alias in defn.aliases:
            idx[_normalize(alias)] = tid
    return idx


_LOOKUP = _lookup_index()


def get_topic(topic_id: str) -> Optional[TopicDefinition]:
    return TOPIC_CATALOG.get(topic_id)


def topic_available_for_grade(defn: TopicDefinition, grade: int) -> bool:
    """Temat dostępny, jeśli klasa mieści się w zakresie i istnieje blueprint."""
    if grade < defn.grades_min or grade > defn.grades_max:
        return False
    bp = get_blueprint(defn.blueprint_key, grade)
    return bp is not None


def topic_labels_for_grade(grade: int) -> list[str]:
    """Etykiety PL do selectboxa Streamlit dla danej klasy."""
    labels: list[str] = []
    for tid in TOPIC_DISPLAY_ORDER:
        defn = TOPIC_CATALOG[tid]
        if topic_available_for_grade(defn, grade):
            labels.append(defn.label_pl)
    return labels


def default_topic_label_for_grade(grade: int) -> str:
    labels = topic_labels_for_grade(grade)
    if not labels:
        return TOPIC_CATALOG["dodawanie_do_20"].label_pl
    preferred = TOPIC_CATALOG["dodawanie_do_20"].label_pl
    if preferred in labels:
        return preferred
    return labels[0]


def resolve_topic(topic_input: str, grade: int) -> ResolvedTopic:
    """
    Rozwiązuje wejście (topic_id, label lub alias) do ResolvedTopic.
    Ustala status blueprintu i zbiera ostrzeżenia dla UI.
    """
    norm = _normalize(topic_input)
    topic_id = _LOOKUP.get(norm)
    warnings: list[str] = []

    if not topic_id:
        return ResolvedTopic(
            topic_id="unknown",
            label_pl=topic_input,
            blueprint_key=norm,
            grade=grade,
            blueprint_status="unknown",
            capabilities=_cap("none"),
            warnings=[
                f"Nieznany temat: „{topic_input}”. Wybierz temat z listy w panelu bocznym."
            ],
        )

    defn = TOPIC_CATALOG[topic_id]

    if grade < defn.grades_min or grade > defn.grades_max:
        warnings.append(
            f"Temat „{defn.label_pl}” jest przeznaczony dla klas {defn.grades_min}–{defn.grades_max}, "
            f"a wybrano klasę {grade}."
        )

    from app.ai import topic_blueprints as tb

    grades_map = tb.TOPIC_BLUEPRINTS.get(defn.blueprint_key)
    if grades_map and grade in grades_map:
        bp_exact = grades_map[grade]
        status: BlueprintStatus = "exact"
    else:
        bp = get_blueprint(defn.blueprint_key, grade)
        if bp:
            status = "downgraded"
            if grades_map:
                lower = [g for g in grades_map if g <= grade]
                used = max(lower) if lower else "?"
                warnings.append(
                    f"Brak szablonu dla klasy {grade} — użyto wersji dla klasy {used} "
                    f"(temat: „{defn.label_pl}”)."
                )
        else:
            status = "missing"
            warnings.append(
                f"Brak szablonu programu dla tematu „{defn.label_pl}” w klasie {grade}. "
                f"Zadania mogą być generyczne."
            )

    if defn.capabilities.answer_support == "none":
        warnings.append(
            f"Klucz odpowiedzi dla tematu „{defn.label_pl}” ma ograniczone wsparcie — "
            f"część odpowiedzi może wymagać ręcznej weryfikacji."
        )
    elif defn.capabilities.answer_support == "partial":
        warnings.append(
            f"Klucz odpowiedzi dla tematu „{defn.label_pl}” obsługuje tylko wybrane formaty zadań."
        )

    return ResolvedTopic(
        topic_id=topic_id,
        label_pl=defn.label_pl,
        blueprint_key=defn.blueprint_key,
        grade=grade,
        blueprint_status=status,
        capabilities=defn.capabilities,
        warnings=warnings,
    )


def visual_family_for_topic(topic_input: str) -> Optional[str]:
    """Rodzina ilustracji dla topic_id / label (do images.py)."""
    resolved = resolve_topic(topic_input, grade=2)
    if resolved.capabilities.skip_images:
        return None
    return resolved.capabilities.visual_family


def should_skip_images(topic_input: str) -> bool:
    resolved = resolve_topic(topic_input, grade=2)
    return resolved.capabilities.skip_images


def upper_grades_mvp_caption_pl(grade: int) -> str | None:
    """Komunikat UI: klasy 4–8 to wąski zakres rachunkowy (Faza 0)."""
    if grade >= 4:
        return (
            "Klasy 4–8 (MVP): głównie ćwiczenia rachunkowe — dodawanie, odejmowanie, "
            "mnożenie, dzielenie, ułamki, równania z okienkiem ☐. "
            "To nie jest pełne pokrycie podstawy programowej dla tych klas."
        )
    return None


def answer_key_expectation_pl(topic_input: str, grade: int) -> str | None:
    """Krótka informacja przy włączeniu strony odpowiedzi (Faza 0)."""
    support = resolve_topic(topic_input, grade).capabilities.answer_support
    if support == "full":
        return None
    if support == "partial":
        return (
            "Klucz częściowy — automatycznie tylko wybrane formaty (np. działania, "
            "ułamki o tym samym mianowniku). Reszta: ręczna weryfikacja."
        )
    return (
        "Brak automatycznego klucza dla tego tematu — strona odpowiedzi wymaga "
        "ręcznej weryfikacji (np. zadania tekstowe, pieniądze, czas)."
    )
