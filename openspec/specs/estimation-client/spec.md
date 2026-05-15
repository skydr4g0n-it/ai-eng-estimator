# estimation-client Specification

## Purpose
Defines the Streamlit client, client-side tooling, and model synchronization path for the estimator UI.

## Requirements

### Requirement: Streamlit form client for estimation

The system SHALL provide a Streamlit application outside the `engine/` tree that collects `description`, `project_type`, `detail_level`, and `output_format`, wraps submission in `st.form`, and on successful submit sends an HTTP `POST` with `Content-Type: application/json` to the configured estimator base URL joined with `/api/v1/estimate`, with a JSON body matching the engine's `EstimationRequest` field names and enum string values.

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

### Requirement: Client uses modern Python tooling with uv and pyproject.toml

The system SHALL use `uv` for dependency management and a `pyproject.toml` file to declare dependencies, scripts, and build configuration for the client project.

#### Scenario: Install dependencies with uv

- **WHEN** a developer runs `uv sync` in the client directory
- **THEN** `uv` resolves and installs all dependencies according to the lockfile, ensuring reproducible environments.

### Requirement: Automatic synchronization of Pydantic models from engine to client

The system SHALL provide a script that exports Pydantic model definitions from the engine package and generates corresponding model files in the client package, keeping them in sync.

#### Scenario: Export models via sync script

- **WHEN** the synchronization script `scripts/export_models.py` is executed
- **THEN** it reads the engine's Pydantic model definitions and writes up-to-date `client/models.py` (or a package) reflecting any changes.
