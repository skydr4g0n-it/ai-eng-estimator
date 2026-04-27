from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class EstimationRequest(BaseModel):
    transcription: str = Field(
        ...,
        min_length=1,
        description="Texto de la transcripcion de la reunion con el cliente.",
    )

    @field_validator("transcription")
    @classmethod
    def transcription_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("La transcripcion no puede estar vacia.")
        return stripped


class EstimationResponse(BaseModel):
    estimation: str
    model: str
    provider: str
    generated_at: datetime
