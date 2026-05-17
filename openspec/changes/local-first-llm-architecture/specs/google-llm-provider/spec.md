## ADDED Requirements

### Requirement: Google Gemini as cloud fallback provider

The system SHALL support Google Gemini as a cloud LLM provider via LiteLLM. The system SHALL accept a `GOOGLE_API_KEY` configuration variable and route Gemini completion requests through LiteLLM using the `gemini/` model prefix (e.g., `gemini/gemini-2.5-flash`). The Gemini provider SHALL be registered as the second deployment in the LiteLLM Router's `model_list` under `model_name: "estimator"`, positioned after the local Ollama deployment and before Anthropic. The system SHALL allow the Gemini model to be configured via the `PRIMARY_MODEL` or a dedicated `GOOGLE_MODEL` environment variable.

#### Scenario: Gemini handles fallback completion

- **WHEN** the local Ollama provider is unreachable and a completion request is made
- **THEN** the LiteLLM Router falls through to the Gemini deployment and returns a successful response if the Gemini API is available

#### Scenario: Gemini completion reports cost

- **WHEN** a completion is performed via the Gemini provider
- **THEN** the response metadata includes `provider: "google"` (or `"gemini"`), token usage counts, and an estimated `cost_usd` derived from documented Gemini per-model rates

#### Scenario: Missing Google API key skips Gemini deployment

- **WHEN** `GOOGLE_API_KEY` is not set or empty
- **THEN** the Gemini deployment is either not registered in the Router or is skipped during fallback, and the chain proceeds to the next available provider

### Requirement: Gemini pricing in cost tracking

The `MODEL_COSTS` dictionary in `app/services/llm_wrapper.py` SHALL include entries for supported Gemini models (at minimum `gemini-2.5-flash`) with documented input and output pricing per 1M tokens. The `_provider_from_model` function SHALL return `"google"` for model identifiers starting with `"gemini/"` or `"gemini-"`.

#### Scenario: Gemini cost is calculated correctly

- **WHEN** a Gemini completion uses 1000 input tokens and 500 output tokens
- **THEN** the estimated `cost_usd` is calculated using the documented Gemini pricing rates
