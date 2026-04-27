from fastapi import FastAPI

from app.config import settings
from app.routers import estimations

app = FastAPI(
    title="Estimador CAG",
    description=(
        "API para generar estimaciones de software a partir de transcripciones "
        "de reuniones usando contexto estatico inyectado en el prompt."
    ),
    version="0.1.0",
)

app.include_router(estimations.router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "environment": settings.app_env,
        "provider": settings.llm_provider,
        "model": settings.llm_model,
    }
