from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.context.examples import CANONICAL_EXAMPLES
from app.services import llm_service

WELL_FORMED_MD = CANONICAL_EXAMPLES[0].estimation_markdown

VALID_BODY = {
    "description": "We need a small CRM with auth, contacts and roles. MVP six weeks.",
    "project_type": "web_saas",
    "detail_level": "medium",
    "output_format": "narrative",
}


def _fake_response(*, estimation: str = WELL_FORMED_MD, finish_reason: str = "stop") -> dict:
    return {
        "estimation": estimation,
        "model": "gpt-4o-mini",
        "provider": "openai",
        "finish_reason": finish_reason,
        "usage": {"input_tokens": 1234, "output_tokens": 567, "total_tokens": 1801},
        "latency_ms": 12,
        "cost_usd": 0.001234,
        "cache_hit": False,
    }


@pytest.fixture
def call_log(monkeypatch: pytest.MonkeyPatch) -> Iterator[list[dict]]:
    """Replace the LLM seam with a recording fake. Returns the list of calls."""
    calls: list[dict] = []

    def fake(
        *,
        system_prompt: str,
        user_message: str,
        model_override: str | None,
        max_tokens: int,
        thinking_budget: int | None,
    ) -> dict:
        calls.append(
            {
                "system_prompt": system_prompt,
                "user_message": user_message,
                "model_override": model_override,
                "max_tokens": max_tokens,
                "thinking_budget": thinking_budget,
            }
        )
        finish_reason = "length" if max_tokens <= 200 else "stop"
        return _fake_response(finish_reason=finish_reason)

    monkeypatch.setattr(llm_service, "_invoke_llm", fake)
    yield calls


def test_valid_request_returns_text_and_prompt_version(
    client: TestClient, call_log: list[dict]
) -> None:
    response = client.post("/api/v1/estimate", json=VALID_BODY)
    assert response.status_code == 200
    body = response.json()
    assert body == {"text": WELL_FORMED_MD, "prompt_version": "v1"}
    assert len(call_log) == 1
    assert "phases_table" not in call_log[0]["system_prompt"]  # narrative path
    assert "<project_description>" in call_log[0]["user_message"]


def test_short_description_returns_422(client: TestClient) -> None:
    payload = {
        **VALID_BODY,
        "description": "too short",
    }
    response = client.post("/api/v1/estimate", json=payload)
    assert response.status_code == 422


def test_unknown_enum_returns_422(client: TestClient) -> None:
    payload = {**VALID_BODY, "project_type": "not_a_type"}
    response = client.post("/api/v1/estimate", json=payload)
    assert response.status_code == 422


def test_llm_error_returns_500(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(**_kwargs: object) -> dict:
        raise RuntimeError("provider down")

    monkeypatch.setattr(llm_service, "_invoke_llm", boom)
    response = client.post("/api/v1/estimate", json=VALID_BODY)
    assert response.status_code == 500
    assert "temporarily unavailable" in response.json()["detail"].lower()
