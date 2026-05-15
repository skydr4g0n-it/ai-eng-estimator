from fastapi.testclient import TestClient

from app.dependencies import get_estimation_service
from app.guardrails import GuardrailViolation
from app.main import app
from app.schemas.estimation import EstimationResponse, EstimationResult
from app.services.estimation_service import EstimationOutputInvalid

VALID_BODY = {
    "description": "We need a small CRM with auth, contacts and roles. MVP six weeks.",
    "project_type": "web_saas",
    "detail_level": "medium",
    "output_format": "narrative",
}


def _result() -> EstimationResult:
    return EstimationResult(
        summary="CRM MVP with auth, contacts, and roles.",
        total_duration_weeks=6,
        total_cost_eur=12000,
        confidence_pct=80,
        phases=[
            {
                "name": "Discovery",
                "duration_weeks": 1,
                "cost_eur": 2000,
                "confidence_pct": 80,
                "assumptions": ["Stakeholders are available."],
            },
            {
                "name": "Build",
                "duration_weeks": 5,
                "cost_eur": 10000,
                "confidence_pct": 75,
                "assumptions": ["CRM scope stays within MVP."],
            },
        ],
    )


class _FakeService:
    def __init__(self, exc: Exception | None = None) -> None:
        self.calls: list[dict] = []
        self.exc = exc

    def estimate(self, request, *, prompt_version: str) -> EstimationResponse:
        self.calls.append({"request": request, "prompt_version": prompt_version})
        if self.exc:
            raise self.exc
        return EstimationResponse(result=_result(), prompt_version=prompt_version)


def test_valid_request_returns_result_and_prompt_version(client: TestClient) -> None:
    service = _FakeService()
    app.dependency_overrides[get_estimation_service] = lambda: service
    try:
        response = client.post("/api/v1/estimate", json=VALID_BODY)
    finally:
        app.dependency_overrides.pop(get_estimation_service, None)

    assert response.status_code == 200
    body = response.json()
    assert body["prompt_version"] == "v1"
    assert body["result"]["total_cost_eur"] == 12000
    assert len(service.calls) == 1


def test_v2_prompt_version_is_passed_to_service(client: TestClient) -> None:
    service = _FakeService()
    app.dependency_overrides[get_estimation_service] = lambda: service
    try:
        response = client.post("/api/v1/estimate?prompt_version=v2", json=VALID_BODY)
    finally:
        app.dependency_overrides.pop(get_estimation_service, None)

    assert response.status_code == 200
    assert service.calls[0]["prompt_version"] == "v2"


def test_unsupported_prompt_version_returns_422(client: TestClient) -> None:
    response = client.post("/api/v1/estimate?prompt_version=v999", json=VALID_BODY)
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["prompt_version"] == "v999"
    assert detail["supported_versions"] == ["v1", "v2"]


def test_short_description_returns_422(client: TestClient) -> None:
    response = client.post("/api/v1/estimate", json={**VALID_BODY, "description": "too short"})
    assert response.status_code == 422


def test_unknown_enum_returns_422(client: TestClient) -> None:
    response = client.post("/api/v1/estimate", json={**VALID_BODY, "project_type": "not_a_type"})
    assert response.status_code == 422


def test_guardrail_error_returns_client_error(client: TestClient) -> None:
    service = _FakeService(GuardrailViolation("pii", "Remove sensitive data."))
    app.dependency_overrides[get_estimation_service] = lambda: service
    try:
        response = client.post("/api/v1/estimate", json=VALID_BODY)
    finally:
        app.dependency_overrides.pop(get_estimation_service, None)

    assert response.status_code == 400
    assert response.json()["detail"] == "Remove sensitive data."


def test_invalid_output_returns_safe_error(client: TestClient) -> None:
    service = _FakeService(EstimationOutputInvalid("bad"))
    app.dependency_overrides[get_estimation_service] = lambda: service
    try:
        response = client.post("/api/v1/estimate", json=VALID_BODY)
    finally:
        app.dependency_overrides.pop(get_estimation_service, None)

    assert response.status_code == 502
    assert "valid structured result" in response.json()["detail"]
