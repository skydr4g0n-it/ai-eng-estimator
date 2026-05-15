## Context

The current `engine/` service exposes a form-driven synchronous estimation endpoint, a streaming endpoint, versioned Jinja prompt templates for `v1`, a LiteLLM wrapper, and Redis exact-match caching. The next increment needs production-facing controls: prompt A/B style selection, structured output, input/output validation, semantic reuse of similar requests, and prompt render observability without logging sensitive project descriptions.

The upstream session 4 reference shows a useful direction: a thin router, a dedicated estimation pipeline service, structured `EstimationResult` models with business validators, input/output guardrails, semantic cache buckets, and a wrapper method for structured completions. This design adapts those ideas to this repo's `engine/` layout and keeps `ai-engineering/estimator/` out of scope except for deleting it as duplicate code.

## Goals / Non-Goals

**Goals:**

- Support prompt version selection on both sync and streaming endpoints with `v1` and `v2`.
- Keep prompt packs as real directories under `engine/app/prompts/estimation/<version>/`.
- Add optional `reference_projects` to the request schema and render them only when supplied.
- Make the sync LLM result structured JSON validated by Pydantic and Guardrails AI.
- Add bounded repair/retry behavior for invalid LLM output, capped at 2 retries.
- Keep the AI service contract data-only: it always returns `EstimationResult`; presentation choices live in the business backend or frontend.
- Add semantic cache lookup after exact cache miss and before LLM invocation.
- Log prompt render metadata with prompt version and content hash, never full prompt contents.
- Keep routers thin by moving orchestration into a service-layer pipeline.

**Non-Goals:**

- No prompt versioning UI is required in the client.
- No database persistence of estimations is required.
- No semantic cache hit is allowed across different prompt versions or request option buckets.
- No streaming structured JSON contract is required; streaming can remain token text but must use the selected prompt version.
- No table, PDF, Slack, email, or UI rendering is owned by the AI service.
- No implementation outside `engine/` is required, except removing confirmed duplicate app code under `ai-engineering/estimator/`.

## Decisions

1. Use a dedicated `EstimationService` pipeline for synchronous estimation.

   The router should parse HTTP parameters, inject dependencies, and map known exceptions to HTTP responses. The service should run input guardrails, exact cache lookup, semantic cache lookup, prompt rendering, structured LLM completion, output guardrails, cache writes, and response assembly. This keeps endpoint behavior testable without coupling HTTP tests to provider internals. The alternative was to extend `engine/app/services/llm_service.py` directly; that is simpler initially but would keep too many concerns in one module.

2. Represent structured output with Pydantic models, Guardrails AI, and Instructor.

   The sync response should wrap a typed `EstimationResult` containing `summary`, `total_duration_weeks`, `total_cost_eur`, `confidence_pct`, and `phases`. Each `Phase` contains `name`, `duration_weeks`, `cost_eur`, `confidence_pct`, and `assumptions`. The model validator should enforce that summed phase weeks match `total_duration_weeks` within 1 week and summed phase cost matches `total_cost_eur` within 5%, with safe handling for zero totals. Guardrails AI should sit around the input/output validation path for policy checks and structured validation. Instructor is the required structured-output adapter so provider differences are handled behind a single `response_model=EstimationResult` call with validation retries. The alternative was to ask the LLM for JSON and parse manually; that would make repair/retry and validation less reliable.

3. Keep data and presentation separate.

   The AI service always returns the rich `EstimationResult` shape, not a rendered table, narrative, or line-item document. `output_format` remains on `EstimationRequest`, but it is interpreted as prompt guidance that influences how extensive the `summary` is and how detailed phase `assumptions` are. The business backend or frontend decides how to render the result for a table, PDF, Slack message, email, or UI. The alternative was to make the AI service return presentation-specific text; that couples future delivery channels to prompt and schema changes.

4. Use `prompt_version` as an explicit pipeline input.

   `v1` remains the default from settings. `v2` is a sibling prompt pack that changes tone only, not fields or examples. Both sync and streaming endpoints accept a query parameter and validate it against directories or a configured allowlist. Unsupported versions raise HTTP 422 with a body that names the unsupported value and supported versions. The alternative was to fall back to `v1`; that hides production misconfiguration and makes experiments hard to reason about.

5. Use a composite semantic cache identity to avoid unsafe reuse.

   Semantic cache identity has two parts. The deterministic part is a bucket derived from `prompt_version`, `project_type`, `detail_level`, `output_format`, and reference-project context. The vector part is the embedding of `request.description`. Lookup only compares vectors inside the same deterministic bucket, so two requests with the same description but different detail level, output format, project type, reference context, or prompt version cannot collide. `prompt_version` is deliberately first-class in the bucket so promoting `v2` naturally moves traffic into new buckets while `v1` entries age out by TTL. The threshold should default within 0.85-0.90, with `0.87` as a balanced starting point and a `log_only` mode for calibration. The alternative was global nearest-neighbor lookup over embedded descriptions; that risks returning estimates shaped for different prompt instructions.

6. Prefer `text-embedding-3-small` initially.

   `text-embedding-3-small` is cost-effective and matches the upstream reference dimensions. It is appropriate for short-to-medium project descriptions and can be made configurable through `EMBEDDING_MODEL`. If later traffic shows poor semantic precision, the model can be swapped by settings and index migration. The alternative, a larger embedding model, may improve recall but raises cost before the feature has traffic data.

7. Run guardrails before cache reads and cache writes only after full validation.

   Input guardrails must run before exact or semantic cache lookup, because the cache is also an output surface that can leak or amplify unsafe requests. Exact-match cache remains the cheapest lookup after input validation and can run before embedding generation. Semantic lookup then computes the description embedding and searches RedisVL inside the deterministic bucket. Cache writes happen only after the LLM output passes Instructor/Pydantic validation, Guardrails AI validators, and domain checks. The alternative was to serve cache hits before input guardrails or write before output validation; both make the cache propagate unsafe or malformed responses.

8. Implement semantic cache with RedisVL `SemanticCache`.

   RedisVL `SemanticCache` provides the Redis-backed vector cache primitive, TTL, vectorizer integration, distance threshold, and filterable fields needed for bucketed lookup. The implementation should configure filterable bucket fields and translate the product-level similarity threshold into the RedisVL cosine distance threshold used by the library. The alternative was a custom `SearchIndex` wrapper; that gives more control but duplicates library functionality and increases implementation surface.

9. Log prompt render hashes in the loader.

   `render_estimation_prompt` should compute a SHA-256 over the rendered system and user content and emit `prompt_rendered` with `prompt_version`, template names, and hash prefixes or full hashes. It must not log full rendered prompts, descriptions, reference project details, or API keys. The alternative was to log prompt text for debugging; that conflicts with production privacy constraints.

## Risks / Trade-offs

- Structured response is a breaking API change -> Keep the OpenSpec requirement explicit, update tests and docs, and return exactly `EstimationResponse(result: EstimationResult, prompt_version: str)`.
- Guardrails AI dependency may add setup complexity -> Isolate guardrail code under `engine/app/guardrails/` and degrade only where safe; unsafe input violations must fail closed.
- Semantic cache can return a plausible but wrong reused estimate -> Scope by prompt/version/options/reference context, use a conservative threshold, expose `SEMANTIC_CACHE_LOG_ONLY`, and store only validated outputs.
- Redis vector support may not exist in vanilla Redis -> Document Redis Stack or equivalent vector support; disable semantic cache with warning when index setup fails while preserving exact cache.
- Output repair retries can increase latency -> Cap validation retries at 2 and log retry failures with error class and prompt version.
- `v2` tone-only prompt can accidentally change output semantics -> Keep schema and examples unchanged or copied, and test that `v2` renders the same variables while changing only tone guidance.
- Removing `ai-engineering/estimator/` could delete useful local artifacts -> Verify duplication before deletion and keep the canonical app under `engine/`.

## Migration Plan

1. Add schemas, prompt version validation, `v2` templates, render logging, and tests without enabling semantic cache hits by default if Redis vector support is unavailable.
2. Add the service pipeline, structured LLM wrapper path, Guardrails AI checks, and response model changes.
3. Add semantic cache implementation, config, Docker/README updates, and tests using fakes where possible.
4. Remove duplicated `ai-engineering/estimator/` after confirming all canonical implementation and tests live under `engine/`.
5. Rollback path: set default prompt version back to `v1`, disable semantic cache via configuration, and fall back to exact cache plus Instructor-backed structured generation. If structured output causes client incompatibility, revert the response contract change together with dependent tests.

## Open Questions

- Should moderation use OpenAI Moderation when an OpenAI key is configured, or should Guardrails AI be the only moderation layer for the first implementation?
