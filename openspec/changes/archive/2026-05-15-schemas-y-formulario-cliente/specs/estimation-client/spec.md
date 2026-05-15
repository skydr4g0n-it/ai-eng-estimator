## ADDED Requirements

### Requirement: Streamlit form client for estimation

The system SHALL provide a Streamlit application outside the `engine/` tree that collects `description`, `project_type`, `detail_level`, and `output_format`, wraps submission in `st.form`, and on successful submit sends an HTTP `POST` with `Content-Type: application/json` to the configured estimator base URL joined with `/api/v1/estimate`, with a JSON body matching the engine’s `EstimationRequest` field names and enum string values.

#### Scenario: Form submit calls the estimate API

- **WHEN** the user fills all required fields and submits the form
- **THEN** the client issues `POST` with a JSON body containing `description`, `project_type`, `detail_level`, and `output_format` and displays the response `text` (or a clear error message on non-2xx)

#### Scenario: No chat-style free-text loop as primary UX

- **WHEN** the user opens the application
- **THEN** the primary interaction is the structured form, not a multi-turn chat transcript input

### Requirement: Client configuration

The Streamlit client SHALL read the engine base URL from environment configuration (documented in the client README) so deployments can point at local or remote engines without code changes.

#### Scenario: Missing base URL fails gracefully

- **WHEN** the base URL is unset or invalid
- **THEN** the app shows an actionable configuration error instead of an unhandled exception
