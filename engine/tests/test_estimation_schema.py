import pytest
from pydantic import ValidationError

from app.schemas.estimation import EstimationResult


def test_estimation_result_accepts_matching_totals() -> None:
    result = EstimationResult(
        summary="A bounded CRM MVP.",
        total_duration_weeks=3,
        total_cost_eur=12000,
        confidence_pct=75,
        phases=[
            {
                "name": "Discovery",
                "duration_weeks": 1,
                "cost_eur": 2000,
                "confidence_pct": 80,
                "assumptions": ["Scope is confirmed."],
            },
            {
                "name": "Build",
                "duration_weeks": 2,
                "cost_eur": 10000,
                "confidence_pct": 70,
                "assumptions": ["No complex integrations."],
            },
        ],
    )
    assert result.total_cost_eur == 12000


def test_total_cost_mismatch_is_rejected() -> None:
    with pytest.raises(ValidationError):
        EstimationResult(
            summary="A bounded CRM MVP.",
            total_duration_weeks=3,
            total_cost_eur=10000,
            confidence_pct=75,
            phases=[
                {
                    "name": "Discovery",
                    "duration_weeks": 1,
                    "cost_eur": 2000,
                    "confidence_pct": 80,
                    "assumptions": ["Scope is confirmed."],
                },
                {
                    "name": "Build",
                    "duration_weeks": 2,
                    "cost_eur": 10000,
                    "confidence_pct": 70,
                    "assumptions": ["No complex integrations."],
                },
            ],
        )
