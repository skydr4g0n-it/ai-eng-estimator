import pytest

from app.schemas import estimation as engine_models
from models import DetailLevel, EstimationRequest, OutputFormat, ProjectType


def test_client_enums_match_engine_schema() -> None:
    assert [item.value for item in ProjectType] == [
        item.value for item in engine_models.ProjectType
    ]
    assert [item.value for item in DetailLevel] == [
        item.value for item in engine_models.DetailLevel
    ]
    assert [item.value for item in OutputFormat] == [
        item.value for item in engine_models.OutputFormat
    ]


def test_client_request_accepts_streamlit_form_payload() -> None:
    request = EstimationRequest(
        description="Build a scheduling dashboard for field technicians.",
        project_type=ProjectType.web_saas,
        detail_level=DetailLevel.medium,
        output_format=OutputFormat.phases_table,
    )

    assert request.model_dump(mode="json") == {
        "description": "Build a scheduling dashboard for field technicians.",
        "project_type": "web_saas",
        "detail_level": "medium",
        "output_format": "phases_table",
    }


def test_client_request_uses_engine_validation_constraints() -> None:
    with pytest.raises(ValueError):
        EstimationRequest(
            description="too short",
            project_type=ProjectType.web_saas,
            detail_level=DetailLevel.medium,
            output_format=OutputFormat.phases_table,
        )
