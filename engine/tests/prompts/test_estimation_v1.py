"""Tests for Jinja estimation prompt rendering."""

from app.prompts.loader import render_estimation_prompt
from app.schemas.estimation import (
    DetailLevel,
    EstimationRequest,
    OutputFormat,
    ProjectType,
    ReferenceProject,
)


def _req(
    *,
    description: str = "Default description at least twenty chars.",
    project_type: ProjectType = ProjectType.web_saas,
    detail_level: DetailLevel = DetailLevel.medium,
    output_format: OutputFormat = OutputFormat.narrative,
    reference_projects: list[ReferenceProject] | None = None,
) -> EstimationRequest:
    return EstimationRequest(
        description=description,
        project_type=project_type,
        detail_level=detail_level,
        output_format=output_format,
        reference_projects=reference_projects,
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
    assert "EstimationResult" in system_table
    assert "EstimationResult" in system_narrative


def test_detailed_includes_assumptions_per_phase_summary_does_not() -> None:
    detailed = _req(detail_level=DetailLevel.detailed)
    summary = _req(detail_level=DetailLevel.summary)
    sys_d, _ = render_estimation_prompt(detailed)
    sys_s, _ = render_estimation_prompt(summary)
    assert "assumptions per phase" in sys_d
    assert "assumptions per phase" not in sys_s


def test_v2_renders_sibling_prompt_pack_with_tone_variation() -> None:
    system, user = render_estimation_prompt(_req(), version="v2")
    assert "crisp, executive tone" in system
    assert "<project_description>" in user


def test_reference_projects_render_when_present() -> None:
    refs = [
        ReferenceProject(
            name="CRM Alpha",
            project_type="web_saas",
            short_description="Comparable CRM with auth and contacts.",
            comparable_scope="Small team MVP with role-based access.",
            total_hours=180,
            total_cost_eur=12000,
            lessons="Keep reporting out of MVP.",
        ),
        ReferenceProject(
            name="CRM Beta",
            project_type="internal_tool",
            short_description="Internal contact manager with imports.",
            comparable_scope="CSV import and search were the main effort.",
        ),
    ]
    _, user = render_estimation_prompt(_req(reference_projects=refs))
    assert "<reference_projects>" in user
    assert "CRM Alpha" in user
    assert "CRM Beta" in user


def test_reference_projects_omitted_when_absent() -> None:
    _, user = render_estimation_prompt(_req())
    assert "<reference_projects>" not in user


def test_prompt_render_logs_hash_without_prompt_content(monkeypatch) -> None:
    events: list[dict] = []

    class _Logger:
        def info(self, event: str, **kwargs) -> None:
            events.append({"event": event, **kwargs})

    import app.prompts.loader as loader

    monkeypatch.setattr(loader, "log", _Logger())
    desc = "Description that must not appear in prompt render logs."
    render_estimation_prompt(_req(description=desc))
    event = events[0]
    assert event["event"] == "prompt_rendered"
    assert event["prompt_version"] == "v1"
    assert len(event["content_sha256"]) == 64
    assert desc not in str(event)
