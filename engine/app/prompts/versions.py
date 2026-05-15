"""Prompt-version validation shared by sync and streaming routes."""

from __future__ import annotations

from fastapi import HTTPException

from app.config import get_settings


def supported_prompt_versions() -> tuple[str, ...]:
    return get_settings().supported_prompt_versions


def resolve_prompt_version(prompt_version: str | None) -> str:
    settings = get_settings()
    selected = prompt_version or settings.ESTIMATION_PROMPT_VERSION
    supported = settings.supported_prompt_versions
    if selected not in supported:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "unsupported_prompt_version",
                "prompt_version": selected,
                "supported_versions": list(supported),
            },
        )
    return selected
