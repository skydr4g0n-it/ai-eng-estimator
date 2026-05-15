## Why

The synchronous estimation API today is tuned around a long meeting `transcription` plus many LLM tuning knobs, while the learning goal for this iteration is a **clear, typed contract** between a simple UI and the engine, and a **form-driven Streamlit client** that mirrors that contract. A shared Pydantic model set makes validation consistent on the wire and keeps the client aligned with the service.

## What Changes

- **BREAKING**: Replace the public `POST /api/v1/estimate` request body with structured fields: `description` (20–2000 chars), `project_type`, `detail_level`, and `output_format` (string enums as in the product brief), implemented with **Pydantic v2** in `engine/app/schemas/` (consolidate or extend the existing module per design—avoid a duplicate root `app/schemas.py` that diverges from the engine layout).
- **BREAKING**: Narrow the synchronous response to a minimal `EstimationResponse` with `text` and `prompt_version` for this iteration (free-form estimation text for now; richer structure deferred).
- Introduce a **Jinja2 prompt pack** and loader under the engine’s `app/` package (see **Prompt structure and loader** below); synchronous estimates **must not** assemble long prompt strings ad hoc in Python beyond what the templates require.
- Refactor the synchronous estimate route so it renders `(system, user)` and calls the **session-03 provider wrapper** with **two chat messages** (system + user), not a single concatenated user message; response includes `prompt_version` aligned with the template pack (e.g. `"v1"` when using `estimation/v1/`).
- Add **fast unit tests** for template rendering (no live LLM); see **Template unit tests** below.
- Add a **Streamlit** app (new package path under the repo, e.g. `client/` or `streamlit_app/` per design) that **replaces chat-style UX** with `st.form`: on submit, construct an `EstimationRequest`, `POST` to the engine’s estimate URL (full path `.../api/v1/estimate` unless a dedicated alias is added), and display returned `text`. Optional: reuse the same Pydantic models in the client via a shared module or duplicated definitions.
- Update tests and docs that assumed the old transcription-heavy request and rich response shape.

## Prompt structure and loader (IA service)

Create this layout **inside the engine service** (i.e. under `engine/app/` with imports as `app.prompts...`):

```text
app/
├── prompts/
│   ├── loader.py
│   └── estimation/
│       └── v1/
│           ├── system.j2
│           ├── user.j2
│           └── examples.j2
```

**system.j2** — Define the model role and general instructions; include **conditional** blocks driven by `output_format` (how to shape the answer) and by `detail_level` (how deep to go). Include **examples.j2** via `{% include ... %}` (path as appropriate for the Jinja environment’s loader).

**user.j2** — Wraps the end-user’s project **description** (the field from `EstimationRequest`).

**examples.j2** — **Two or three** plausible few-shot estimation examples, well formed for the task. Use **invented** project scenarios; do not copy text from any course handout or this proposal.

**loader.py** — Expose:

`render_estimation_prompt(request: EstimationRequest, version: str = "v1") -> tuple[str, str]`

returning `(system, user)` strings ready to send to the provider. Use Jinja2’s `Environment` with **`StrictUndefined`**, **`trim_blocks=True`**, and **`lstrip_blocks=True`**. Callers must be able to switch **template version** via the `version` argument (and matching subdirectory) without editing unrelated code paths.

Minimal Jinja reminder for implementers: `{{ var }}` interpolates; `{% if %}...{% endif %}` branches; `{% include "path" %}` pulls in another template.

## Endpoint refactor

For the synchronous **`POST /api/v1/estimate`** route (product shorthand “POST /estimate” means this mounted path):

1. Accept a JSON body validated as **`EstimationRequest`**.
2. Call **`render_estimation_prompt(request)`** (optionally passing `version` when wiring multiple packs) to obtain **`(system, user)`**.
3. Call the LLM through the **existing session-03 wrapper** with **separate** system and user messages (provider-native or chat-style messages with roles **`system`** and **`user`**), **not** one blob that merges system into user.
4. Return **`EstimationResponse`** with the generated **`text`** and **`prompt_version="v1"`** when serving the `v1` template pack.

**Default model suggestion** (config / env): `gpt-4o-mini` or `claude-haiku-4-5-20251001`.

## Template unit tests

Under the engine test suite, add **`engine/tests/prompts/test_estimation_v1.py`** (or the same layout your tree uses) with **at least three** tests that:

1. Assert the rendered output **literally includes** the request’s `description` inside the chosen wrapper convention—either **XML-style** `<project_description>...</project_description>` **or** a Markdown section **`## Project description`** (pick one in `user.j2` and assert consistently).
2. When **`output_format=phases_table`**, the **system** string contains an agreed **format keyword** present in the template instructions (e.g. `phases_table` or `confidence_pct` if the template uses it); when **`output_format=narrative`**, that keyword **must not** appear in the system string.
3. When **`detail_level=detailed`**, the **system** string includes the **extra instruction** to list **assumptions per phase**; when **`detail_level=summary`**, that instruction **must not** appear.

These tests must run in **milliseconds** and **must not** call external HTTP APIs or real LLMs—they validate **template rendering** only.

## Capabilities

### New Capabilities

- `estimation-client`: Streamlit form-based UI, environment configuration for API base URL, submit → JSON body → display response text; dependency and run instructions.

### Modified Capabilities

- `estimation-api`: Request validation rules, JSON schema on the wire, successful response shape, and error behavior for the synchronous estimate endpoint aligned with the new contract; remove or supersede requirements that mandate the old `transcription`-only body and full metadata response for this endpoint; require **Jinja-rendered** system/user prompts and a **dual-message** LLM invocation via the existing provider wrapper; `prompt_version` tied to the template pack (e.g. `v1`).

## Impact

- `engine/app/schemas/estimation.py`, `engine/app/prompts/**`, `engine/app/routers/estimations.py`, `engine/app/services/llm_service.py` and **`LLMWrapper`** (extend message API if needed so sync path passes system + user without concatenation), `engine/pyproject.toml` (**Jinja2** dependency), tests under `engine/tests/` including **`engine/tests/prompts/`**, CI (`docker compose run --rm tests`).
- New Streamlit dependency and entry script (location TBD in design); `engine/pyproject.toml` may gain a dependency group or remain engine-only with client in a sibling `pyproject.toml`.
- Caching keys and evaluation hooks may need redesign if they keyed on old request shape—called out in design/tasks.
