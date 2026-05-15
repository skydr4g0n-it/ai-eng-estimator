## ADDED Requirements

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
