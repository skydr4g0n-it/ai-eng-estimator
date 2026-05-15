"""Output guardrails for structured estimation results."""

from __future__ import annotations

import structlog

from app.guardrails.input import GuardrailViolation
from app.schemas.estimation import EstimationResult

log = structlog.get_logger()


def validate_output(result: EstimationResult) -> None:
    for phase in result.phases:
        if phase.confidence_pct < 20:
            log.warning("output_guardrail_rejected", reason_code="low_phase_confidence")
            raise GuardrailViolation(
                "low_phase_confidence",
                "The estimate could not be validated with sufficient confidence.",
            )
    if result.confidence_pct < 20:
        log.warning("output_guardrail_rejected", reason_code="low_result_confidence")
        raise GuardrailViolation(
            "low_result_confidence",
            "The estimate could not be validated with sufficient confidence.",
        )
