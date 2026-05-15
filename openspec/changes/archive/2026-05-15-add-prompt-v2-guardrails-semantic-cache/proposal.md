## Why

The estimator has a first version of form-driven prompt rendering and exact-match caching, but it still lacks production controls for prompt experiments, structured model output, guardrail validation, and near-duplicate request reuse. This change makes the estimation pipeline safer to operate, easier to debug, and cheaper under repeated similar traffic.

## What Changes

- Add real prompt versioning for estimation prompts by creating `engine/app/prompts/estimation/v2/` alongside `v1/`, with `v2` deliberately changing tone only.
- Allow both `POST /api/v1/estimate` and `POST /api/v1/estimate/stream` to accept `?prompt_version=v2`; unsupported versions return HTTP 422 with a clear response body.
- Extend the synchronous estimation request schema with optional `reference_projects: list[ReferenceProject] | None`, and render them in the Jinja templates using a `{% for %}` loop when present.
- **BREAKING** Change the synchronous LLM output contract from free-form estimation text to structured JSON validated into a typed `EstimationResult`.
- Make the AI service always return the rich data shape (`EstimationResult`) rather than presentation-specific text; `output_format` becomes prompt guidance for summary/assumption detail, while rendering for tables, PDFs, Slack, email, or UI lives outside the AI service.
- Add Guardrails AI plus domain-specific input and output guardrails, including prompt-injection/PII checks and business-rule validation for duration totals, cost totals, confidence, and assumptions.
- Use Instructor to manage structured responses across providers, and retry invalid structured LLM output up to 2 times.
- Add semantic response caching alongside the existing exact-match Redis cache, using a composite cache identity: deterministic bucket fields plus a vector embedding of the free-text description.
- Implement semantic caching with RedisVL `SemanticCache`, using bucket filters, a text vectorizer, TTL, and a cosine similarity threshold between 0.85 and 0.90.
- Emit a structlog event for every prompt render with the prompt version and a SHA-256 content hash, without logging full descriptions or full rendered prompts.
- Remove the duplicated `ai-engineering/estimator/` application tree if it is confirmed to be redundant, keeping implementation scope under `engine/`.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `estimation-api`: Add query-level prompt version selection, reference projects, structured estimation responses, guardrail error behavior, and unsupported-version validation.
- `estimation-streaming`: Add query-level prompt version selection and unsupported-version validation for streaming estimates.
- `llm-provider`: Add Instructor-backed structured-output completion support with bounded validation retries and provider metadata for structured calls.
- `redis-cache`: Preserve exact-match caching and add RedisVL semantic caching with deterministic buckets, embedding-based lookup, configurable threshold, TTL, and safe degradation.
- `platform-runtime`: Add runtime dependencies and configuration for Guardrails AI, Instructor, embeddings, Redis vector search, prompt render logging, and duplicate-tree cleanup.

## Impact

- Affected API surface: `POST /api/v1/estimate`, `POST /api/v1/estimate/stream`, request schema, synchronous response schema, and validation error responses.
- Affected code under `engine/`: `app/schemas/`, `app/routers/`, `app/services/`, `app/prompts/`, `app/dependencies.py`, `app/config.py`, tests, Docker Compose, `.env.example`, and dependency lock files.
- New dependencies may include Guardrails AI, Instructor, RedisVL `SemanticCache`, OpenAI embeddings client support, and supporting numeric/vector packages.
- Operational impact: local Redis may need Redis Stack or another vector-capable Redis deployment for semantic cache; the service must degrade gracefully when semantic cache setup is unavailable.
