"""FastAPI dependency factories for shared singletons (cache and LLM wrapper)."""

from __future__ import annotations

from functools import lru_cache

import structlog

from app.cache.semantic import SemanticCacheUnavailable, SemanticEstimationCache
from app.config import get_settings
from app.services.cache import EstimationCache
from app.services.estimation_service import EstimationService
from app.services.llm_wrapper import LLMWrapper

log = structlog.get_logger()


@lru_cache
def get_cache() -> EstimationCache:
    settings = get_settings()
    return EstimationCache.from_url(settings.REDIS_URL, ttl=settings.CACHE_TTL)


@lru_cache
def get_llm_wrapper() -> LLMWrapper:
    settings = get_settings()
    return LLMWrapper(
        openai_api_key=settings.OPENAI_API_KEY,
        anthropic_api_key=settings.ANTHROPIC_API_KEY,
        primary_model=settings.PRIMARY_MODEL,
        fallback_model=settings.FALLBACK_MODEL,
        timeout=settings.LLM_TIMEOUT,
        num_retries=settings.LLM_RETRIES,
        cache=get_cache(),
    )


@lru_cache
def get_semantic_cache() -> SemanticEstimationCache | None:
    settings = get_settings()
    if not settings.SEMANTIC_CACHE_ENABLED:
        return None
    try:
        return SemanticEstimationCache(
            redis_url=settings.REDIS_URL,
            embedding_model=settings.EMBEDDING_MODEL,
            similarity_threshold=settings.SEMANTIC_CACHE_THRESHOLD,
            ttl=settings.SEMANTIC_CACHE_TTL,
            log_only=settings.SEMANTIC_CACHE_LOG_ONLY,
        )
    except SemanticCacheUnavailable as exc:
        log.warning("semantic_cache_disabled", reason=str(exc))
        return None


def get_estimation_service() -> EstimationService:
    return EstimationService(
        settings=get_settings(),
        exact_cache=get_cache(),
        semantic_cache=get_semantic_cache(),
        llm_wrapper=get_llm_wrapper(),
    )
