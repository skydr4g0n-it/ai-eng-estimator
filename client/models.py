"""Client-side mirrors of engine ``EstimationRequest`` (same field names and enum strings)."""

from enum import StrEnum

from pydantic import BaseModel, Field


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
    description: str = Field(..., min_length=20, max_length=2000)
    project_type: ProjectType
    detail_level: DetailLevel
    output_format: OutputFormat
