## MODIFIED Requirements

### Requirement: Semantic cache with local embeddings

The semantic cache SHALL use local embeddings from Ollama instead of OpenAI's embedding API. The vectorizer implementation SHALL call Ollama's `/api/embed` endpoint with the configured `EMBEDDING_MODEL` (default `nomic-embed-text`) and return the embedding vector for similarity matching. The vector dimension SHALL be 768 (matching `nomic-embed-text` output), replacing the previous 1536-dimensional OpenAI `text-embedding-3-small` vectors.

The `SemanticEstimationCache` initialization SHALL accept a vectorizer that implements an `embed(text: str) -> list[float]` interface, decoupling the embedding provider from the cache implementation. When the Ollama embedding endpoint is unreachable, the semantic cache SHALL degrade gracefully by returning `None` for cache lookups and silently skipping cache writes, preserving exact-match cache behavior.

#### Scenario: Semantic cache stores with local embedding

- **WHEN** a validated estimation result is stored in the semantic cache
- **THEN** the prompt text is embedded via Ollama's `/api/embed` endpoint and the result is indexed in Redis with the 768-dimensional vector

#### Scenario: Semantic cache lookup with local embedding

- **WHEN** a new estimation request is submitted and a semantically similar request exists in the cache
- **THEN** the cache returns the cached result if the similarity score exceeds the configured threshold

#### Scenario: Ollama embedding unavailable degrades gracefully

- **WHEN** the Ollama instance is unreachable during a semantic cache operation
- **THEN** the cache operation is skipped with a structured warning log, and the estimation proceeds without semantic caching
