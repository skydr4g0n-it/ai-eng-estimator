from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

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


class EstimationResponse(BaseModel):
    """Minimal synchronous response: rendered estimation text and prompt pack id."""

    text: str = Field(..., min_length=1, description="Generated estimation content")
    prompt_version: str = Field(
        ...,
        min_length=1,
        description="Prompt template pack version (e.g. v1 for estimation/v1/)",
    )


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
