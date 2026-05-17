from unittest.mock import patch, MagicMock

import pytest

from app.cache.ollama_vectorizer import OllamaTextVectorizer


def test_ollama_vectorizer_embed() -> None:
    fake_response = MagicMock()
    fake_response.json.return_value = {"embeddings": [[0.1, 0.2, 0.3]]}
    fake_response.raise_for_status = MagicMock()

    with patch("app.cache.ollama_vectorizer.httpx.post", return_value=fake_response) as mock_post:
        vectorizer = OllamaTextVectorizer(model="nomic-embed-text", base_url="http://localhost:11434")
        result = vectorizer.embed("test text")

    assert result == [0.1, 0.2, 0.3]
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["json"]["model"] == "nomic-embed-text"
    assert call_kwargs["json"]["input"] == "test text"


def test_ollama_vectorizer_embed_many() -> None:
    fake_response = MagicMock()
    fake_response.json.return_value = {"embeddings": [[0.1, 0.2], [0.3, 0.4]]}
    fake_response.raise_for_status = MagicMock()

    with patch("app.cache.ollama_vectorizer.httpx.post", return_value=fake_response) as mock_post:
        vectorizer = OllamaTextVectorizer(model="nomic-embed-text", base_url="http://localhost:11434")
        result = vectorizer.embed_many(["text one", "text two"])

    assert result == [[0.1, 0.2], [0.3, 0.4]]
    assert len(result) == 2


def test_ollama_vectorizer_http_error() -> None:
    import httpx

    with patch("app.cache.ollama_vectorizer.httpx.post", side_effect=httpx.ConnectError("connection refused")):
        vectorizer = OllamaTextVectorizer(model="nomic-embed-text", base_url="http://localhost:11434")
        with pytest.raises(RuntimeError, match="Ollama embedding request failed"):
            vectorizer.embed("test text")


def test_ollama_vectorizer_empty_embeddings() -> None:
    fake_response = MagicMock()
    fake_response.json.return_value = {"embeddings": []}
    fake_response.raise_for_status = MagicMock()

    with patch("app.cache.ollama_vectorizer.httpx.post", return_value=fake_response):
        vectorizer = OllamaTextVectorizer(model="nomic-embed-text", base_url="http://localhost:11434")
        with pytest.raises(RuntimeError, match="Ollama returned no embeddings"):
            vectorizer.embed("test text")
