# llm-provider Specification

## Purpose
TBD - created by archiving change sync-engine-with-session3-live. Update Purpose after archive.
## Requirements
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

### Requirement: Instructor structured completion primitive

The LLM wrapper SHALL expose an Instructor-backed structured completion primitive for synchronous estimations that accepts separate system and user messages, a Pydantic response model, optional model override, max token limit, and a bounded validation retry count. The primitive SHALL force the provider call to return JSON compatible with the supplied response model by using Instructor with `response_model=EstimationResult`, and SHALL return a validated model instance plus metadata including resolved model, inferred provider, and latency. The primitive SHALL retry invalid structured output up to 2 times for the estimation pipeline before raising a service-level error.

#### Scenario: Structured model succeeds

- **WHEN** the provider returns JSON matching the requested response model on the first attempt
- **THEN** the wrapper returns the validated Pydantic instance and metadata without invoking repair retries

#### Scenario: Structured model repairs invalid output

- **WHEN** the provider returns JSON that fails Pydantic or guardrail validation and then returns valid JSON within 2 retries
- **THEN** the wrapper returns the repaired validated result and logs structured retry metadata without logging full prompt contents

#### Scenario: Structured model exhausts retries

- **WHEN** the provider fails to produce output that validates against the response model within 2 retries
- **THEN** the wrapper raises a service-level error that the API layer can map to a safe error response

### Requirement: Instructor provider compatibility

The structured completion primitive SHALL preserve the existing LLM wrapper boundary and MUST NOT introduce direct ad hoc completion SDK calls in routers or prompt rendering code. Instructor SHALL be the component responsible for normalizing structured response handling across supported providers. If an explicit model override is supplied, the wrapper SHALL route the structured call consistently with existing override semantics. If no model override is supplied, the wrapper SHALL use the configured primary model and fallback strategy where the selected Instructor integration supports it.

#### Scenario: Router does not call SDK directly

- **WHEN** a synchronous estimation request requires structured output
- **THEN** the router delegates to service-layer code and the LLM wrapper performs the provider call

#### Scenario: Model override honored

- **WHEN** a structured completion is requested with an explicit supported model override
- **THEN** the wrapper calls the override model through the same provider boundary and records metadata for the resolved model

