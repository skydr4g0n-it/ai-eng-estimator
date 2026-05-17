## MODIFIED Requirements

### Requirement: Runtime configuration for structured safeguards

The system SHALL expose runtime configuration for prompt default version, supported prompt versions or prompt directory discovery, Instructor validation retry count, RedisVL semantic cache threshold, semantic cache TTL, semantic cache log-only mode, embedding model, and guardrail behavior. Configuration defaults SHALL be documented in `engine/.env.example` and SHALL avoid requiring live API keys for offline tests.

The system SHALL accept the following additional configuration variables:
- `GOOGLE_API_KEY`: Google AI Studio API key for Gemini provider access (optional)
- `OLLAMA_BASE_URL`: URL of the Ollama instance (default `http://localhost:11434`)
- `OLLAMA_MODEL`: Ollama model tag to use for completions (default `qwen2.5:14b`)
- `EMBEDDING_MODEL`: Embedding model name for semantic cache (default `nomic-embed-text`)

The API key validation SHALL NOT require any cloud API key to be set. The system SHALL operate in offline mode when all cloud API keys are absent.

#### Scenario: Defaults documented

- **WHEN** a developer inspects `engine/.env.example`
- **THEN** the file documents defaults or examples for all configuration variables including `GOOGLE_API_KEY`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, and `EMBEDDING_MODEL`

#### Scenario: Tests run without live keys

- **WHEN** the automated test suite runs in CI without OpenAI, Anthropic, or Google API keys
- **THEN** tests use mocks or fakes for LLM, embedding, moderation, and guardrail integrations

#### Scenario: System starts with only Ollama configured

- **WHEN** `OLLAMA_BASE_URL` and `OLLAMA_MODEL` are set but all cloud API keys are empty
- **THEN** the application starts successfully and uses Ollama as the sole LLM provider

### Requirement: Containerized runtime with Redis

The primary Docker Compose definition under `engine/` SHALL define the API service, a Redis service with health checks, and an Ollama service with GPU passthrough. The Compose file SHALL override `REDIS_URL` inside the API container to the in-network Redis host and `OLLAMA_BASE_URL` to the in-network Ollama host. The API service SHALL declare explicit dependencies on both Redis (healthy condition) and Ollama (started condition). When semantic caching is enabled, the local development Redis image SHALL support vector search or the application SHALL disable semantic caching with a structured warning while preserving exact-match cache behavior.

#### Scenario: Developer stack matches production-like wiring

- **WHEN** a developer runs `docker compose up` from `engine/` with a valid `.env` providing at least `OLLAMA_MODEL`
- **THEN** the API process can open Redis using `REDIS_URL`, reach Ollama at `http://ollama:11434`, and serve `/docs` and `/api/v1` routes without manual extra containers beyond Compose

#### Scenario: Vector cache setup degrades safely

- **WHEN** semantic cache dependencies are configured but the Redis container does not support vector indexes
- **THEN** startup continues with exact-match cache available and a structured warning indicates semantic cache is disabled
