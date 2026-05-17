## MODIFIED Requirements

### Requirement: LiteLLM-backed generation

The system SHALL perform all LLM completions for estimations through **LiteLLM**, using a dedicated wrapper component that supports a configured primary model, a configured fallback model, bounded retries, a request timeout, and structured logging of outcomes. The system SHALL NOT use direct `openai` or `anthropic` Python SDK clients for completion calls in the application layer after this change.

The LiteLLM Router SHALL support a 4-tier fallback chain under `model_name: "estimator"`: local Ollama (primary), Google Gemini (first fallback), Anthropic (second fallback), and OpenAI (third fallback). Each deployment SHALL be configured with the appropriate API key or base URL, and the Router SHALL cascade through deployments in order when a provider fails. The local Ollama deployment SHALL use a longer timeout (default 120 seconds) to accommodate slower local inference, while cloud deployments SHALL use the standard configured timeout.

#### Scenario: Primary model succeeds

- **WHEN** a completion is requested and the primary model returns a successful response within the configured timeout
- **THEN** the response metadata includes the resolved model identifier, inferred provider, token usage counts, and an estimated USD cost derived from documented per-model rates

#### Scenario: Fallback after primary failure

- **WHEN** the primary model fails in a way that triggers fallback policy (as implemented in the wrapper)
- **THEN** the system attempts the next deployment in the fallback chain and returns a successful estimation if any deployment in the chain succeeds, with metadata reflecting the model actually used

#### Scenario: Full chain exhaustion

- **WHEN** all configured deployments in the fallback chain fail
- **THEN** the system raises a service-level error that the API layer maps to a safe error response

#### Scenario: Per-request model override

- **WHEN** the API client supplies an explicit `model` override on the sync or streaming estimation endpoint
- **THEN** the wrapper invokes LiteLLM for that model directly (bypassing the default router fallback semantics) while still honoring timeout, retries where applicable, and cache key inputs consistent with the reference implementation

### Requirement: Instructor provider compatibility

The structured completion primitive SHALL preserve the existing LLM wrapper boundary and MUST NOT introduce direct ad hoc completion SDK calls in routers or prompt rendering code. Instructor SHALL be the component responsible for normalizing structured response handling across supported providers. If an explicit model override is supplied, the wrapper SHALL route the structured call consistently with existing override semantics. If no model override is supplied, the wrapper SHALL use the configured primary model and fallback strategy where the selected Instructor integration supports it.

The structured completion primitive SHALL work with local Ollama models through the OpenAI-compatible API that Ollama exposes. If the local model fails to produce valid structured output within the configured retry limit, the primitive SHALL raise a service-level error, allowing the caller to handle the failure (e.g., by falling back to a cloud provider or returning an error response).

#### Scenario: Router does not call SDK directly

- **WHEN** a synchronous estimation request requires structured output
- **THEN** the router delegates to service-layer code and the LLM wrapper performs the provider call

#### Scenario: Model override honored

- **WHEN** a structured completion is requested with an explicit supported model override
- **THEN** the wrapper calls the override model through the same provider boundary and records metadata for the resolved model

#### Scenario: Local model structured output fails

- **WHEN** the local Ollama model fails to produce valid structured output within the retry limit
- **THEN** the wrapper raises a service-level error without attempting cloud fallback (structured completions do not use the Router fallback chain)
