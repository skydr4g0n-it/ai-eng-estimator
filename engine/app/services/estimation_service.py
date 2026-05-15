"""Synchronous estimation pipeline orchestration."""

from __future__ import annotations

import structlog
from pydantic import ValidationError

from app.cache.semantic import SemanticEstimationCache, semantic_bucket
from app.config import Settings
from app.guardrails import GuardrailViolation, validate_input, validate_output
from app.prompts.loader import render_estimation_prompt
from app.schemas.estimation import EstimationRequest, EstimationResponse, EstimationResult
from app.services.cache import EstimationCache
from app.services.llm_wrapper import LLMWrapper

log = structlog.get_logger()

DEFAULT_MAX_TOKENS = 4000


class EstimationServiceError(Exception):
    """Raised when the estimation pipeline cannot produce a safe response."""


class EstimationOutputInvalid(EstimationServiceError):
    """Raised when structured output cannot be validated."""


class EstimationService:
    """Run guardrails, cache lookup, prompt render, LLM call, validation, and cache writes."""

    def __init__(
        self,
        *,
        settings: Settings,
        exact_cache: EstimationCache,
        semantic_cache: SemanticEstimationCache | None,
        llm_wrapper: LLMWrapper,
    ) -> None:
        self.settings = settings
        self.exact_cache = exact_cache
        self.semantic_cache = semantic_cache
        self.llm_wrapper = llm_wrapper

    def estimate(self, request: EstimationRequest, *, prompt_version: str) -> EstimationResponse:
        validate_input(request)
        system_prompt, user_message = render_estimation_prompt(request, version=prompt_version)
        exact_key = EstimationCache.make_key(
            system_prompt=system_prompt,
            user_message=user_message,
            model=self.settings.PRIMARY_MODEL,
            max_tokens=DEFAULT_MAX_TOKENS,
            thinking_budget=None,
            extra_context=self._cache_context(request, prompt_version),
        )

        cached = self.exact_cache.get(exact_key)
        if cached:
            result = EstimationResult.model_validate(cached["result"])
            return EstimationResponse(result=result, prompt_version=cached["prompt_version"])

        if self.semantic_cache is not None:
            semantic_result = self.semantic_cache.get(
                request=request, prompt_version=prompt_version
            )
            if semantic_result is not None:
                return EstimationResponse(result=semantic_result, prompt_version=prompt_version)

        try:
            structured = self.llm_wrapper.complete_structured(
                system_prompt=system_prompt,
                user_message=user_message,
                response_model=EstimationResult,
                model_override=None,
                max_tokens=DEFAULT_MAX_TOKENS,
                validation_retries=self.settings.ESTIMATION_VALIDATION_RETRIES,
            )
            result = structured["result"]
            validate_output(result)
        except GuardrailViolation:
            raise
        except (ValidationError, ValueError, TypeError) as exc:
            log.error("estimation_output_invalid", error_type=type(exc).__name__)
            raise EstimationOutputInvalid("Structured estimation output failed validation") from exc
        except Exception as exc:
            log.error("estimation_service_failed", error_type=type(exc).__name__)
            raise EstimationServiceError("Estimation service failed") from exc

        response = EstimationResponse(result=result, prompt_version=prompt_version)
        payload = response.model_dump(mode="json")
        self.exact_cache.set(exact_key, payload)
        if self.semantic_cache is not None:
            self.semantic_cache.set(request=request, prompt_version=prompt_version, result=result)
        return response

    @staticmethod
    def _cache_context(request: EstimationRequest, prompt_version: str) -> dict:
        return {
            "prompt_version": prompt_version,
            "semantic_bucket": semantic_bucket(request, prompt_version),
            "request": request.model_dump(mode="json", exclude={"description"}),
        }
