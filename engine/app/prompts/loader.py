"""Load and render estimation prompts from ``app/prompts/estimation/<version>/``."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from app.schemas.estimation import EstimationRequest

_PROMPTS_ROOT = Path(__file__).resolve().parent


def render_estimation_prompt(
    request: EstimationRequest,
    version: str = "v1",
) -> tuple[str, str]:
    """Render ``(system, user)`` strings for the LLM from the versioned template pack."""
    env = Environment(
        loader=FileSystemLoader(_PROMPTS_ROOT),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    prefix = f"estimation/{version}/"
    ctx = request.model_dump()
    system = env.get_template(f"{prefix}system.j2").render(**ctx)
    user = env.get_template(f"{prefix}user.j2").render(**ctx)
    return system, user
