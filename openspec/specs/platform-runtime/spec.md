# platform-runtime Specification

## Purpose
TBD - created by archiving change sync-engine-with-session3-live. Update Purpose after archive.
## Requirements
### Requirement: Structured application logging

The system SHALL configure **structlog** at application startup with ISO timestamps, log level, and stack/excinfo processors. In production environment mode the renderer SHALL emit JSON logs; in non-production modes the renderer SHALL use a human-readable console renderer.

#### Scenario: Startup emits structured application event

- **WHEN** the FastAPI application completes startup after logging configuration
- **THEN** at least one structured log event records the active `APP_ENV` and indicates the application has started

### Requirement: Health endpoint metadata

The system SHALL expose `GET /health` returning JSON with service health status, a semantic version string, and the active `APP_ENV` value suitable for orchestration probes.

#### Scenario: Health check for compose

- **WHEN** an unauthenticated client calls `GET /health`
- **THEN** the response status is 200 and the JSON includes `status`, `version`, and `environment` keys populated from configuration

### Requirement: Containerized runtime with Redis

The primary Docker Compose definition under `engine/` SHALL define the API service and a Redis service with health checks, override `REDIS_URL` inside the API container to the in-network Redis host, and declare an explicit dependency so the API starts after Redis is healthy.

#### Scenario: Developer stack matches production-like wiring

- **WHEN** a developer runs `docker compose up` from `engine/` with a valid `.env` providing API keys
- **THEN** the API process can open Redis using `REDIS_URL` and serve `/docs` and `/api/v1` routes without manual extra containers beyond Compose

### Requirement: Continuous integration with Redis

The CI workflow for the engine SHALL run automated tests in an environment where Redis is reachable at the `REDIS_URL` supplied to the job (for example via a service container or compose profile), and SHALL NOT install or invoke Streamlit.

#### Scenario: CI exports Redis to tests

- **WHEN** CI executes the test suite on a pull request
- **THEN** jobs configure `REDIS_URL` to a running Redis instance and the test command completes without requiring Streamlit or manual Redis startup outside the workflow definition

