from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.schemas.estimations import EstimationRequest, EstimationResponse
from app.services import llm_service
from app.services.llm_service import LLMConfigurationError

router = APIRouter(prefix="/estimate", tags=["estimations"])


@router.post("", response_model=EstimationResponse)
async def estimate(request: EstimationRequest) -> EstimationResponse:
    try:
        estimation = await llm_service.generate_estimation(request.transcription)
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="No se pudo generar la estimacion con el proveedor LLM.",
        ) from exc

    return EstimationResponse(
        estimation=estimation,
        model=settings.llm_model,
        provider=settings.llm_provider,
        generated_at=datetime.now(UTC),
    )
