"""Ollama-backed text vectorizer for RedisVL semantic cache."""

from __future__ import annotations

from typing import Any, Callable

import httpx
import structlog
from pydantic import Field

try:
    from redisvl.utils.vectorize import BaseVectorizer as _BaseVectorizer

    _BASE = _BaseVectorizer
except ImportError:
    _BASE = object

log = structlog.get_logger()


class OllamaTextVectorizer(_BASE):
    """Generates text embeddings by calling Ollama's ``/api/embed`` endpoint."""

    base_url: str = Field(default="http://localhost:11434")
    dims: int = 768

    def __init__(self, model: str, base_url: str = "http://localhost:11434") -> None:
        if _BASE is object:
            self.model = model
            self.base_url = base_url.rstrip("/")
            self.dtype = "float32"
            self.dims = 768
            self.cache = None
        else:
            super().__init__(model=model, base_url=base_url.rstrip("/"), dims=768)

    def embed(
        self,
        content: str | None = None,
        text: str | None = None,
        preprocess: Callable | None = None,
        as_buffer: bool = False,
        skip_cache: bool = False,
        **kwargs: Any,
    ) -> list[float] | bytes:
        content = content or text
        if not content:
            raise ValueError("No content provided to embed.")
        if preprocess is not None:
            content = preprocess(content)
        if self.cache is not None and not skip_cache:
            try:
                cache_result = self.cache.get(
                    content=self._serialize_for_cache(content), model_name=self.model
                )
                if cache_result:
                    return self._process_embedding(cache_result, as_buffer)
            except Exception:
                log.warning("ollama_vectorizer_cache_get_failed")

        embedding = self._call_ollama_embed(content)
        if self.cache is not None and not skip_cache:
            try:
                self.cache.set(
                    content=self._serialize_for_cache(content),
                    model_name=self.model,
                    embedding=embedding,
                )
            except Exception:
                log.warning("ollama_vectorizer_cache_set_failed")
        return self._process_embedding(embedding, as_buffer)

    def _call_ollama_embed(self, text: str) -> list[float]:
        url = f"{self.base_url}/api/embed"
        payload = {"model": self.model, "input": text}
        try:
            response = httpx.post(url, json=payload, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            embeddings = data.get("embeddings", [])
            if embeddings:
                return embeddings[0]
            raise RuntimeError(f"Ollama returned no embeddings for model={self.model}")
        except httpx.HTTPError as exc:
            log.error("ollama_embedding_failed", url=url, error=str(exc))
            raise RuntimeError(f"Ollama embedding request failed: {exc}") from exc

    def embed_many(
        self,
        contents: list[str] | None = None,
        texts: list[str] | None = None,
        preprocess: Callable | None = None,
        as_buffer: bool = False,
        skip_cache: bool = False,
        batch_size: int = 1000,
        **kwargs: Any,
    ) -> list[list[float]] | list[bytes]:
        items = contents or texts or []
        if not items:
            raise ValueError("No content provided to embed.")
        if preprocess is not None:
            items = [preprocess(item) for item in items]

        url = f"{self.base_url}/api/embed"
        payload = {"model": self.model, "input": items}
        try:
            response = httpx.post(url, json=payload, timeout=60.0)
            response.raise_for_status()
            data = response.json()
            embeddings = data.get("embeddings", [])
            if len(embeddings) != len(items):
                raise RuntimeError(
                    f"Ollama returned {len(embeddings)} embeddings for {len(items)} texts"
                )
            if as_buffer:
                import struct

                return [struct.pack(f"{len(e)}f", *e) for e in embeddings]
            return embeddings
        except httpx.HTTPError as exc:
            log.error("ollama_embedding_failed", url=url, error=str(exc))
            raise RuntimeError(f"Ollama embedding request failed: {exc}") from exc

    def _process_embedding(self, embedding: list[float], as_buffer: bool) -> list[float] | bytes:
        if as_buffer:
            import struct

            return struct.pack(f"{len(embedding)}f", *embedding)
        return embedding

    def _serialize_for_cache(self, content: str) -> str:
        return content

    @property
    def type(self) -> str:
        return "ollama"
