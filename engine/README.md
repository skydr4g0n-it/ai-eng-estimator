# Estimator Engine

FastAPI service for software estimates. The synchronous `POST /api/v1/estimate`
path accepts a typed request, renders versioned Jinja prompts from
`app/prompts/estimation/<version>/`, calls the LLM through the wrapper, and
returns structured `EstimationResponse` data:

```json
{
  "result": {
    "summary": "...",
    "total_duration_weeks": 6,
    "total_cost_eur": 12000,
    "confidence_pct": 80,
    "phases": []
  },
  "prompt_version": "v1"
}
```

`output_format` is prompt guidance only. It can influence the richness of the
summary and assumptions, but the response schema stays `EstimationResult`.

## Prompt Versions

Supported prompt versions are configured with `ESTIMATION_PROMPT_VERSIONS`
(default `v1,v2`) and selected per request with `?prompt_version=v2`.
Unsupported versions return HTTP 422 and list supported versions. `v1` remains
the default; `v2` changes tone only.

## Guardrails

The synchronous pipeline runs input guardrails before cache lookup. It rejects
prompt-injection-like instructions and obvious PII in descriptions or reference
projects. Structured output must pass Pydantic validators and domain output
checks before it can be returned or cached. Logs include reason codes and prompt
hashes, not full descriptions, reference project details, or rendered prompts.

## Caching

Exact-match Redis cache keys include the selected prompt version, rendered
system and user prompts, model, generation knobs, and structured request
context. Semantic caching uses RedisVL when vector support is available. Its
bucket includes `prompt_version`, `project_type`, `detail_level`,
`output_format`, and reference-project context, while the vector compares only
`description`. RedisVL lookups apply that bucket as tag filter expressions, so
similar descriptions cannot cross prompt versions or structured request options.
Set `SEMANTIC_CACHE_LOG_ONLY=true` to observe candidates without serving
semantic hits.

Local Compose uses Redis Stack for vector search. If RedisVL or vector setup is
unavailable, startup continues with exact-match caching and logs that semantic
cache is disabled.

## Environment

Copy `.env.example` to `.env` and set provider keys for live LLM calls.
Important defaults:

```text
ESTIMATION_PROMPT_VERSION=v1
ESTIMATION_PROMPT_VERSIONS=v1,v2
ESTIMATION_VALIDATION_RETRIES=2
SEMANTIC_CACHE_ENABLED=true
SEMANTIC_CACHE_LOG_ONLY=false
SEMANTIC_CACHE_THRESHOLD=0.87
SEMANTIC_CACHE_TTL=86400
EMBEDDING_MODEL=text-embedding-3-small
```

## Run

```bash
cd engine
docker compose up --build
```

API docs are at `http://localhost:8000/docs`.

## Test

```bash
cd engine
uv sync --dev
uv run pytest
```

Docker/CI style:

```bash
cd engine
docker compose run --rm tests
```
