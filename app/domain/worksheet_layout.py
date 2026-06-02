"""Single authority for final worksheet PDF layout (P1.5)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.ai.layout_generator import generate_layout
from app.domain.profile_catalog import ResolvedProfile
from app.domain.profile_pedagogy import layout_overrides_for_pedagogy, low_stimuli_boost_for_profile

PDF_PRINT_DEFAULTS: dict[str, Any] = {
    "title_font_size": 22,
    "metadata_font_size": 11,
    "section_font_size": 16,
    "task_font_size": 14,
    "answer_font_size": 14,
    "margin": 50,
    "title_spacing": 28,
    "metadata_spacing": 22,
    "section_spacing": 20,
    "task_spacing": 10,
    "line_spacing": 18,
    "workspace_lines": 3,
    "workspace_line_gap": 18,
    "text_color": "#000000",
    "muted_color": "#9e9e9e",
    "background_color": "#FFFFFF",
    "header_image_width_pt": 160,
    "header_image_height_pt": 90,
    "task_image_aspect": 100 / 480,
}

LOW_STIMULI_PDF_BOOST: dict[str, Any] = {
    "title_font_size": 24,
    "metadata_font_size": 12,
    "section_font_size": 18,
    "task_font_size": 16,
    "answer_font_size": 16,
    "margin": 60,
    "title_spacing": 32,
    "metadata_spacing": 26,
    "section_spacing": 24,
    "task_spacing": 14,
    "line_spacing": 22,
    "workspace_lines": 4,
    "workspace_line_gap": 22,
    "background_color": "#fafafa",
}

_TYPOGRAPHY_KEYS = frozenset(
    {
        "title_font_size",
        "metadata_font_size",
        "section_font_size",
        "task_font_size",
        "answer_font_size",
        "margin",
        "title_spacing",
        "metadata_spacing",
        "section_spacing",
        "task_spacing",
        "line_spacing",
        "workspace_lines",
        "workspace_line_gap",
        "text_color",
        "muted_color",
        "background_color",
    }
)


@dataclass(frozen=True)
class ResolvedWorksheetLayout:
    """Final layout consumed by PDF renderer — no profile re-decisions in PDF."""

    title_font_size: int
    metadata_font_size: int
    section_font_size: int
    task_font_size: int
    answer_font_size: int
    margin: int
    title_spacing: int
    metadata_spacing: int
    section_spacing: int
    task_spacing: int
    line_spacing: int
    workspace_lines: int
    workspace_line_gap: int
    text_color: str
    muted_color: str
    background_color: str
    header_image_width_pt: float
    header_image_height_pt: float
    task_image_aspect: float
    is_low_stimuli: bool
    source: str

    def to_pdf_dict(self) -> dict[str, Any]:
        return {
            "title_font_size": self.title_font_size,
            "metadata_font_size": self.metadata_font_size,
            "section_font_size": self.section_font_size,
            "task_font_size": self.task_font_size,
            "answer_font_size": self.answer_font_size,
            "margin": self.margin,
            "title_spacing": self.title_spacing,
            "metadata_spacing": self.metadata_spacing,
            "section_spacing": self.section_spacing,
            "task_spacing": self.task_spacing,
            "line_spacing": self.line_spacing,
            "workspace_lines": self.workspace_lines,
            "workspace_line_gap": self.workspace_line_gap,
            "text_color": self.text_color,
            "muted_color": self.muted_color,
            "background_color": self.background_color,
            "header_image_width_pt": self.header_image_width_pt,
            "header_image_height_pt": self.header_image_height_pt,
            "task_image_aspect": self.task_image_aspect,
        }

    @classmethod
    def from_mapping(
        cls, values: dict[str, Any], *, is_low_stimuli: bool, source: str
    ) -> ResolvedWorksheetLayout:
        return cls(
            title_font_size=int(values["title_font_size"]),
            metadata_font_size=int(values["metadata_font_size"]),
            section_font_size=int(values["section_font_size"]),
            task_font_size=int(values["task_font_size"]),
            answer_font_size=int(values.get("answer_font_size", values["task_font_size"])),
            margin=int(values["margin"]),
            title_spacing=int(values["title_spacing"]),
            metadata_spacing=int(values["metadata_spacing"]),
            section_spacing=int(values["section_spacing"]),
            task_spacing=int(values["task_spacing"]),
            line_spacing=int(values["line_spacing"]),
            workspace_lines=int(values.get("workspace_lines", 0)),
            workspace_line_gap=int(values.get("workspace_line_gap", 18)),
            text_color=str(values["text_color"]),
            muted_color=str(values.get("muted_color", "#9e9e9e")),
            background_color=str(values["background_color"]),
            header_image_width_pt=float(values.get("header_image_width_pt", 160)),
            header_image_height_pt=float(values.get("header_image_height_pt", 90)),
            task_image_aspect=float(values.get("task_image_aspect", 100 / 480)),
            is_low_stimuli=is_low_stimuli,
            source=source,
        )


def resolve_worksheet_layout(
    resolved_profile: ResolvedProfile,
    grade: int,
    number_of_tasks: int,
    *,
    include_workspace: bool = True,
) -> ResolvedWorksheetLayout:
    values = dict(PDF_PRINT_DEFAULTS)
    source = "pdf_defaults"

    profile_layout = generate_layout(
        resolved_profile.profile_id,
        str(grade),
        number_of_tasks,
    )
    for key in _TYPOGRAPHY_KEYS:
        if key in profile_layout:
            values[key] = profile_layout[key]
    source = "profile_layout"

    pedagogy_layout = layout_overrides_for_pedagogy(resolved_profile.profile_id)
    for key in _TYPOGRAPHY_KEYS:
        if key in pedagogy_layout:
            values[key] = pedagogy_layout[key]
    if pedagogy_layout:
        source = "profile_pedagogy"

    if resolved_profile.is_low_stimuli:
        values.update(low_stimuli_boost_for_profile(resolved_profile.profile_id))
        source = "low_stimuli_boost"

    values = _apply_grade_readability(values, grade)

    if not include_workspace:
        values["workspace_lines"] = 0

    values["answer_font_size"] = values.get("answer_font_size", values["task_font_size"])

    return ResolvedWorksheetLayout.from_mapping(
        values,
        is_low_stimuli=resolved_profile.is_low_stimuli,
        source=source,
    )


def _apply_grade_readability(values: dict[str, Any], grade: int) -> dict[str, Any]:
    if grade <= 3:
        values["task_font_size"] = max(int(values["task_font_size"]), 12)
        values["margin"] = max(int(values["margin"]), 55)
    return values
