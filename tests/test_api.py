from fastapi.testclient import TestClient

from app.main import app
from app.services import llm_service


client = TestClient(app)


def test_health_endpoint_returns_service_status() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_estimate_endpoint_returns_generated_estimation(monkeypatch) -> None:
    async def fake_generate_estimation(transcription: str) -> str:
        assert "landing page" in transcription
        return "## Estimacion: Landing Page\n\n**Total estimado: 96 horas**"

    monkeypatch.setattr(llm_service, "generate_estimation", fake_generate_estimation)

    response = client.post(
        "/api/v1/estimate",
        json={
            "transcription": (
                "El cliente necesita una landing page con formulario, "
                "HubSpot y blog con editor WYSIWYG."
            )
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["estimation"].startswith("## Estimacion")
    assert body["model"]
    assert body["provider"] in {"openai", "anthropic"}
