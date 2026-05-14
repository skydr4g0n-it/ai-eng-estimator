## MODIFIED Requirements

### Requirement: Synchronous estimation endpoint

The system SHALL expose `POST /api/v1/estimate` accepting a JSON body validated by Pydantic v2 with: `description` (string, minimum length 20, maximum length 2000), `project_type` (enum: `mobile_app`, `web_saas`, `internal_tool`, `data_pipeline`), `detail_level` (enum: `summary`, `medium`, `detailed`), and `output_format` (enum: `phases_table`, `line_items`, `narrative`). Before calling the LLM, the system SHALL render `(system, user)` via `render_estimation_prompt` (default template version `v1`) and SHALL invoke the LLM with those strings as **separate** system and user chat roles through the existing provider wrapper. The HTTP 200 response body SHALL be JSON with exactly `text` (non-empty string: the generated estimation content) and `prompt_version` (non-empty string identifying the prompt template pack, e.g. `v1` when using `estimation/v1/`). On LLM or internal service failure after retries, the API SHALL return HTTP 500 with a safe error detail and MUST NOT log full `description` content by default.

#### Scenario: Successful estimation

- **WHEN** a valid request is submitted and the LLM returns complete generated content
- **THEN** the HTTP response is 200 with `text` populated and `prompt_version` populated

#### Scenario: Validation error on bad payload

- **WHEN** the client sends a body that fails Pydantic validation (e.g. `description` shorter than 20 characters or unknown enum value)
- **THEN** the API returns HTTP 422 with validation error details

#### Scenario: LLM failure surfaces as server error

- **WHEN** the LLM layer raises a service-level error after retries and fallback logic have been applied
- **THEN** the API returns HTTP 500 with a safe error detail string and structured logs capture the failure class without logging full descriptions by default

## REMOVED Requirements

### Requirement: Structural evaluation

**Reason:** The synchronous response contract for this iteration no longer exposes structural validation results or evaluation toggles on the public schema.

**Migration:** A future change may reintroduce quality scoring as optional fields or a separate endpoint once the response model is structured beyond free-form `text`.

## ADDED Requirements

### Requirement: Jinja prompt rendering for synchronous estimate

The system SHALL render synchronous estimation prompts using versioned Jinja2 templates under `app/prompts/estimation/<version>/` named `system.j2`, `user.j2`, and `examples.j2`. The system SHALL provide `render_estimation_prompt(request, version="v1") -> tuple[str, str]` using a Jinja2 `Environment` configured with `undefined=StrictUndefined`, `trim_blocks=True`, and `lstrip_blocks=True`. The `system.j2` template SHALL include conditional guidance based on `output_format` and `detail_level`, and SHALL include `examples.j2` via Jinja `include`. The `user.j2` template SHALL wrap the request `description` in a single documented convention (either XML-style `<project_description>` or Markdown `## Project description`). The `examples.j2` template SHALL contain two or three invented few-shot estimation examples.

#### Scenario: Version selects template directory

- **WHEN** `render_estimation_prompt` is invoked with `version="v1"`
- **THEN** templates are resolved from `app/prompts/estimation/v1/`

### Requirement: Dual-role messages to the LLM provider stack

For `POST /api/v1/estimate`, the system SHALL pass rendered `system` and `user` strings to the existing session-03 LLM wrapper as **separate** chat roles (`system` and `user`). The system SHALL NOT implement this path by concatenating system and user into a single user-only message.

#### Scenario: Successful call uses two messages

- **WHEN** a valid synchronous estimation request is processed
- **THEN** the completion layer receives distinct system and user message bodies matching the output of `render_estimation_prompt`

### Requirement: Offline unit tests for estimation templates

The system SHALL ship unit tests (e.g. under `engine/tests/prompts/test_estimation_v1.py`) that exercise `render_estimation_prompt` only, with **no** outbound HTTP calls and **no** live LLM calls. The tests SHALL assert at minimum that: (1) the request `description` appears literally inside the project-description wrapper emitted by rendering; (2) when `output_format` is `phases_table`, the rendered **system** string contains an agreed phases-table format keyword used in template instructions, and when `output_format` is `narrative`, that keyword does not appear in the **system** string; (3) when `detail_level` is `detailed`, the **system** string includes the extra instruction to list assumptions per phase, and when `detail_level` is `summary`, that instruction does not appear.

#### Scenario: Prompt tests complete without network

- **WHEN** the test runner executes the estimation prompt template tests
- **THEN** those tests pass without requiring external API connectivity
