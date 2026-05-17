import os

os.environ.setdefault("OPENAI_API_KEY", "sk-test-openai")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-anthropic")
os.environ.setdefault("GOOGLE_API_KEY", "sk-test-google")
os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")
os.environ.setdefault("OLLAMA_MODEL", "qwen3.5:9b")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Provide a FastAPI test client configured with the application."""
    return TestClient(app)
