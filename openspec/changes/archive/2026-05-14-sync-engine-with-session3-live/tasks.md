## 1. Dependencies and tooling

- [x] 1.1 Update `engine/pyproject.toml`: add `litellm`, `redis`, `structlog`, `sse-starlette`, `httpx`; add dev `pytest-asyncio`, `ruff`, `fakeredis`; **do not** add `streamlit`.
- [x] 1.2 Regenerate or update `engine/uv.lock` with `uv lock` (or project-standard lock workflow).
- [x] 1.3 Add `.python-version` under `engine/` if the team standardizes on a single patch release (e.g. `3.11`).
- [x] 1.4 Add Ruff config blocks aligned with the reference (`line-length`, `target-version`).

## 2. Configuration and secrets

- [x] 2.1 Port `Settings` from the reference: `PRIMARY_MODEL`, `FALLBACK_MODEL`, `LLM_TIMEOUT`, `LLM_RETRIES`, `REDIS_URL`, `CACHE_TTL`, `APP_ENV`, validation for at least one API key; omit `ESTIMATOR_API_BASE_URL` or keep undocumented optional stub only if code requires it (prefer removal).
- [x] 2.2 Refresh `engine/.env.example` to document Session 3 variables; remove Streamlit-only comments/vars.

## 3. Core services

- [x] 3.1 Add `app/services/cache.py` (`EstimationCache`) and `app/services/llm_wrapper.py` (`LLMWrapper`) per reference, adapted only for layout under `engine/`.
- [x] 3.2 Add `app/dependencies.py` with `get_cache` and `get_llm_wrapper` singletons.
- [x] 3.3 Port `app/services/evaluation.py` and wire optional validation from the sync router.
- [x] 3.4 Replace `app/services/llm_service.py` implementation to orchestrate preprocessing, `build_system_prompt`, `generate_estimation`, and errors through LiteLLM wrapper semantics from the reference (no direct `openai`/`anthropic` SDK completion paths).

## 4. HTTP API and static assets

- [x] 4.1 Replace schemas with reference-aligned models in `app/schemas/estimation.py` (adjust imports project-wide; remove or rename obsolete `estimations.py`).
- [x] 4.2 Update `app/routers/estimations.py`: sync `POST /api/v1/estimate`, stream `POST /api/v1/estimate/stream`, error handling, structlog usage.
- [x] 4.3 Update `app/main.py`: lifespan structlog setup, CORS if present, mount `app/static` for `sse_demo.html` when packaged.
- [x] 4.4 Copy `app/static/sse_demo.html` from the reference (SSE demo only).

## 5. Docker and CI

- [x] 5.1 Update `engine/docker-compose.yml`: Redis service with health check; API `depends_on` Redis; override `REDIS_URL` for in-network Redis; bind-mount `./app` for dev reload if keeping reference dev UX.
- [x] 5.2 Update `engine/Dockerfile` and image CMD as needed for new entrypoint/deps.
- [x] 5.3 Update `engine/.github/workflows/ci.yml` to provision Redis (service container or compose) and export `REDIS_URL` for pytest; ensure no Streamlit steps.

## 6. Tests and fixtures

- [x] 6.1 Port reference tests (`conftest.py`, cache, stream, evaluation, health, examples format, LLM wrapper, estimate endpoint); drop or rewrite tests that assume the old schema-only layout.
- [x] 6.2 Add `app/fixtures/` transcription files if referenced by tests; align paths.
- [x] 6.3 Run `docker compose` test target (or `uv run pytest`) locally and fix failures.

## 7. Documentation

- [x] 7.1 Update `engine/README.md`: new endpoints, Redis requirement, LiteLLM env vars, **BREAKING** API note, explicit “Streamlit not included” line pointing to the upstream course repo for learners who want it.

## 8. OpenSpec closure

- [x] 8.1 After implementation merge, run `openspec validate --strict` repo-wide and archive this change per `openspec/AGENTS.md`, merging deltas into `openspec/specs/`.
