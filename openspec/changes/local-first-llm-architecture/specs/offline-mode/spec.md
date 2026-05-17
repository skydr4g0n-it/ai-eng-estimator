## ADDED Requirements

### Requirement: Offline-only operation

The system SHALL operate fully when no cloud API keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`) are configured, using only the local Ollama provider for all LLM completions. The configuration validation in `app/config.py` SHALL NOT require any cloud API key to be set. When all cloud API keys are absent, the LiteLLM Router SHALL be configured with only the local Ollama deployment, and the fallback chain SHALL consist solely of the local provider.

#### Scenario: System starts with no cloud API keys

- **WHEN** the application starts with `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and `GOOGLE_API_KEY` all unset or empty
- **THEN** the application starts successfully without raising a configuration validation error

#### Scenario: Estimation succeeds with local provider only

- **WHEN** an estimation request is submitted with no cloud API keys configured and the Ollama instance is reachable
- **THEN** the estimation is completed using the local Ollama provider and returns a valid response

#### Scenario: Estimation fails gracefully when local provider is down

- **WHEN** an estimation request is submitted with no cloud API keys configured and the Ollama instance is unreachable
- **THEN** the system returns a clear error response indicating that no LLM provider is available

### Requirement: Offline test execution

The test suite SHALL run successfully in an environment with no cloud API keys configured, using fakes or mocks for all LLM providers. The `APP_ENV=test` configuration SHALL NOT require any API key to be set. Tests that specifically exercise fallback chain behavior SHALL use mocked providers to simulate multi-provider scenarios without requiring live API connectivity.

#### Scenario: Tests pass with zero API keys

- **WHEN** the test suite is executed with `APP_ENV=test` and no `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GOOGLE_API_KEY` set
- **THEN** all tests pass using mocked or fake LLM providers
