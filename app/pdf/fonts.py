"""Polish-capable PDF font resolution and registration (P0.4)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from reportlab.pdfbase import pdfmetrics  # pyright: ignore[reportMissingModuleSource]
from reportlab.pdfbase.ttfonts import TTFont  # pyright: ignore[reportMissingModuleSource]

FONT_LOGICAL_NAME = "DejaVuSans"
BUNDLED_RELATIVE = Path("assets/fonts/DejaVuSans.ttf")

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class FontRegistration:
    """Outcome of registering a Polish-capable TTF for ReportLab."""

    ok: bool
    regular_name: str
    bold_name: str
    source: str  # bundled | pip | none
    path: Path | None
    warning: str | None = None


def repo_root() -> Path:
    return _REPO_ROOT


def bundled_font_path() -> Path:
    return _REPO_ROOT / BUNDLED_RELATIVE


def resolve_polish_font_path() -> tuple[Path | None, str]:
    """Locate DejaVu Sans TTF in repo assets. Returns (path, source_label)."""
    bundled = bundled_font_path()
    if bundled.is_file():
        return bundled, "bundled"
    return None, "none"


def register_polish_font() -> FontRegistration:
    """
    Register DejaVu for ReportLab. Bold uses the same face (emulated in generator).
    On failure, returns Helvetica names and a teacher-facing warning string.
    """
    base_font = "Helvetica"
    bold_font = "Helvetica-Bold"
    font_path, source = resolve_polish_font_path()

    if font_path is None:
        warning = (
            "Brak czcionki DejaVu Sans — PDF może nie wyświetlać polskich znaków "
            "(ą, ę, ó, ł, ś, ź, ż, ć, ń). Zainstaluj zależności projektu "
            "(assets/fonts/DejaVuSans.ttf w repozytorium)."
        )
        return FontRegistration(
            ok=False,
            regular_name=base_font,
            bold_name=bold_font,
            source=source,
            path=None,
            warning=warning,
        )

    try:
        if FONT_LOGICAL_NAME not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(FONT_LOGICAL_NAME, str(font_path)))
        return FontRegistration(
            ok=True,
            regular_name=FONT_LOGICAL_NAME,
            bold_name=FONT_LOGICAL_NAME,
            source=source,
            path=font_path,
            warning=None,
        )
    except Exception as exc:
        warning = (
            f"Nie udało się załadować czcionki DejaVu ({font_path}): {exc}. "
            "PDF może nie wyświetlać polskich znaków."
        )
        return FontRegistration(
            ok=False,
            regular_name=base_font,
            bold_name=bold_font,
            source=source,
            path=font_path,
            warning=warning,
        )
