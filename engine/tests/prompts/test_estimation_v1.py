"""Tests for Jinja estimation prompt rendering."""

from app.prompts.loader import render_estimation_prompt
from app.schemas.estimation import (
    DetailLevel,
    EstimationRequest,
    OutputFormat,
    ProjectType,
)


def _req(
    *,
    description: str = "Default description at least twenty chars.",
    project_type: ProjectType = ProjectType.web_saas,
    detail_level: DetailLevel = DetailLevel.medium,
    output_format: OutputFormat = OutputFormat.narrative,
) -> EstimationRequest:
    return EstimationRequest(
        description=description,
        project_type=project_type,
        detail_level=detail_level,
        output_format=output_format,
    )


def test_rendered_user_wraps_description_literally() -> None:
    desc = "Custom project description for unit test XYZ123."
    request = _req(description=desc)
    _, user = render_estimation_prompt(request)
    assert "<project_description>" in user
    assert desc in user
    assert "</project_description>" in user


def test_phases_table_vs_narrative_system_keyword() -> None:
    table_req = _req(output_format=OutputFormat.phases_table)
    narrative_req = _req(output_format=OutputFormat.narrative)
    system_table, _ = render_estimation_prompt(table_req)
    system_narrative, _ = render_estimation_prompt(narrative_req)
    assert "phases_table" in system_table
    assert "phases_table" not in system_narrative


def test_detailed_includes_assumptions_per_phase_summary_does_not() -> None:
    detailed = _req(detail_level=DetailLevel.detailed)
    summary = _req(detail_level=DetailLevel.summary)
    sys_d, _ = render_estimation_prompt(detailed)
    sys_s, _ = render_estimation_prompt(summary)
    assert "assumptions per phase" in sys_d
    assert "assumptions per phase" not in sys_s
