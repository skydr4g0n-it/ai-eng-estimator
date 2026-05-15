# platform-runtime Specification

## Purpose
TBD - created by archiving change sync-engine-with-session3-live. Update Purpose after archive.
## Requirements
### Requirement: Structured application logging

The system SHALL configure structlog at application startup with ISO timestamps, log level, and stack/excinfo processors. In production environment mode the renderer SHALL emit JSON logs; in non-production modes the renderer SHALL use a human-readable console renderer. Prompt rendering SHALL emit a structured event containing prompt version and a SHA-256 hash of rendered prompt content, but MUST NOT log full prompts, full descriptions, full reference projects, or API keys by default.

#### Scenario: Startup emits structured application event

- **WHEN** the FastAPI application completes startup after logging configuration
- **THEN** at least one structured log event records the active `APP_ENV` and indicates the application has started

#### Scenario: Prompt render emits safe metadata

- **WHEN** the prompt loader renders an estimation prompt
- **THEN** structlog records prompt version and content hash while excluding full user-provided content and rendered prompt text

### Requirement: Health endpoint metadata

The system SHALL expose `GET /health` returning JSON with service health status, a semantic version string, and the active `APP_ENV` value suitable for orchestration probes.

#### Scenario: Health check for compose

- **WHEN** an unauthenticated client calls `GET /health`
- **THEN** the response status is 200 and the JSON includes `status`, `version`, and `environment` keys populated from configuration

### Requirement: Containerized runtime with Redis

The primary Docker Compose definition under `engine/` SHALL define the API service and a Redis service with health checks, override `REDIS_URL` inside the API container to the in-network Redis host, and declare an explicit dependency so the API starts after Redis is healthy. When semantic caching is enabled, the local development Redis image SHALL support vector search or the application SHALL disable semantic caching with a structured warning while preserving exact-match cache behavior.

#### Scenario: Developer stack matches production-like wiring

- **WHEN** a developer runs `docker compose up` from `engine/` with a valid `.env` providing API keys
- **THEN** the API process can open Redis using `REDIS_URL` and serve `/docs` and `/api/v1` routes without manual extra containers beyond Compose

#### Scenario: Vector cache setup degrades safely

- **WHEN** semantic cache dependencies are configured but the Redis container does not support vector indexes
- **THEN** startup continues with exact-match cache available and a structured warning indicates semantic cache is disabled

### Requirement: Continuous integration with Redis

The CI workflow for the engine SHALL run automated tests in an environment where Redis is reachable at the `REDIS_URL` supplied to the job (for example via a service container or compose profile), and SHALL NOT install or invoke Streamlit. CI SHALL include tests for prompt version validation, structured output validation, guardrail behavior, and semantic cache behavior using fakes or local services as appropriate.

#### Scenario: CI exports Redis to tests

- **WHEN** CI executes the test suite on a pull request
- **THEN** jobs configure `REDIS_URL` to a running Redis instance and the test command completes without requiring Streamlit or manual Redis startup outside the workflow definition

#### Scenario: CI covers new pipeline controls

- **WHEN** CI executes the engine test suite
- **THEN** tests exercise supported and unsupported prompt versions, guardrail rejection, structured output validation retry/error paths, and semantic cache hit/miss behavior without live LLM calls

### Requirement: Runtime configuration for structured safeguards

The system SHALL expose runtime configuration for prompt default version, supported prompt versions or prompt directory discovery, Instructor validation retry count, RedisVL semantic cache threshold, semantic cache TTL, semantic cache log-only mode, embedding model, and guardrail behavior. Configuration defaults SHALL be documented in `engine/.env.example` and SHALL avoid requiring live API keys for offline tests.

#### Scenario: Defaults documented

- **WHEN** a developer inspects `engine/.env.example`
- **THEN** the file documents defaults or examples for prompt versioning, structured validation retries, RedisVL semantic cache settings, embedding model, and guardrail settings

#### Scenario: Tests run without live keys

- **WHEN** the automated test suite runs in CI without OpenAI or Anthropic API keys
- **THEN** tests use mocks or fakes for LLM, embedding, moderation, and guardrail integrations

### Requirement: Canonical engine application tree

The repository SHALL treat `engine/` as the canonical FastAPI estimator application tree. If `ai-engineering/estimator/` is duplicated application code, it SHALL be removed so future changes do not need to update two Python app copies. OpenSpec artifacts and implementation tasks SHALL refer to paths under `engine/` for application code.

#### Scenario: Duplicate tree removed

- **WHEN** the change is implemented and `ai-engineering/estimator/` is confirmed to duplicate `engine/`
- **THEN** the duplicate tree is removed and the remaining tests and documentation point at `engine/`

