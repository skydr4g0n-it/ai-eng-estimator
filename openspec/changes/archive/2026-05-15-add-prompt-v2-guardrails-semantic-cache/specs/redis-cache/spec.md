## MODIFIED Requirements

### Requirement: Redis-backed exact-match cache

The system SHALL store successful LLM estimation payloads in Redis using an exact-match key derived from a canonical JSON serialization of the selected prompt version, rendered system prompt, rendered user message, resolved model name, `max_tokens`, optional thinking budget, and structured request context including reference projects when present, with a configurable TTL. Cache read and write failures SHALL degrade gracefully (miss on read, no-op on write) while emitting structured log events. Exact-match cache lookup SHALL run only after input guardrails pass and before semantic cache lookup.

#### Scenario: Cache hit returns stored payload

- **WHEN** a new estimation request produces the same cache key as a previously stored successful response and Redis contains that key
- **THEN** the service returns `EstimationResponse(result=<cached result>, prompt_version=<selected version>)` without invoking the LLM and logs an exact cache hit internally

#### Scenario: Redis unavailable on read

- **WHEN** Redis raises an error on `GET`
- **THEN** the service treats the lookup as a miss, proceeds with the remaining pipeline, and does not fail the user request solely due to the cache read error

### Requirement: Operational Redis dependency

The deployment default for local development and CI SHALL include a healthy Redis instance reachable at `REDIS_URL`. The API process SHALL depend on Redis being available for normal exact cache operation. Semantic cache operation SHALL use a vector-capable Redis deployment such as Redis Stack or SHALL disable semantic lookup with a structured warning if vector indexing is unavailable. Tests MAY use in-memory fakes when they do not assert real network or vector-index semantics.

#### Scenario: Compose wires in-network Redis

- **WHEN** the stack is started with the project Docker Compose file
- **THEN** the API container receives `REDIS_URL` pointing at the Compose Redis service hostname and starts only after Redis passes its health check

#### Scenario: Semantic cache disabled without vector support

- **WHEN** the application starts with Redis reachable but vector index creation is unsupported
- **THEN** exact-match caching remains available and semantic caching is disabled with a structured warning

## ADDED Requirements

### Requirement: Semantic estimation cache

The system SHALL provide a RedisVL `SemanticCache` for validated estimation results. Semantic lookup SHALL run only after input guardrails pass and exact-match cache misses. The semantic cache identity SHALL be composite: a deterministic bucket plus a vector embedding. The deterministic bucket SHALL include at least `prompt_version`, `project_type`, `detail_level`, `output_format`, and reference-project context. The vector part SHALL be the embedding of `request.description` only. Lookup SHALL compare description embeddings only within the same deterministic bucket, using RedisVL filterable fields or equivalent filtering, so incompatible prompts or request options cannot share cached results. The product-level threshold SHALL be expressed as cosine similarity between 0.85 and 0.90 and translated to RedisVL's cosine distance threshold when configuring `SemanticCache`. Semantic cache write SHALL occur only after the response passes Pydantic `model_validator`, Guardrails AI validators, and all configured semantic/domain output checks.

#### Scenario: Similar request returns semantic hit

- **WHEN** a valid request misses exact cache and has embedding similarity at or above the configured threshold to a stored validated result in the same bucket
- **THEN** the service returns `EstimationResponse(result=<cached result>, prompt_version=<selected version>)` without invoking the LLM and logs a semantic cache hit internally

#### Scenario: Structured parameters isolate buckets

- **WHEN** two requests have the same `description` but different `output_format` or `detail_level`
- **THEN** semantic lookup uses different deterministic buckets and cannot return the first request's cached result for the second request

#### Scenario: Different prompt version does not cross-hit

- **WHEN** a request uses `prompt_version=v2` and a semantically similar cached entry exists only for `prompt_version=v1`
- **THEN** semantic lookup treats the entry as ineligible and proceeds as a miss

#### Scenario: Prompt version migration needs no manual invalidation

- **WHEN** the default prompt version changes from `v1` to `v2`
- **THEN** new semantic cache lookups target `v2` buckets while `v1` entries remain unused until Redis TTL expires them

#### Scenario: Below-threshold similarity misses

- **WHEN** the nearest stored result in the same bucket has cosine similarity below the configured threshold
- **THEN** the service treats semantic lookup as a miss and invokes the LLM

#### Scenario: Log-only mode does not serve hits

- **WHEN** semantic cache log-only mode is enabled and a request would otherwise qualify as a semantic hit
- **THEN** the service logs the candidate similarity but does not return the cached result

### Requirement: Guardrail-safe cache order

The estimation pipeline SHALL run input guardrails before any exact-match or semantic cache lookup. A cache hit SHALL NOT bypass input guardrails. The pipeline SHALL write to exact-match and semantic caches only after the LLM output has passed Instructor/Pydantic structured validation, Pydantic model validators, Guardrails AI validators, and configured semantic/domain output checks. Failed, repaired-but-invalid, unsafe, or unvalidated responses MUST NOT be cached.

#### Scenario: Unsafe input cannot receive cached result

- **WHEN** a request contains prompt injection or blocked content that would otherwise match an existing cache entry
- **THEN** input guardrails reject the request before exact or semantic cache lookup

#### Scenario: Invalid LLM output is not cached

- **WHEN** the LLM returns output that fails validation after all retries
- **THEN** the pipeline returns a safe error or fallback response and writes nothing to exact or semantic caches
