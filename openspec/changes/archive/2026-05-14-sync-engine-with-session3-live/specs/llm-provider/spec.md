## ADDED Requirements

### Requirement: LiteLLM-backed generation

The system SHALL perform all LLM completions for estimations through **LiteLLM**, using a dedicated wrapper component that supports a configured primary model, a configured fallback model, bounded retries, a request timeout, and structured logging of outcomes. The system SHALL NOT use direct `openai` or `anthropic` Python SDK clients for completion calls in the application layer after this change.

#### Scenario: Primary model succeeds

- **WHEN** a completion is requested and the primary model returns a successful response within the configured timeout
- **THEN** the response metadata includes the resolved model identifier, inferred provider, token usage counts, and an estimated USD cost derived from documented per-model rates

#### Scenario: Fallback after primary failure

- **WHEN** the primary model fails in a way that triggers fallback policy (as implemented in the wrapper)
- **THEN** the system attempts the fallback model with the appropriate API key and returns a successful estimation if the fallback succeeds, with metadata reflecting the model actually used

#### Scenario: Per-request model override

- **WHEN** the API client supplies an explicit `model` override on the sync or streaming estimation endpoint
- **THEN** the wrapper invokes LiteLLM for that model directly (bypassing the default router fallback semantics) while still honoring timeout, retries where applicable, and cache key inputs consistent with the reference implementation

### Requirement: Streaming completion primitive

The system SHALL expose a blocking iterator-style streaming primitive from the LLM wrapper that yields text chunks suitable for wrapping in Server-Sent Events, without leaking two-phase preprocessing intermediate outputs on the streaming path.

#### Scenario: Stream yields terminal chunks

- **WHEN** the streaming primitive is consumed until exhaustion for a valid prompt
- **THEN** the concatenation of non-empty chunks equals the full generated text for that call and the consumer can detect completion without hanging after the final chunk
