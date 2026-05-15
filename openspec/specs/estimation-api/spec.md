# estimation-api Specification

## Purpose
Defines the synchronous estimation HTTP API, prompt rendering contract, and provider-call behavior for form-driven project estimates.
## Requirements
### Requirement: Synchronous estimation endpoint

The system SHALL expose `POST /api/v1/estimate` accepting a JSON body validated by Pydantic v2 with: `description` (string, minimum length 20, maximum length 2000), `project_type` (enum: `mobile_app`, `web_saas`, `internal_tool`, `data_pipeline`), `detail_level` (enum: `summary`, `medium`, `detailed`), `output_format` (enum: `phases_table`, `line_items`, `narrative`), and optional `reference_projects` (`list[ReferenceProject] | None`). The endpoint SHALL accept an optional `prompt_version` query parameter; omitted values SHALL use the configured default prompt version, and supported values SHALL include `v1` and `v2`. Unsupported prompt versions SHALL return HTTP 422 with a clear response body naming the unsupported version and supported versions. Before calling the LLM, the system SHALL render `(system, user)` via `render_estimation_prompt` using the selected template version and SHALL invoke the LLM with those strings as separate system and user chat roles through the existing provider wrapper. The HTTP 200 response body SHALL be exactly `EstimationResponse` with `result: EstimationResult` and `prompt_version: str`. On guardrail input rejection the API SHALL return a clear client error response. On LLM or internal service failure after retries, the API SHALL return a safe error detail and MUST NOT log full `description` or `reference_projects` content by default.

#### Scenario: Successful estimation

- **WHEN** a valid request is submitted and the LLM returns structured content that passes output validation
- **THEN** the HTTP response is 200 with `result` populated and `prompt_version` equal to the selected prompt version

#### Scenario: Output format does not change response schema

- **WHEN** valid requests differ only by `output_format`
- **THEN** each successful response uses the same `EstimationResponse(result: EstimationResult, prompt_version: str)` schema, while `output_format` only influences prompt guidance and cache bucket identity

#### Scenario: Validation error on bad payload

- **WHEN** the client sends a body that fails Pydantic validation (e.g. `description` shorter than 20 characters, unknown enum value, or malformed `reference_projects`)
- **THEN** the API returns HTTP 422 with validation error details

#### Scenario: Unsupported prompt version

- **WHEN** the client calls `POST /api/v1/estimate?prompt_version=v999`
- **THEN** the API returns HTTP 422 with a response body that clearly states `v999` is unsupported and identifies the supported prompt versions

#### Scenario: LLM failure surfaces as server error

- **WHEN** the LLM layer raises a service-level error after retries and fallback logic have been applied
- **THEN** the API returns a safe server error response and structured logs capture the failure class without logging full descriptions, reference project details, or rendered prompts by default

### Requirement: Jinja prompt rendering for synchronous estimate

The system SHALL render synchronous estimation prompts using versioned Jinja2 templates under `app/prompts/estimation/<version>/` named `system.j2`, `user.j2`, and `examples.j2`. The system SHALL provide `render_estimation_prompt(request, version="v1") -> tuple[str, str]` using a Jinja2 `Environment` configured with `undefined=StrictUndefined`, `trim_blocks=True`, and `lstrip_blocks=True`. The `v1` and `v2` directories SHALL exist side by side; `v2` SHALL deliberately vary tone only and SHALL NOT remove required request variables or structured-output instructions. The `system.j2` template SHALL include conditional guidance based on `output_format` and `detail_level`, but this guidance SHALL only influence the richness of `summary` and `Phase.assumptions`; the service output schema SHALL remain `EstimationResult` for every `output_format`. The `system.j2` template SHALL include `examples.j2` via Jinja `include`. The `user.j2` template SHALL wrap the request `description` in a single documented convention (either XML-style `<project_description>` or Markdown `## Project description`) and SHALL render `reference_projects` with a Jinja `{% for %}` loop when present. Each render SHALL emit a structlog event containing the selected prompt version and a SHA-256 hash of the rendered content, without logging full prompt text or user-provided descriptions.

#### Scenario: Version selects template directory

- **WHEN** `render_estimation_prompt` is invoked with `version="v2"`
- **THEN** templates are resolved from `app/prompts/estimation/v2/`

#### Scenario: Reference projects render when present

- **WHEN** `render_estimation_prompt` receives a request with two `reference_projects`
- **THEN** the rendered user prompt includes a reference-projects section with both projects represented through template iteration

#### Scenario: Reference projects omitted when absent

- **WHEN** `render_estimation_prompt` receives a request without `reference_projects`
- **THEN** the rendered prompt omits the reference-projects section without raising a template error

#### Scenario: Prompt render is logged by hash

- **WHEN** `render_estimation_prompt` completes successfully
- **THEN** a structured `prompt_rendered` event records `prompt_version` and a content hash while excluding full rendered prompt content

### Requirement: Dual-role messages to the LLM provider stack

For `POST /api/v1/estimate`, the system SHALL pass rendered `system` and `user` strings to the existing session-03 LLM wrapper as separate chat roles (`system` and `user`). The system SHALL NOT implement this path by concatenating system and user into a single user-only message.

#### Scenario: Successful call uses two messages

- **WHEN** a valid synchronous estimation request is processed
- **THEN** the completion layer receives distinct system and user message bodies matching the output of `render_estimation_prompt`

### Requirement: Offline unit tests for estimation templates

The system SHALL ship unit tests (e.g. under `engine/tests/prompts/test_estimation_v1.py` and corresponding `v2` coverage) that exercise `render_estimation_prompt` only, with no outbound HTTP calls and no live LLM calls. The tests SHALL assert at minimum that: (1) the request `description` appears literally inside the project-description wrapper emitted by rendering; (2) `output_format` changes prompt guidance but does not change the required `EstimationResult` schema; (3) when `detail_level` is `detailed`, the system string includes the extra instruction to list assumptions per phase, and when `detail_level` is `summary`, that instruction does not appear; (4) `v2` is renderable as a sibling prompt pack and includes the tone variation; and (5) `reference_projects` render through template iteration when present.

#### Scenario: Prompt tests complete without network

- **WHEN** the test runner executes the estimation prompt template tests
- **THEN** those tests pass without requiring external API connectivity

### Requirement: Reference project schema

The system SHALL define a `ReferenceProject` schema that can be used inside `EstimationRequest.reference_projects`. Each reference project SHALL include enough structured context to influence estimation without relying on unbounded prose: a name, project type or domain label, short description, comparable scope notes, total hours or total cost where known, and optional lessons or caveats. Field lengths and numeric ranges SHALL be validated to prevent oversized prompt injection through reference context.

#### Scenario: Valid reference project accepted

- **WHEN** a request includes a valid `reference_projects` list with comparable project context
- **THEN** Pydantic validation accepts the payload and the prompt renderer receives the projects as structured data

#### Scenario: Oversized reference project rejected

- **WHEN** a request includes a reference project with text fields exceeding configured limits
- **THEN** the API returns HTTP 422 before rendering prompts or calling the LLM

### Requirement: Structured estimation response

The synchronous estimation path SHALL return a validated structured result rather than raw free-form text. The response SHALL be `EstimationResponse(result: EstimationResult, prompt_version: str)`. `EstimationResult` SHALL include `summary: str`, `total_duration_weeks: int = Field(ge=1)`, `total_cost_eur: int = Field(ge=0)`, `confidence_pct: int = Field(ge=0, le=100)`, and `phases: list[Phase]`. `Phase` SHALL include `name: str`, `duration_weeks: int = Field(ge=1, le=52)`, `cost_eur: int = Field(ge=0)`, `confidence_pct: int = Field(ge=0, le=100)`, and `assumptions: list[str]`. The result SHALL include a Pydantic `model_validator(mode="after")` equivalent to `total_must_match_sum_of_phases`: summed phase weeks MUST match `total_duration_weeks` within an absolute tolerance of 1 week, and summed phase cost MUST match `total_cost_eur` within 5% relative tolerance. Implementations MUST handle `total_cost_eur == 0` without division-by-zero errors.

#### Scenario: Valid structured output returned

- **WHEN** the LLM returns JSON matching the structured result schema and all business validators pass
- **THEN** the endpoint returns that result in the response body and stores it only after validation succeeds

#### Scenario: Invalid total cost rejected

- **WHEN** the LLM returns phase costs whose sum differs from `total_cost_eur` by more than 5%
- **THEN** output validation fails and the structured LLM retry path is invoked up to the configured limit

#### Scenario: Invalid total duration rejected

- **WHEN** the LLM returns phase durations whose sum differs from `total_duration_weeks` by more than 1 week
- **THEN** output validation fails and the structured LLM retry path is invoked up to the configured limit

#### Scenario: Schema contract test catches total mismatch

- **WHEN** a unit test creates an `EstimationResult` whose phases cost 12000 EUR but whose `total_cost_eur` is 10000 EUR
- **THEN** Pydantic validation raises an error before any LLM call is involved

### Requirement: Estimation guardrails

The synchronous estimation pipeline SHALL run input and output guardrails before returning a response. Input guardrails SHALL include Guardrails AI validation and domain-specific checks for moderation policy violations, prompt-injection-like instructions, and obvious PII such as email addresses, phone numbers, or IBANs. Output guardrails SHALL include Guardrails AI validation and domain-specific checks for structured schema validity, total consistency, phase confidence values, and safe handling of insufficiently specified estimates. Guardrail failures SHALL be logged with reason codes but MUST NOT log full user descriptions, reference project details, or rendered prompts.

#### Scenario: Prompt injection blocked

- **WHEN** the request description includes instruction-like text such as attempts to ignore previous instructions
- **THEN** the pipeline rejects the request before cache lookup, prompt rendering, or LLM invocation

#### Scenario: PII blocked

- **WHEN** the request description or reference project content contains obvious PII matched by configured checks
- **THEN** the pipeline rejects the request before cache lookup, prompt rendering, or LLM invocation

#### Scenario: Output guardrail prevents unsafe cache write

- **WHEN** the LLM output fails structured validation or output guardrails after all retries
- **THEN** the pipeline returns a safe error response and does not write the failed output to exact or semantic caches

