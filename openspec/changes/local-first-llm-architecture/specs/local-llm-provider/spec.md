## ADDED Requirements

### Requirement: Local LLM inference via Ollama

The system SHALL support Ollama as a local LLM inference provider. The system SHALL connect to an Ollama instance via its REST API (default `http://localhost:11434`) and send completion requests using the `ollama/` LiteLLM model prefix. The local provider SHALL be configured as the first deployment in the LiteLLM Router's `model_list` under `model_name: "estimator"`, making it the primary inference engine when available. The system SHALL allow the Ollama base URL and model name to be configured via environment variables `OLLAMA_BASE_URL` and `OLLAMA_MODEL`.

#### Scenario: Local model handles completion request

- **WHEN** an estimation request is submitted and the Ollama instance is reachable with the configured model loaded
- **THEN** the completion is performed locally and the response includes the resolved model identifier, provider set to `"ollama"`, token usage counts, and `cost_usd` of `0.0`

#### Scenario: Local model not reachable triggers fallback

- **WHEN** an estimation request is submitted and the Ollama instance at `OLLAMA_BASE_URL` is unreachable
- **THEN** the LiteLLM Router falls through to the next deployment in the chain (Google Gemini)

#### Scenario: Configured model name is used

- **WHEN** `OLLAMA_MODEL` is set to `qwen2.5:14b`
- **THEN** completion requests are sent to Ollama with model identifier `ollama/qwen2.5:14b`

### Requirement: Ollama service in Docker Compose

The Docker Compose stack under `engine/` SHALL define an `ollama` service using the `ollama/ollama:latest` image, exposing port `11434`, with a named volume for model persistence (`ollama_data:/root/.ollama`). The `ollama` service SHALL reserve GPU resources via `deploy.resources.reservations.devices` with `capabilities: [gpu]`. The `api` service SHALL depend on the `ollama` service and pass `OLLAMA_BASE_URL=http://ollama:11434` as an environment variable.

#### Scenario: Docker Compose starts all services

- **WHEN** a developer runs `docker compose up` from `engine/`
- **THEN** the `redis`, `ollama`, and `api` services start, with the `api` service able to reach Ollama at `http://ollama:11434`

#### Scenario: Ollama model persists across restarts

- **WHEN** the `ollama` container is restarted after pulling a model
- **THEN** the model is still available from the `ollama_data` volume without re-downloading

### Requirement: Local model cost tracking

The `MODEL_COSTS` dictionary in `app/services/llm_wrapper.py` SHALL include an entry for Ollama models with `input` and `output` costs set to `0.0`. The `_provider_from_model` function SHALL return `"ollama"` for model identifiers starting with `"ollama/"` or containing `"ollama"` as a provider prefix.

#### Scenario: Local completion reports zero cost

- **WHEN** a completion is performed via the Ollama provider
- **THEN** the response metadata includes `cost_usd: 0.0` and `provider: "ollama"`
