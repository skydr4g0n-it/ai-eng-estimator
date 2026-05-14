# estimation-api Specification

## Purpose
TBD - created by archiving change sync-engine-with-session3-live. Update Purpose after archive.
## Requirements
### Requirement: Synchronous estimation endpoint

The system SHALL expose `POST /api/v1/estimate` accepting a meeting transcription of minimum length and optional generation controls (`preprocessing`, `example_format`, `num_examples`, `use_examples`, `model`, `max_tokens`, `thinking_budget`, `evaluate`). The response SHALL include the markdown estimation, model and provider metadata, token usage split (including optional preprocessing token fields when applicable), finish reason, server-side latency in milliseconds, preprocessing mode, optional phase-one extracted requirements when `two_phase` preprocessing is used, optional structural validation results, `cache_hit`, and `cost_usd`.

#### Scenario: Successful estimation with validation

- **WHEN** a valid request is submitted with `evaluate` true and the LLM returns a complete estimation
- **THEN** the HTTP response is 200 with an `EstimationResponse`-shaped body containing a non-empty `estimation` string and a populated `validation` object with scoring fields consistent with the structural evaluator

#### Scenario: LLM failure surfaces as server error

- **WHEN** the LLM layer raises a service-level error after retries and fallback logic have been applied
- **THEN** the API returns HTTP 500 with a safe error detail string and structured logs capture the failure class without logging full transcriptions by default

### Requirement: Structural evaluation

The system SHALL provide a pure-Python structural evaluator that inspects the generated markdown for expected sections (title, task breakdown table, totals, team, duration), compares declared totals to table aggregates within configured tolerances, checks finish reason acceptability, computes a numeric score, and returns a list of human-readable issues.

#### Scenario: Evaluation skipped when disabled

- **WHEN** the client sets `evaluate` false on `POST /api/v1/estimate`
- **THEN** the response body contains `validation` null while still returning the estimation and usage metadata

