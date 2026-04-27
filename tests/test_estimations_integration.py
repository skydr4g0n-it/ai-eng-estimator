"""HTTP integration tests for the estimation endpoint (router + app + request body)."""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

REPO_ROOT = Path(__file__).resolve().parent.parent
MEETING_TRANSCRIPT_PATH = REPO_ROOT / "transcripts" / "meeting_transcription.txt"

client = TestClient(app)

# `skipif` debe aceptar la clave (1) desde variables de entorno, como inyecta
# docker compose, y (2) solo desde un `.env` en disco, como al ejecutar
# `pytest` en local: en ese caso `os.environ` a menudo no tiene la clave pero
# `pydantic-settings` si carga el archivo. En contenedor, no se copia `.env` a
# la imagen; ahi la clave entra por entorno. Comprobamos `os` y `settings` para
# cubrir ambos casos.


def _load_meeting_transcription() -> str:
    return MEETING_TRANSCRIPT_PATH.read_text(encoding="utf-8")


def _uses_openai() -> bool:
    provider = os.environ.get("LLM_PROVIDER") or (settings.llm_provider or "openai")
    return str(provider).lower() == "openai"


def _openai_key_configured() -> bool:
    if (os.environ.get("OPENAI_API_KEY") or "").strip():
        return True
    return bool((settings.openai_api_key or "").strip())


@pytest.mark.skipif(
    not _uses_openai(),
    reason="Requiere LLM_PROVIDER=openai para probar el proveedor OpenAI.",
)
@pytest.mark.skipif(
    not _openai_key_configured(),
    reason="Requiere OPENAI_API_KEY (variable de entorno, docker compose, o .env visto por pydantic-settings).",
)
def test_post_estimate_with_meeting_transcription_file() -> None:
    text = _load_meeting_transcription()
    assert "HubSpot" in text
    assert "landing page" in text

    response = client.post(
        "/api/v1/estimate",
        json={"transcription": text},
    )

    assert response.status_code == 200, response.text
    body = response.json()

    assert body["model"] == settings.llm_model
    assert body["provider"] == "openai"
    assert "generated_at" in body

    estimation = body["estimation"]
    assert isinstance(estimation, str) and len(estimation) > 80

    # La estimacion responde en espanol al alcance del transcript; evitamos
    # aserciones fijas al texto del modelo, pero verificamos que haya contexto
    # del requerimiento.
    est_lower = estimation.lower()
    assert any(
        phrase in est_lower
        for phrase in (
            "hubspot",
            "landing",
            "blog",
            "crm",
            "figma",
            "wysiwyg",
        )
    ), "La estimacion deberia reflejar terminos clave del requerimiento."

    assert (
        "hora" in est_lower
        or "seman" in est_lower
        or "día" in est_lower
        or "dias" in est_lower
    ), "La estimacion deberia mencionar horas, semanas o plazos de calendario."
