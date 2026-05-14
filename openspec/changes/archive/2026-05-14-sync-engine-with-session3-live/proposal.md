# Change: Sync `engine/` with LIDR `session_3_live` (minus chat UI)

## Why

The course reference branch [LIDR-academy/ai-engineering @ `session_3_live`](https://github.com/LIDR-academy/ai-engineering/tree/session_3_live) (`estimator/`) advances the Estimator with LiteLLM-backed generation, Redis-backed exact-match caching, optional structural validation, structured logging, and an SSE streaming endpoint. This fork’s runnable service lives under `engine/` and should match that behavior so coursework and demos align, while **omitting Streamlit and other chat-style UI** and their dependencies.

## What Changes

- **BREAKING**: Replace the current direct OpenAI/Anthropic client path in `engine/` with **LiteLLM** via a dedicated wrapper (primary model + fallback, retries, timeout, token usage and cost metadata).
- **BREAKING**: Align HTTP contracts with the reference: richer `POST /api/v1/estimate` request body, extended response fields (e.g. `cache_hit`, `cost_usd`, `validation`), and schema module layout consistent with the reference (`estimation` models, generation options).
- Add **`POST /api/v1/estimate/stream`** (Server-Sent Events) for token streaming, plus static assets for the **SSE demo page** (not a chat product UI).
- Require **Redis** at runtime and in CI/Docker Compose for the cache; tests use **fakeredis** where appropriate for hermetic runs.
- Add **structlog** configuration (JSON in production, console in development) and lifecycle wiring in FastAPI.
- Expand **pytest** coverage toward the reference suite (cache, streaming, evaluation, health, examples format, LLM wrapper behavior with mocks).
- Add **Ruff** and **pytest-asyncio** to match reference developer ergonomics; add `.python-version` if aligned with `>=3.11`.
- **Out of scope**: `streamlit`, `streamlit_app.py`, `ESTIMATOR_API_BASE_URL` product coupling, and any Streamlit-specific documentation beyond a short README note that the course UI is intentionally omitted.

## Impact

- **Affected specs (new)**: `llm-provider`, `redis-cache`, `estimation-api`, `estimation-streaming`, `platform-runtime`.
- **Affected code**: `engine/pyproject.toml`, `engine/uv.lock`, `engine/app/**/*.py`, `engine/app/static/`, `engine/docker-compose.yml`, `engine/Dockerfile`, `engine/.env.example`, `engine/.github/workflows/ci.yml`, `engine/README.md`, `engine/tests/**`.
