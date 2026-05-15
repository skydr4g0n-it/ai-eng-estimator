from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

# --- Streaming / legacy prompt-building (Session 2–3) -------------------------

PreprocessingMode = Literal["none", "inline_cleaning", "two_phase"]
ExampleFormat = Literal["markdown", "json", "narrative"]


class StreamEstimationRequest(BaseModel):
    """Streaming endpoint request — transcription only; knobs are not exposed."""

    transcription: str = Field(..., min_length=50, description="Meeting transcription text")
    model: str | None = Field(default=None, description="Override the default model")
    max_tokens: int = Field(default=4000, gt=0, le=16000)


# --- Synchronous form contract (typed description + enums) --------------------


class ProjectType(StrEnum):
    mobile_app = "mobile_app"
    web_saas = "web_saas"
    internal_tool = "internal_tool"
    data_pipeline = "data_pipeline"


class DetailLevel(StrEnum):
    summary = "summary"
    medium = "medium"
    detailed = "detailed"


class OutputFormat(StrEnum):
    phases_table = "phases_table"
    line_items = "line_items"
    narrative = "narrative"


class EstimationRequest(BaseModel):
    """JSON body for ``POST /api/v1/estimate`` (synchronous form-driven path)."""

    description: str = Field(
        ...,
        min_length=20,
        max_length=2000,
        description="Project description for estimation",
    )
    project_type: ProjectType
    detail_level: DetailLevel
    output_format: OutputFormat
    reference_projects: list["ReferenceProject"] | None = Field(
        default=None,
        max_length=5,
        description="Comparable projects used only as bounded prompt context",
    )


class ReferenceProject(BaseModel):
    """Bounded comparable-project context for the synchronous estimator."""

    name: str = Field(..., min_length=1, max_length=80)
    project_type: str = Field(..., min_length=1, max_length=80)
    short_description: str = Field(..., min_length=10, max_length=400)
    comparable_scope: str = Field(..., min_length=1, max_length=300)
    total_hours: int | None = Field(default=None, ge=1, le=100_000)
    total_cost_eur: int | None = Field(default=None, ge=0, le=10_000_000)
    lessons: str | None = Field(default=None, max_length=300)


class EstimationResponse(BaseModel):
    """Synchronous response: validated estimation data and prompt pack id."""

    result: "EstimationResult"
    prompt_version: str = Field(
        ...,
        min_length=1,
        description="Prompt template pack version (e.g. v1 for estimation/v1/)",
    )


class Phase(BaseModel):
    """One phase of the structured estimate."""

    name: str = Field(..., min_length=1, max_length=120)
    duration_weeks: int = Field(..., ge=1, le=52)
    cost_eur: int = Field(..., ge=0)
    confidence_pct: int = Field(..., ge=0, le=100)
    assumptions: list[str] = Field(default_factory=list, max_length=12)


class EstimationResult(BaseModel):
    """Structured output expected from the synchronous LLM path."""

    summary: str = Field(..., min_length=1, max_length=2000)
    total_duration_weeks: int = Field(..., ge=1)
    total_cost_eur: int = Field(..., ge=0)
    confidence_pct: int = Field(..., ge=0, le=100)
    phases: list[Phase] = Field(..., min_length=1)

    @model_validator(mode="after")
    def total_must_match_sum_of_phases(self) -> "EstimationResult":
        phase_weeks = sum(phase.duration_weeks for phase in self.phases)
        if abs(phase_weeks - self.total_duration_weeks) > 1:
            raise ValueError(
                "total_duration_weeks must match summed phase duration within 1 week",
            )

        phase_cost = sum(phase.cost_eur for phase in self.phases)
        if self.total_cost_eur == 0:
            if phase_cost != 0:
                raise ValueError("total_cost_eur is zero but phase costs are non-zero")
            return self

        relative_delta = abs(phase_cost - self.total_cost_eur) / self.total_cost_eur
        if relative_delta > 0.05:
            raise ValueError("total_cost_eur must match summed phase cost within 5%")
        return self


# --- Internal / evaluation (not returned on sync estimate) ------------------


class TokenUsage(BaseModel):
    """Token consumption details from the LLM call(s)."""

    input_tokens: int
    output_tokens: int
    total_tokens: int
    preprocessing_input_tokens: int = 0
    preprocessing_output_tokens: int = 0


class StructureCheck(BaseModel):
    """Level-1 structural evaluation of a generated estimation."""

    has_title: bool
    has_breakdown_table: bool
    has_totals_section: bool
    has_team_section: bool
    has_duration_section: bool
    declared_total_hours: int | None
    sum_row_hours: int | None
    hours_match: bool | None
    declared_total_cost: float | None
    sum_row_cost: float | None
    cost_match: bool | None
    finish_reason_ok: bool
    score: float
    issues: list[str]
