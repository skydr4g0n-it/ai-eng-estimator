## ADDED Requirements

### Requirement: Redis-backed exact-match cache

The system SHALL store successful LLM estimation payloads in **Redis** using an exact-match key derived from a canonical JSON serialization of the system prompt, user message, resolved model name, `max_tokens`, and optional thinking budget, with a configurable TTL. Cache read and write failures SHALL degrade gracefully (miss on read, no-op on write) while emitting structured log events.

#### Scenario: Cache hit returns stored payload

- **WHEN** a new estimation request produces the same cache key as a previously stored successful response and Redis contains that key
- **THEN** the service returns the cached payload without invoking the LLM and marks the response with `cache_hit` true

#### Scenario: Redis unavailable on read

- **WHEN** Redis raises an error on `GET`
- **THEN** the service treats the lookup as a miss, proceeds with a normal LLM call, and does not fail the user request solely due to the cache read error

### Requirement: Operational Redis dependency

The deployment default for local development and CI SHALL include a **healthy Redis** instance reachable at `REDIS_URL`. The API process SHALL depend on Redis being available for normal cache operation; tests MAY use in-memory fakes when they do not assert real network semantics.

#### Scenario: Compose wires in-network Redis

- **WHEN** the stack is started with the project Docker Compose file
- **THEN** the API container receives `REDIS_URL` pointing at the Compose `redis` service hostname and starts only after Redis passes its health check
