"""RedisVL-backed semantic cache for validated estimation responses."""

from __future__ import annotations

import hashlib
import json
from functools import reduce
from typing import Any

import structlog

from app.schemas.estimation import EstimationRequest, EstimationResult

log = structlog.get_logger()


class SemanticCacheUnavailable(RuntimeError):
    """Raised when RedisVL or vector setup is unavailable."""


def reference_context_hash(request: EstimationRequest) -> str:
    projects = [project.model_dump(mode="json") for project in request.reference_projects or []]
    payload = json.dumps(projects, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def semantic_bucket(request: EstimationRequest, prompt_version: str) -> dict[str, str]:
    return {
        "prompt_version": prompt_version,
        "project_type": request.project_type.value,
        "detail_level": request.detail_level.value,
        "output_format": request.output_format.value,
        "reference_context": reference_context_hash(request),
    }


def _filter_expression(bucket: dict[str, str]) -> Any:
    from redisvl.query.filter import Tag

    filters = [Tag(name) == value for name, value in bucket.items()]
    return reduce(lambda left, right: left & right, filters)


class SemanticEstimationCache:
    """Thin semantic cache adapter.

    The implementation uses RedisVL when installed and initialized successfully.
    Tests can replace this adapter with a fake; production startup degrades to
    exact-match caching if setup fails.
    """

    def __init__(
        self,
        *,
        redis_url: str,
        embedding_model: str,
        similarity_threshold: float,
        ttl: int,
        log_only: bool,
        ollama_base_url: str = "http://localhost:11434",
    ) -> None:
        self.redis_url = redis_url
        self.embedding_model = embedding_model
        self.similarity_threshold = similarity_threshold
        self.distance_threshold = 1 - similarity_threshold
        self.ttl = ttl
        self.log_only = log_only
        self.ollama_base_url = ollama_base_url
        self._cache: Any | None = None
        self._init_redisvl()

    def _init_redisvl(self) -> None:
        try:
            from redisvl.extensions.cache.llm.semantic import SemanticCache
        except ImportError as exc:
            raise SemanticCacheUnavailable(
                "RedisVL semantic cache dependencies unavailable"
            ) from exc

        from app.cache.ollama_vectorizer import OllamaTextVectorizer

        try:
            vectorizer = OllamaTextVectorizer(
                model=self.embedding_model,
                base_url=self.ollama_base_url,
            )
            self._cache = SemanticCache(
                name="estimation_semantic_cache",
                redis_url=self.redis_url,
                distance_threshold=self.distance_threshold,
                ttl=self.ttl,
                vectorizer=vectorizer,
                filterable_fields=[
                    {"name": "prompt_version", "type": "tag"},
                    {"name": "project_type", "type": "tag"},
                    {"name": "detail_level", "type": "tag"},
                    {"name": "output_format", "type": "tag"},
                    {"name": "reference_context", "type": "tag"},
                ],
            )
        except Exception as exc:  # noqa: BLE001
            raise SemanticCacheUnavailable(str(exc)) from exc

    def get(
        self,
        *,
        request: EstimationRequest,
        prompt_version: str,
    ) -> EstimationResult | None:
        if self._cache is None:
            return None
        bucket = semantic_bucket(request, prompt_version)
        try:
            matches = self._cache.check(
                prompt=request.description,
                filter_expression=_filter_expression(bucket),
                num_results=1,
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("semantic_cache_get_failed", error_type=type(exc).__name__)
            return None

        if not matches:
            log.info("semantic_cache_miss", **bucket)
            return None
        match = matches[0]
        similarity = 1 - float(match.get("distance", self.distance_threshold))
        log.info(
            "semantic_cache_candidate", similarity=similarity, log_only=self.log_only, **bucket
        )
        if self.log_only:
            return None
        try:
            payload = match.get("response") or match.get("metadata", {}).get("response")
            return EstimationResult.model_validate_json(payload)
        except Exception as exc:  # noqa: BLE001
            log.warning("semantic_cache_payload_invalid", error_type=type(exc).__name__)
            return None

    def set(
        self,
        *,
        request: EstimationRequest,
        prompt_version: str,
        result: EstimationResult,
    ) -> None:
        if self._cache is None:
            return
        bucket = semantic_bucket(request, prompt_version)
        try:
            self._cache.store(
                prompt=request.description,
                response=result.model_dump_json(),
                filters=bucket,
            )
            log.info("semantic_cache_stored", **bucket)
        except Exception as exc:  # noqa: BLE001
            log.warning("semantic_cache_set_failed", error_type=type(exc).__name__)
