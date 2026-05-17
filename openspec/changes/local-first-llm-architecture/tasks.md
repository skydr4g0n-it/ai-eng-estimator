## 1. Configuration and Settings

- [x] 1.1 Add `GOOGLE_API_KEY`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, and `EMBEDDING_MODEL` fields to `app/config.py` Settings class with appropriate defaults (`OLLAMA_BASE_URL="http://localhost:11434"`, `OLLAMA_MODEL="qwen2.5:14b"`, `EMBEDDING_MODEL="nomic-embed-text"`)
- [x] 1.2 Update the `model_validator` in Settings to allow all cloud API keys to be empty (remove the requirement that at least one of `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` must be set)
- [x] 1.3 Update `engine/.env.example` to document all new variables with defaults and examples

## 2. Docker Compose Topology

- [x] 2.1 Add `ollama` service to `engine/docker-compose.yml` with `ollama/ollama:latest` image, port `11434`, `ollama_data` volume, and GPU reservation via `deploy.resources.reservations.devices`
- [x] 2.2 Update `api` service to depend on `ollama` (condition `service_started`) and pass `OLLAMA_BASE_URL=http://ollama:11434`
- [x] 2.3 Update `tests` service environment to include `OLLAMA_BASE_URL` and `OLLAMA_MODEL` with test-appropriate values

## 3. LLM Wrapper — Router Expansion

- [x] 3.1 Update `LLMWrapper.__init__` to accept `google_api_key: str | None` and `ollama_base_url: str` parameters alongside existing `openai_api_key` and `anthropic_api_key`
- [x] 3.2 Expand the Router `model_list` to 4 deployments: Ollama (primary, `api_base=ollama_base_url`, timeout=120), Gemini (`api_key=google_api_key`), Anthropic, OpenAI — all under `model_name: "estimator"`
- [x] 3.3 Update `_dispatch` to handle Ollama provider (no API key, uses `api_base`) and Google provider (uses `google_api_key`)
- [x] 3.4 Update `_provider_from_model` to return `"ollama"` for `"ollama/"` prefix and `"google"` for `"gemini/"` or `"gemini-"` prefix
- [x] 3.5 Update `MODEL_COSTS` to include Gemini pricing (`gemini-2.5-flash`: input ~$0.10/M, output ~$0.40/M) and Ollama entry with $0 costs

## 4. LLM Wrapper — Structured Completions

- [x] 4.1 Update `_dispatch_structured` to handle Ollama provider (no API key, uses `api_base`) and Google provider (uses `google_api_key`)
- [x] 4.2 Verify instructor compatibility with Ollama's OpenAI-compatible endpoint (test with mock or local run)

## 5. Dependencies and Service Wiring

- [x] 5.1 Update `get_llm_wrapper()` in `app/dependencies.py` to pass `google_api_key` and `ollama_base_url` from settings to `LLMWrapper`

## 6. Semantic Cache — Local Embeddings

- [x] 6.1 Create `app/cache/ollama_vectorizer.py` with an `OllamaTextVectorizer` class that implements `embed(text: str) -> list[float]` by calling Ollama's `/api/embed` endpoint via HTTP POST
- [x] 6.2 Update `SemanticEstimationCache._init_redisvl` in `app/cache/semantic.py` to use `OllamaTextVectorizer` instead of `OpenAITextVectorizer`
- [x] 6.3 Update the `SemanticEstimationCache` constructor to accept `ollama_base_url` parameter for the vectorizer
- [x] 6.4 Update `get_semantic_cache()` in `app/dependencies.py` to pass `ollama_base_url` to `SemanticEstimationCache`

## 7. Tests

- [x] 7.1 Update test fixtures to mock Ollama endpoints (`/api/chat`, `/api/embed`) alongside existing OpenAI/Anthropic mocks
- [x] 7.2 Add tests for 4-tier fallback chain behavior (local success, local fail → Gemini success, full chain exhaustion)
- [x] 7.3 Add tests for offline mode: system starts and handles requests with no cloud API keys
- [x] 7.4 Add tests for `OllamaTextVectorizer` embedding generation (mock HTTP response)
- [x] 7.5 Update existing tests that assume API keys are required to work with empty-key configuration
- [x] 7.6 Run full test suite from `engine/` via `docker compose run --rm tests` and verify all pass

## 8. Verification

- [ ] 8.1 Pull `qwen2.5:14b` and `nomic-embed-text` models in local Ollama instance
- [x] 8.2 Start full stack with `docker compose up` and verify all 3 services (redis, ollama, api) are healthy
- [x] 8.3 Test streaming endpoint (`POST /api/v1/estimate/stream`) with a sample transcription and verify local model response
- [x] 8.4 Test structured endpoint (`POST /api/v1/estimate`) with a sample project description and verify structured output
- [ ] 8.5 Test offline mode: stop cloud connectivity, verify local-only operation still works
- [ ] 8.6 Test fallback: stop Ollama container, verify cloud provider fallback (if API keys configured)
