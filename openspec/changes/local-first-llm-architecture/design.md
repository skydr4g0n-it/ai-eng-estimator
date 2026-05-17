## Context

The estimator engine currently uses a 2-provider LiteLLM Router: OpenAI (primary, `gpt-4o-mini`) and Anthropic (fallback, `claude-haiku-4-5`). All LLM calls flow through `LLMWrapper` in `app/services/llm_wrapper.py`, which manages the Router, exact-match cache, cost tracking, and structured logging. The semantic cache in `app/cache/semantic.py` uses `OpenAITextVectorizer` from RedisVL, creating a hard dependency on OpenAI's embedding API even when the completion model is Anthropic.

The Docker Compose stack defines two services: `redis` (with vector search) and `api` (FastAPI). No local inference service exists.

## Goals / Non-Goals

**Goals:**
- Make local LLM (Ollama/Qwen 2.5 14B) the default primary inference engine
- Add Google Gemini 2.5 Flash as first cloud fallback tier
- Expand fallback chain to 4 tiers: local → Google → Anthropic → OpenAI
- Enable fully offline operation when no cloud API keys are configured
- Replace OpenAI embeddings with local Ollama embeddings for the semantic cache
- Maintain backward compatibility — all existing endpoints, schemas, and behaviors preserved

**Non-Goals:**
- No changes to the streaming endpoint API contract or SSE format
- No changes to the synchronous estimation API request/response schema
- No changes to guardrails, prompt templates, or example data
- No vLLM, vLLM migration, or alternative inference engine support (Ollama only)
- No changes to the client (Streamlit app)
- No changes to evaluation/scoring logic

## Decisions

### D1: Ollama as the local inference engine

**Decision**: Use Ollama (not vLLM, LocalAI, or llama.cpp directly).

**Rationale**: The estimator is a low-concurrency, latency-sensitive service — one estimation request at a time. Ollama's simplicity (one command to pull and serve a model) outweighs vLLM's throughput advantages (continuous batching, PagedAttention), which matter at scale but not here. Ollama provides an OpenAI-compatible REST API that LiteLLM supports natively via the `ollama/` prefix, requiring minimal code changes.

**Alternatives considered**:
- vLLM: Higher throughput, more complex setup, better for production at scale. Overkill for this traffic pattern.
- LocalAI: Broader model support, heavier footprint.
- llama.cpp server: Manual quantization management, less user-friendly.

### D2: Qwen 2.5 14B at Q4_K_M as the local model

**Decision**: Default to `qwen2.5:14b` (Ollama tag, which maps to Q4_K_M quantization, 9.0 GB).

**Rationale**: On a 16 GB VRAM GPU (RTX 5080), Qwen 2.5 14B at Q4_K_M uses ~9 GB, leaving ~7 GB for the KV cache — sufficient for estimation prompts (~2-5K tokens). Qwen 2.5's documentation explicitly highlights "generating structured outputs, especially in JSON format" and "resilience to diverse system prompts," which directly matches the estimation pipeline's needs (instructor structured completions, varied prompt templates).

**Alternatives considered**:
- Llama 3.1 8B: Smaller (4.9 GB), better function calling, but less reasoning depth. Good fallback option if Qwen 2.5 14B has structured output issues.
- Qwen 2.5 7B: Faster, but noticeably weaker at estimation reasoning.
- Mistral Small 3.1 24B: Too large for 16 GB VRAM at Q4.

### D3: nomic-embed-text for local embeddings

**Decision**: Use Ollama's `nomic-embed-text` model (137M params, 768 dimensions) for the semantic cache.

**Rationale**: nomic-embed-text is Ollama's most popular embedding model, well-supported, and produces 768-dimensional vectors. While this is a dimension change from OpenAI's `text-embedding-3-small` (1536 dim), the semantic cache is isolated to Redis and the index will be rebuilt. The quality difference is acceptable for semantic similarity matching of estimation prompts.

**Alternatives considered**:
- `mxbai-embed-large`: 1024 dimensions, higher quality but slower and larger.
- `all-minilm`: 384 dimensions, fastest but lowest quality.
- Keep OpenAI embeddings: Simpler code change, but maintains OpenAI dependency.

### D4: LiteLLM Router with 4 deployments under one model group

**Decision**: All 4 providers are registered as deployments under the same `model_name: "estimator"` in the LiteLLM Router, with `fallbacks` configured to cascade through the chain.

**Rationale**: LiteLLM's Router automatically tries the next deployment when one fails if they share the same `model_name`. This keeps the `LLMWrapper` API unchanged — callers still call `router.completion(model="estimator")` and the Router handles provider selection and fallback internally.

The deployment order in `model_list` determines priority:
1. `ollama/qwen2.5:14b` (local, no API key, longer timeout)
2. `gemini/gemini-2.5-flash` (Google, cheap)
3. `anthropic/claude-haiku-4-5-20251001` (Anthropic, quality)
4. `gpt-4o-mini` (OpenAI, reliable last resort)

**Alternatives considered**:
- Separate model groups (`local`, `google`, `anthropic`, `openai`) with explicit fallback chains: More verbose, requires changes to all call sites.
- Weighted routing: Doesn't match the "try local first, fall through on failure" semantics.

### D5: Config validation allows all API keys to be empty

**Decision**: Remove the requirement that at least one of `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` must be set. All API keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`) may be empty for offline/local-only operation.

**Rationale**: The local Ollama provider requires no API key. Users who want fully offline operation should not need to configure any cloud credentials. The Router will skip deployments whose API keys are not configured (or the `api_base` is unreachable for local).

### D6: Semantic cache vectorizer replaced with custom Ollama wrapper

**Decision**: Replace `OpenAITextVectorizer` in `semantic.py` with a custom vectorizer class that calls Ollama's `/api/embed` endpoint via HTTP.

**Rationale**: RedisVL does not ship a built-in `OllamaTextVectorizer`. The Ollama embedding API is a simple HTTP POST to `/api/embed` with `{"model": "nomic-embed-text", "prompt": "..."}` returning a list of floats. A thin wrapper class implementing the same interface as `OpenAITextVectorizer` (an `embed(text: str) -> list[float]` method) is sufficient.

**Alternatives considered**:
- `HuggingFaceTextVectorizer`: Runs embeddings locally in Python, but requires downloading model weights and adds a Python dependency.
- Keep OpenAI embeddings: Maintains the OpenAI hard dependency we're trying to eliminate.

### D7: Docker Compose GPU passthrough via NVIDIA Container Toolkit

**Decision**: The `ollama` service uses `deploy.resources.reservations.devices` with `capabilities: [gpu]` for GPU passthrough.

**Rationale**: This is the standard Docker Compose v3+ syntax for GPU reservation. It requires the host to have the NVIDIA Container Toolkit installed. The RTX 5080 on the target machine supports this natively.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Qwen 2.5 14B fails instructor structured completions** — 14B models at Q4 may not reliably follow function-calling schemas, causing the synchronous `/api/v1/estimate` endpoint to exhaust retries and fall through to cloud providers. | Test structured output reliability early. If failure rate is high, consider swapping to Llama 3.1 8B for structured paths only, or increase `ESTIMATION_VALIDATION_RETRIES`. |
| **Semantic cache index invalidation** — Changing embedding dimensions from 1536 to 768 invalidates all existing cached entries. | Document this as a breaking change. The cache rebuilds naturally as new requests arrive. Add a startup warning if dimensions mismatch detected. |
| **Ollama cold start** — First request after container startup triggers model download (~9 GB) if not pre-pulled. | Add a healthcheck that verifies the model is loaded. Document `ollama pull qwen2.5:14b` as a pre-start step. Consider an init container for production. |
| **Local model latency** — Qwen 2.5 14B on RTX 5080 will be slower than cloud APIs (~25 tok/s vs ~100+ tok/s), increasing response times. | Set a higher timeout for the local deployment (120s vs 30s). The fallback chain ensures cloud providers respond if local is too slow. |
| **VRAM contention** — 9 GB for the model + KV cache + other GPU processes could cause OOM if the host runs other GPU workloads. | Document the GPU requirement. The Docker `deploy` reservation prevents other containers from using the GPU. |
| **LiteLLM Router fallback semantics** — LiteLLM's behavior when multiple deployments share a `model_name` may not guarantee strict priority ordering. | Test the fallback chain empirically. If ordering is unreliable, switch to separate model groups with explicit fallback chains. |
