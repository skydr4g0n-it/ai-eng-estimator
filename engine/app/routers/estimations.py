import asyncio
from collections.abc import AsyncIterator

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sse_starlette.sse import EventSourceResponse

from app.dependencies import get_estimation_service, get_llm_wrapper
from app.guardrails import GuardrailViolation
from app.prompts.versions import resolve_prompt_version
from app.schemas.estimation import (
    EstimationRequest,
    EstimationResponse,
    StreamEstimationRequest,
)
from app.services.estimation_service import EstimationOutputInvalid, EstimationService
from app.services.llm_service import build_system_prompt
from app.services.llm_wrapper import LLMWrapper

log = structlog.get_logger()

router = APIRouter(prefix="/api/v1", tags=["estimations"])


@router.post("/estimate", response_model=EstimationResponse)
async def create_estimation(
    request: EstimationRequest,
    prompt_version: str | None = Query(default=None),
    service: EstimationService = Depends(get_estimation_service),
) -> EstimationResponse:
    """Structured project description -> validated estimation result."""
    selected_version = resolve_prompt_version(prompt_version)
    try:
        return service.estimate(request, prompt_version=selected_version)
    except GuardrailViolation as exc:
        raise HTTPException(status_code=400, detail=exc.safe_message) from exc
    except EstimationOutputInvalid as exc:
        raise HTTPException(
            status_code=502,
            detail="The estimator could not produce a valid structured result. Please try again.",
        ) from exc
    except Exception as exc:
        log.error("estimation_endpoint_error", error_type=type(exc).__name__)
        raise HTTPException(
            status_code=500,
            detail="Estimation service temporarily unavailable. Please try again later.",
        ) from exc


@router.post("/estimate/stream")
async def create_estimation_stream(
    request: StreamEstimationRequest,
    prompt_version: str | None = Query(default=None),
    wrapper: LLMWrapper = Depends(get_llm_wrapper),
) -> EventSourceResponse:
    """Stream a software estimation token by token via Server-Sent Events."""
    selected_version = resolve_prompt_version(prompt_version)
    system_prompt = build_system_prompt()
    if selected_version == "v2":
        system_prompt = f"{system_prompt}\n\nUse a crisp, executive tone."

    async def event_generator() -> AsyncIterator[dict]:
        loop = asyncio.get_running_loop()
        chunks = wrapper.complete_stream(
            system_prompt=system_prompt,
            user_message=request.transcription,
            model_override=request.model,
            max_tokens=request.max_tokens,
        )

        def _next_chunk() -> str | None:
            try:
                return next(chunks)
            except StopIteration:
                return None
            except Exception as exc:  # noqa: BLE001 - surface as SSE error event
                log.error("estimate_stream_failed", error_type=type(exc).__name__)
                raise

        try:
            while True:
                chunk = await loop.run_in_executor(None, _next_chunk)
                if chunk is None:
                    break
                if chunk:
                    yield {"event": "token", "data": chunk}
            yield {"event": "done", "data": "[DONE]"}
        except Exception as exc:  # noqa: BLE001
            yield {"event": "error", "data": str(exc)}

    return EventSourceResponse(event_generator())
