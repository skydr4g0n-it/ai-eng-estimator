"""LiteLLM-backed wrapper that adds provider fallback, exact-match cache, cost tracking,
and structured logging to every LLM call in the estimator.

Design notes
------------
- The wrapper exposes two primitives: ``complete()`` (blocking, full response) and
  ``complete_stream()`` (yields chunks). Higher-level orchestration (preprocessing,
  validation, prompt building) stays in ``llm_service.py``.
- The Router is configured with multiple deployments under the same ``model_name``
  ("ollama-estimator") so LiteLLM can switch from primary to fallback transparently.
  When the caller overrides the model per-request (Session 2 live demos), we
  bypass the Router and call ``litellm.completion`` directly with explicit
  credentials — that path has no fallback by design.
- The cache key includes the full system prompt and the generation knobs, so any
  Session 2 toggle (preprocessing, num_examples, ACTIVE_OUTPUT_PROMPT) implicitly
  invalidates the cache without manual flushing.
"""

from __future__ import annotations

import time
from typing import Any, Iterator

import litellm
import structlog
from litellm import Router
from pydantic import BaseModel, ValidationError

from app.services.cache import EstimationCache

log = structlog.get_logger()

# Cost per 1M tokens (USD). Update as pricing changes.
MODEL_COSTS: dict[str, dict[str, float]] = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
    "claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
    "gemini-2.5-flash": {"input": 0.10, "output": 0.40},
    "qwen3.5:9b": {"input": 0.0, "output": 0.0},
}


def _estimate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    base = _normalise_model_name(model)
    costs = MODEL_COSTS.get(base) or MODEL_COSTS.get(model) or {"input": 0.0, "output": 0.0}
    return round((tokens_in * costs["input"] + tokens_out * costs["output"]) / 1_000_000, 6)


def _normalise_model_name(model: str) -> str:
    """Strip provider prefixes like ``anthropic/`` that LiteLLM may emit."""
    return model.split("/", 1)[1] if "/" in model else model


def _provider_from_model(model: str) -> str:
    raw = model.lower()
    if raw.startswith("ollama"):
        return "ollama"
    if raw.startswith("gemini"):
        return "google"
    name = _normalise_model_name(model).lower()
    if name.startswith("claude"):
        return "anthropic"
    if name.startswith("gpt") or name.startswith("o1") or name.startswith("o3"):
        return "openai"
    return "unknown"


class LLMWrapper:
    """Unified LLM client with cache, fallback, and cost tracking."""

    def __init__(
        self,
        *,
        openai_api_key: str | None,
        anthropic_api_key: str | None,
        google_api_key: str | None = None,
        ollama_base_url: str = "http://localhost:11434",
        ollama_model: str = "qwen3.5:9b",
        primary_model: str,
        fallback_model: str,
        timeout: int,
        num_retries: int,
        cache: EstimationCache,
    ):
        self.openai_api_key = openai_api_key
        self.anthropic_api_key = anthropic_api_key
        self.google_api_key = google_api_key
        self.ollama_base_url = ollama_base_url
        self.ollama_model = ollama_model
        self.primary_model = primary_model
        self.fallback_model = fallback_model
        self.timeout = timeout
        self.num_retries = num_retries
        self.cache = cache

        self.router = Router(
            model_list=[
                {
                    "model_name": "ollama-estimator",
                    "litellm_params": {
                        "model": f"ollama/{ollama_model}",
                        "api_base": ollama_base_url,
                        "timeout": 120,
                    },
                },
                {
                    "model_name": "gemini-estimator",
                    "litellm_params": {
                        "model": "gemini/gemini-2.5-flash",
                        "api_key": google_api_key,
                        "timeout": timeout,
                    },
                },
                {
                    "model_name": "anthropic-estimator",
                    "litellm_params": {
                        "model": f"anthropic/{fallback_model}",
                        "api_key": anthropic_api_key,
                        "timeout": timeout,
                    },
                },
                {
                    "model_name": "openai-estimator",
                    "litellm_params": {
                        "model": primary_model,
                        "api_key": openai_api_key,
                        "timeout": timeout,
                    },
                },
            ],
            fallbacks=[
                {"ollama-estimator": ["gemini-estimator"]},
                {"gemini-estimator": ["anthropic-estimator"]},
                {"anthropic-estimator": ["openai-estimator"]},
            ],
            num_retries=num_retries,
        )

    def complete(
        self,
        *,
        system_prompt: str,
        user_message: str,
        model_override: str | None = None,
        max_tokens: int = 4000,
        thinking_budget: int | None = None,
    ) -> dict[str, Any]:
        """Single LLM call with cache + (optional) fallback. Returns the legacy dict shape
        plus ``cache_hit`` and ``cost_usd`` fields.
        """
        cache_key_model = model_override or self.primary_model
        cache_key = EstimationCache.make_key(
            system_prompt=system_prompt,
            user_message=user_message,
            model=cache_key_model,
            max_tokens=max_tokens,
            thinking_budget=thinking_budget,
        )
        cached = self.cache.get(cache_key)
        if cached:
            return {**cached, "cache_hit": True}

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        kwargs = self._build_call_kwargs(
            messages=messages,
            max_tokens=max_tokens,
            thinking_budget=thinking_budget,
            model_override=model_override,
        )

        log.info(
            "llm_call_started",
            mode="blocking",
            model=model_override or self.primary_model,
            has_thinking=thinking_budget is not None,
        )
        t0 = time.perf_counter()
        try:
            response = self._dispatch(model_override=model_override, **kwargs)
        except Exception as exc:
            latency_ms = int((time.perf_counter() - t0) * 1000)
            log.error(
                "llm_call_failed",
                error_type=type(exc).__name__,
                error=str(exc),
                latency_ms=latency_ms,
            )
            raise

        latency_ms = int((time.perf_counter() - t0) * 1000)
        result = self._normalise_response(response, latency_ms=latency_ms)
        log.info(
            "llm_call_completed",
            model=result["model"],
            provider=result["provider"],
            input_tokens=result["usage"]["input_tokens"],
            output_tokens=result["usage"]["output_tokens"],
            cost_usd=result["cost_usd"],
            latency_ms=latency_ms,
            finish_reason=result["finish_reason"],
        )
        self.cache.set(cache_key, result)
        return {**result, "cache_hit": False}

    def complete_stream(
        self,
        *,
        system_prompt: str,
        user_message: str,
        model_override: str | None = None,
        max_tokens: int = 4000,
    ) -> Iterator[str]:
        """Yield text chunks as they arrive from the model.

        Cache hits replay the cached estimation as a single chunk so the client UX
        stays consistent. Cache misses stream live and the full text is cached
        once the stream finishes (without ``cost_usd`` since LiteLLM does not
        always report token usage for streaming calls).
        """
        cache_key_model = model_override or self.primary_model
        cache_key = EstimationCache.make_key(
            system_prompt=system_prompt,
            user_message=user_message,
            model=cache_key_model,
            max_tokens=max_tokens,
            thinking_budget=None,
        )
        cached = self.cache.get(cache_key)
        if cached:
            log.info("stream_cache_hit", chars=len(cached.get("estimation", "")))
            yield cached.get("estimation", "")
            return

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        kwargs = self._build_call_kwargs(
            messages=messages,
            max_tokens=max_tokens,
            thinking_budget=None,
            model_override=model_override,
            stream=True,
        )

        log.info(
            "llm_stream_started",
            model=model_override or self.primary_model,
        )
        t0 = time.perf_counter()
        full_text: list[str] = []
        try:
            response = self._dispatch(model_override=model_override, **kwargs)
            for chunk in response:
                delta = _extract_delta(chunk)
                if delta:
                    full_text.append(delta)
                    yield delta
        except Exception as exc:
            latency_ms = int((time.perf_counter() - t0) * 1000)
            log.error(
                "llm_stream_failed",
                error_type=type(exc).__name__,
                error=str(exc),
                latency_ms=latency_ms,
            )
            raise

        latency_ms = int((time.perf_counter() - t0) * 1000)
        rendered = "".join(full_text)
        log.info("llm_stream_completed", latency_ms=latency_ms, chars=len(rendered))

        self.cache.set(
            cache_key,
            {
                "estimation": rendered,
                "model": model_override or self.primary_model,
                "provider": _provider_from_model(model_override or self.primary_model),
                "finish_reason": "stop",
                "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
                "latency_ms": latency_ms,
                "cost_usd": 0.0,
            },
        )

    def complete_structured(
        self,
        *,
        system_prompt: str,
        user_message: str,
        response_model: type[BaseModel],
        model_override: str | None = None,
        max_tokens: int = 4000,
        validation_retries: int = 2,
    ) -> dict[str, Any]:
        """Return a validated Pydantic model using Instructor-style structured output."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        resolved_model = model_override or self.primary_model
        log.info(
            "structured_llm_call_started",
            model=resolved_model,
            validation_retries=validation_retries,
        )
        t0 = time.perf_counter()
        try:
            parsed = self._dispatch_structured(
                messages=messages,
                response_model=response_model,
                model_override=model_override,
                max_tokens=max_tokens,
                validation_retries=validation_retries,
            )
            if not isinstance(parsed, response_model):
                parsed = response_model.model_validate(parsed)
        except (ValidationError, ValueError, TypeError) as exc:
            latency_ms = int((time.perf_counter() - t0) * 1000)
            log.error(
                "structured_llm_validation_exhausted",
                error_type=type(exc).__name__,
                latency_ms=latency_ms,
                model=resolved_model,
            )
            raise
        except Exception as exc:
            latency_ms = int((time.perf_counter() - t0) * 1000)
            log.error(
                "structured_llm_call_failed",
                error_type=type(exc).__name__,
                latency_ms=latency_ms,
                model=resolved_model,
            )
            raise

        latency_ms = int((time.perf_counter() - t0) * 1000)
        metadata = {
            "model": _normalise_model_name(resolved_model),
            "provider": _provider_from_model(resolved_model),
            "latency_ms": latency_ms,
        }
        log.info("structured_llm_call_completed", **metadata)
        return {"result": parsed, "metadata": metadata}

    def _build_call_kwargs(
        self,
        *,
        messages: list[dict],
        max_tokens: int,
        thinking_budget: int | None,
        model_override: str | None,
        stream: bool = False,
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "messages": messages,
            "max_tokens": max_tokens,
        }
        if stream:
            kwargs["stream"] = True

        if thinking_budget is not None:
            target_model = model_override or self.primary_model
            if _provider_from_model(target_model) == "anthropic":
                kwargs["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}
                kwargs["max_tokens"] = max(max_tokens, thinking_budget + 1024)
            else:
                log.warning(
                    "thinking_budget_ignored_for_provider",
                    provider=_provider_from_model(target_model),
                    model=target_model,
                )
        return kwargs

    def _dispatch(self, *, model_override: str | None, **kwargs: Any) -> Any:
        """Call the Router (with fallback) or LiteLLM directly when the caller
        wants a specific model."""
        if model_override:
            provider = _provider_from_model(model_override)
            if provider == "ollama":
                return litellm.completion(
                    model=model_override,
                    api_base=self.ollama_base_url,
                    timeout=self.timeout,
                    num_retries=self.num_retries,
                    **kwargs,
                )
            if provider == "google":
                return litellm.completion(
                    model=model_override,
                    api_key=self.google_api_key,
                    timeout=self.timeout,
                    num_retries=self.num_retries,
                    **kwargs,
                )
            api_key = (
                self.anthropic_api_key
                if provider == "anthropic"
                else self.openai_api_key
            )
            return litellm.completion(
                model=model_override,
                api_key=api_key,
                timeout=self.timeout,
                num_retries=self.num_retries,
                **kwargs,
            )
        return self.router.completion(model="ollama-estimator", **kwargs)

    def _dispatch_structured(
        self,
        *,
        messages: list[dict],
        response_model: type[BaseModel],
        model_override: str | None,
        max_tokens: int,
        validation_retries: int,
    ) -> BaseModel:
        """Instructor-backed structured dispatch.

        Kept in a separate method so tests can monkeypatch the provider boundary without
        reaching into routers or prompt rendering.
        """
        try:
            import instructor
            from instructor import Mode
        except ImportError as exc:
            raise RuntimeError("instructor is required for structured estimation output") from exc

        if model_override is None:
            providers = [
                ("ollama", Mode.JSON, self.ollama_base_url, None),
                ("google", Mode.JSON, None, self.google_api_key),
                ("anthropic", Mode.TOOLS, None, self.anthropic_api_key),
                ("openai", Mode.TOOLS, None, self.openai_api_key),
            ]
            last_error: Exception | None = None
            for provider_name, mode, api_base, api_key in providers:
                if provider_name == "ollama" and api_base:
                    try:
                        client = instructor.from_litellm(litellm.completion, mode=mode)
                        return client.chat.completions.create(
                            model=f"ollama/{self.ollama_model}",
                            api_base=api_base,
                            messages=messages,
                            max_tokens=max_tokens,
                            response_model=response_model,
                            max_retries=validation_retries,
                            timeout=self.timeout,
                            extra_body={"think": False},
                        )
                    except Exception as exc:
                        last_error = exc
                        log.warning("structured_fallback", provider=provider_name, error=str(exc))
                        continue
                if provider_name == "google" and api_key:
                    try:
                        client = instructor.from_litellm(litellm.completion, mode=mode)
                        return client.chat.completions.create(
                            model="gemini/gemini-2.5-flash",
                            api_key=api_key,
                            messages=messages,
                            max_tokens=max_tokens,
                            response_model=response_model,
                            max_retries=validation_retries,
                            timeout=self.timeout,
                        )
                    except Exception as exc:
                        last_error = exc
                        log.warning("structured_fallback", provider=provider_name, error=str(exc))
                        continue
                if provider_name == "anthropic" and api_key:
                    try:
                        client = instructor.from_litellm(litellm.completion, mode=mode)
                        return client.chat.completions.create(
                            model=f"anthropic/{self.fallback_model}",
                            api_key=api_key,
                            messages=messages,
                            max_tokens=max_tokens,
                            response_model=response_model,
                            max_retries=validation_retries,
                            timeout=self.timeout,
                        )
                    except Exception as exc:
                        last_error = exc
                        log.warning("structured_fallback", provider=provider_name, error=str(exc))
                        continue
                if provider_name == "openai" and api_key:
                    try:
                        client = instructor.from_litellm(litellm.completion, mode=mode)
                        return client.chat.completions.create(
                            model=self.primary_model,
                            api_key=api_key,
                            messages=messages,
                            max_tokens=max_tokens,
                            response_model=response_model,
                            max_retries=validation_retries,
                            timeout=self.timeout,
                        )
                    except Exception as exc:
                        last_error = exc
                        log.warning("structured_fallback", provider=provider_name, error=str(exc))
                        continue
            if last_error:
                raise last_error
            raise RuntimeError("No LLM providers available for structured dispatch")

        target_model = model_override
        provider = _provider_from_model(target_model)
        if provider == "ollama":
            client = instructor.from_litellm(litellm.completion, mode=Mode.JSON)
            return client.chat.completions.create(
                model=target_model,
                api_base=self.ollama_base_url,
                messages=messages,
                max_tokens=max_tokens,
                response_model=response_model,
                max_retries=validation_retries,
                timeout=self.timeout,
                extra_body={"think": False},
            )
        if provider == "google":
            client = instructor.from_litellm(litellm.completion, mode=Mode.JSON)
            return client.chat.completions.create(
                model=target_model,
                api_key=self.google_api_key,
                messages=messages,
                max_tokens=max_tokens,
                response_model=response_model,
                max_retries=validation_retries,
                timeout=self.timeout,
            )
        api_key = (
            self.anthropic_api_key
            if provider == "anthropic"
            else self.openai_api_key
        )
        client = instructor.from_litellm(litellm.completion)
        return client.chat.completions.create(
            model=target_model,
            api_key=api_key,
            messages=messages,
            max_tokens=max_tokens,
            response_model=response_model,
            max_retries=validation_retries,
            timeout=self.timeout,
        )

    @staticmethod
    def _normalise_response(response: Any, *, latency_ms: int) -> dict[str, Any]:
        choice = response.choices[0]
        finish_reason = (choice.finish_reason or "stop").lower()
        usage = response.usage
        input_tokens = getattr(usage, "prompt_tokens", 0) or 0
        output_tokens = getattr(usage, "completion_tokens", 0) or 0
        total_tokens = getattr(usage, "total_tokens", input_tokens + output_tokens) or (
            input_tokens + output_tokens
        )

        model = _normalise_model_name(response.model)
        return {
            "estimation": choice.message.content or "",
            "model": model,
            "provider": _provider_from_model(response.model),
            "finish_reason": finish_reason,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
            },
            "latency_ms": latency_ms,
            "cost_usd": _estimate_cost(model, input_tokens, output_tokens),
        }


def _extract_delta(chunk: Any) -> str:
    """Pull the text delta out of a LiteLLM streaming chunk."""
    try:
        delta = chunk.choices[0].delta
    except (AttributeError, IndexError):
        return ""
    content = getattr(delta, "content", None)
    return content or ""
