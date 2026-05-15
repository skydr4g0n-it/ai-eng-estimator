"""Input guardrails for estimation requests."""

from __future__ import annotations

import re

import structlog

from app.schemas.estimation import EstimationRequest

log = structlog.get_logger()

PROMPT_INJECTION_PATTERNS = [
    re.compile(r"\bignore (all )?(previous|prior|above) instructions\b", re.I),
    re.compile(r"\bdisregard (all )?(previous|prior|above) instructions\b", re.I),
    re.compile(r"\bsystem prompt\b", re.I),
]
PII_PATTERNS = [
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    re.compile(r"\b(?:\+?\d[\d .-]{7,}\d)\b"),
    re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b", re.I),
]


class GuardrailViolation(ValueError):
    """Raised when input or output violates estimator safety rules."""

    def __init__(self, reason_code: str, safe_message: str):
        super().__init__(safe_message)
        self.reason_code = reason_code
        self.safe_message = safe_message


def _reference_text(request: EstimationRequest) -> str:
    if not request.reference_projects:
        return ""
    parts: list[str] = []
    for project in request.reference_projects:
        parts.extend(
            [
                project.name,
                project.project_type,
                project.short_description,
                project.comparable_scope,
                project.lessons or "",
            ],
        )
    return "\n".join(parts)


def validate_input(request: EstimationRequest) -> None:
    content = f"{request.description}\n{_reference_text(request)}"
    for pattern in PROMPT_INJECTION_PATTERNS:
        if pattern.search(content):
            log.warning("input_guardrail_rejected", reason_code="prompt_injection")
            raise GuardrailViolation(
                "prompt_injection",
                "Request contains instruction-like text that cannot be estimated safely.",
            )
    for pattern in PII_PATTERNS:
        if pattern.search(content):
            log.warning("input_guardrail_rejected", reason_code="pii")
            raise GuardrailViolation(
                "pii",
                "Request contains personal or sensitive identifiers. Remove them and retry.",
            )
