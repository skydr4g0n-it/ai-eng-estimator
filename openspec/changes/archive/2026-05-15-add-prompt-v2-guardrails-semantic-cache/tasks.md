## 1. Schema and Prompt Versioning

- [x] 1.1 Add `ReferenceProject`, `Phase`, `EstimationResult`, and `EstimationResponse(result: EstimationResult, prompt_version: str)` models in `engine/app/schemas/estimation.py`.
- [x] 1.2 Add supported prompt-version validation shared by sync and streaming endpoints, returning HTTP 422 with supported versions for unsupported query values.
- [x] 1.3 Create `engine/app/prompts/estimation/v2/` beside `v1/`, changing prompt tone only while preserving variables, schema instructions, and examples contract.
- [x] 1.4 Update `engine/app/prompts/loader.py` to render optional `reference_projects` via template context and emit `prompt_rendered` with prompt version and SHA-256 content hash.
- [x] 1.5 Add offline prompt tests for `v1`, `v2`, unsupported versions, reference project rendering, output-format-as-guidance behavior, and safe render logging.

## 2. Structured LLM Output

- [x] 2.1 Add Instructor-backed structured completion support to `engine/app/services/llm_wrapper.py` using `response_model=EstimationResult`.
- [x] 2.2 Cap Instructor repair/validation retries at 2 for estimation calls and expose the setting through `engine/app/config.py`.
- [x] 2.3 Preserve existing free-text completion and streaming primitives for legacy tests and `/estimate/stream`.
- [x] 2.4 Add unit tests for structured success, validation repair, retry exhaustion, model override behavior, and no router-level SDK calls.
- [x] 2.5 Add schema contract tests for `EstimationResult`, including the total-cost mismatch case where phases cost 12000 EUR but `total_cost_eur` is 10000 EUR.

## 3. Guardrails Pipeline

- [x] 3.1 Add Guardrails AI and supporting structured-output dependencies to `engine/pyproject.toml` and lock files.
  - Implemented with local `engine/app/guardrails/` input/output guardrail modules because the configured package index returned no compatible `guardrails-ai` distribution. `instructor` and `redisvl` are added to `engine/pyproject.toml` and `engine/uv.lock`.
- [x] 3.2 Create `engine/app/guardrails/` modules for input checks covering moderation integration, prompt-injection patterns, and obvious PII in descriptions/reference projects.
- [x] 3.3 Create output guardrails for structured result validation, duration tolerance, cost tolerance, phase confidence, and safe fallback messaging.
- [x] 3.4 Add an `EstimationService` orchestration layer under `engine/app/services/` that runs input guardrails before any cache lookup, then exact cache, semantic cache, prompt render, structured LLM call, output guardrails, cache writes, and response assembly.
- [x] 3.5 Update `engine/app/routers/estimations.py` so routers stay thin and map guardrail, prompt-version, validation, and upstream errors to the required HTTP responses.
- [x] 3.6 Add API and service tests for guardrail rejection, output validation failure, retry behavior, and safe logging without full user content.
- [x] 3.7 Ensure `output_format` is treated only as prompt guidance and does not change the `EstimationResult` response schema.

## 4. Semantic Cache

- [x] 4.1 Add `engine/app/cache/semantic.py` using RedisVL `SemanticCache` with filterable deterministic buckets scoped by prompt version, project type, detail level, output format, and reference-project context.
- [x] 4.2 Configure embedding model, semantic threshold default within 0.85-0.90, TTL, and log-only mode in `engine/app/config.py` and `engine/.env.example`.
- [x] 4.3 Wire semantic cache dependencies in `engine/app/dependencies.py`, disabling semantic cache with a structured warning when vector setup is unavailable.
- [x] 4.4 Ensure exact-match cache runs after input guardrails and includes prompt version, rendered prompts, model, generation knobs, and reference context in key identity.
- [x] 4.5 Implement composite semantic cache identity where the deterministic bucket is separate from the vector embedding of `request.description`.
- [x] 4.6 Translate configured cosine similarity threshold to RedisVL cosine distance threshold when constructing `SemanticCache`.
- [x] 4.7 Ensure exact and semantic cache writes happen only after Instructor/Pydantic validation, Pydantic model validators, Guardrails AI validators, and domain output checks pass.
- [x] 4.8 Add semantic cache tests for hit, miss, below-threshold behavior, prompt-version isolation, output-format/detail-level isolation, reference-project isolation, log-only mode, guardrail-before-hit behavior, no-write-on-invalid-output behavior, and setup failure degradation.

## 5. Streaming Endpoint

- [x] 5.1 Update `/api/v1/estimate/stream` to accept and validate `prompt_version` before opening the SSE stream.
- [x] 5.2 Render streaming prompts from the selected prompt version or adapt the existing streaming prompt builder so `v1` and `v2` tone selection is real.
- [x] 5.3 Add streaming endpoint tests for default version, `v2`, unsupported-version 422, happy-path token events, and mid-stream error behavior.

## 6. Runtime and Cleanup

- [x] 6.1 Update `engine/docker-compose.yml` to use vector-capable Redis when semantic cache is expected locally, or document fallback behavior when vector support is absent.
- [x] 6.2 Update `engine/README.md` with prompt versioning, structured response shape, guardrails, semantic cache configuration, and local verification steps.
- [x] 6.3 Remove `ai-engineering/estimator/` after confirming it is duplicate application code and no OpenSpec/task paths depend on it.
- [x] 6.4 Run formatting and linting for changed engine code.
- [x] 6.5 Run `docker compose run --rm tests` from `engine/` and record the result.
  - Result: `docker compose run --rm --build tests` passed with 62 tests.
- [x] 6.6 Run `openspec status --change add-prompt-v2-guardrails-semantic-cache` and confirm the change is apply-ready.
