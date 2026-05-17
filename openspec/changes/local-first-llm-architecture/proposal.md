## Why

The estimator currently depends on paid cloud LLM providers (OpenAI primary, Anthropic fallback) for every estimation call, incurring API costs during development and requiring internet connectivity. This change introduces a local-first architecture using Ollama (Qwen 2.5 14B) as the primary inference engine, with Google Gemini, Anthropic, and OpenAI as cascading fallbacks — enabling zero-cost local development, offline operation, and graceful degradation when cloud providers are unavailable.

## What Changes

- **Local LLM as primary**: Ollama running Qwen 2.5 14B (Q4_K_M) becomes the default first-tier inference engine for all estimation paths (streaming and structured).
- **Google Gemini added**: Gemini 2.5 Flash joins the fallback chain as the first cloud tier (cheap, large context).
- **4-tier fallback chain**: Local → Google → Anthropic → OpenAI, with automatic cascading on failure.
- **Offline mode**: The system operates fully locally when no cloud API keys are configured; config validation no longer requires any cloud API key.
- **Local embeddings**: Semantic cache embeddings switch from OpenAI `text-embedding-3-small` to Ollama `nomic-embed-text`, removing the last OpenAI hard dependency.
- **Docker Compose topology**: New `ollama` service with GPU passthrough alongside existing `redis` and `api` services.
- **Cost tracking extended**: `MODEL_COSTS` includes Gemini pricing and $0 for local models.

## Capabilities

### New Capabilities
- `local-llm-provider`: Ollama-based local LLM inference as the primary provider, including model configuration, GPU passthrough in Docker, and LiteLLM Ollama integration.
- `google-llm-provider`: Google Gemini as a cloud fallback provider, including API key configuration, LiteLLM Gemini routing, and cost tracking.
- `offline-mode`: Graceful degradation when no cloud API keys are configured, allowing the system to operate with local models only.

### Modified Capabilities
- `llm-provider`: Fallback chain expands from 2 providers (OpenAI → Anthropic) to 4 tiers (local → Google → Anthropic → OpenAI). Provider detection, cost estimation, and dispatch logic extend to support Ollama and Google. Structured completion primitive must work with local models via instructor.
- `platform-runtime`: Configuration adds `GOOGLE_API_KEY`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `EMBEDDING_MODEL`. API key validation allows all keys to be empty for offline mode. Docker Compose adds the Ollama service with GPU support.
- `redis-cache`: Semantic cache vectorizer switches from `OpenAITextVectorizer` to a local embedding vectorizer wrapping Ollama's `/api/embed` endpoint. Vector dimension changes from 1536 to 768 (nomic-embed-text).

## Impact

- **`engine/app/config.py`**: New settings, relaxed API key validation.
- **`engine/app/services/llm_wrapper.py`**: Router expanded to 4 deployments, `_dispatch()` and `_provider_from_model()` extended, `MODEL_COSTS` updated.
- **`engine/app/cache/semantic.py`**: `OpenAITextVectorizer` replaced with Ollama-backed vectorizer; Redis index dimension changes.
- **`engine/app/dependencies.py`**: LLMWrapper initialization accepts new parameters (Google API key, Ollama base URL).
- **`engine/docker-compose.yml`**: New `ollama` service, updated `api` service dependencies and environment.
- **`engine/.env.example`**: New variables documented.
- **`engine/tests/`**: Tests updated for 4-tier fallback semantics, local model mocking, offline mode.
- **Breaking**: Semantic cache index must be rebuilt (vector dimension change). Existing cached entries become invalid.
