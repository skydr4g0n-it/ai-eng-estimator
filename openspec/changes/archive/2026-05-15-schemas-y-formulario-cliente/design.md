## Context

The engine already exposes `POST /api/v1/estimate` with a transcription-centric `EstimationRequest` and a rich `EstimationResponse` (`estimation`, usage, latency, optional `validation`, cache, cost). A prior archive explicitly omitted Streamlit. This change introduces a **product-style typed request** (`description`, enums for project type, detail level, output format) and a **minimal JSON response** (`text`, `prompt_version`), plus a **Streamlit form client** that mirrors the request model.

## Goals / Non-Goals

**Goals:**

- Single source of truth for the wire contract in the engine using **Pydantic v2** (`BaseModel`, `Field`, `str` enums), living in `engine/app/schemas/` (extend `estimation.py` or split modules if clarity suffers—**do not** introduce a parallel `engine/app/schemas.py` that bypasses the existing package).
- Router validates with FastAPI + Pydantic; **prompt text** for the synchronous path is produced only via **`render_estimation_prompt(request, version=...)`** loading **`app/prompts/estimation/<version>/*.j2`** (Jinja2 `Environment` with `StrictUndefined`, `trim_blocks=True`, `lstrip_blocks=True`). The LLM is invoked with **two messages** (system + user) through the existing **`LLMWrapper`** / session-03 abstraction—no concatenation of system into a single user string.
- Streamlit UI: `st.form` with fields mapped 1:1 to the request; submit issues `POST` with JSON to `{API_BASE}/api/v1/estimate` (document base URL in `client` README and env, e.g. `ESTIMATOR_API_BASE_URL`).
- `prompt_version` in the HTTP response matches the template pack in use (initially **`"v1"`** when rendering `estimation/v1/`); config may override default **model** to `gpt-4o-mini` or `claude-haiku-4-5-20251001` per proposal.

**Non-Goals:**

- Changing the streaming endpoint contract (`POST /api/v1/estimate/stream`) beyond what is required for consistency (default: leave as-is unless tests force alignment).
- Returning token usage, cost, cache flags, or structural validation in the synchronous JSON response in this iteration.
- Dockerizing the Streamlit app (optional follow-up).

## Decisions

1. **Request model location** — Implement enums (`ProjectType`, `DetailLevel`, `OutputFormat`) and the new `EstimationRequest` / `EstimationResponse` in `engine/app/schemas/estimation.py` (or `engine/app/schemas/estimate_form.py` imported from `estimation.py` if file size warrants). **Rationale:** matches repo convention; avoids `app/schemas.py` at wrong path. **Alternative considered:** shared package for client+engine—rejected for minimal diff; client may duplicate or `pip install -e ../engine` if desired later.

2. **Backward compatibility** — **Breaking** replacement of the public sync body and response (per proposal). **Rationale:** course iteration prioritizes clarity over dual-stack endpoints. **Alternative:** `/v2` route—rejected unless apply phase reveals heavy external consumers (none documented).

3. **Jinja prompt packs** — Author `system.j2` (role, globals, `{% if %}` on `output_format` and `detail_level`, `{% include %}` for `examples.j2`), `user.j2` (wrap `description` in `<project_description>` **or** `## Project description`—pick one and document in tests), and `examples.j2` (2–3 invented few-shots). **loader.py** exposes `render_estimation_prompt(request, version="v1") -> tuple[str, str]`. **Rationale:** versioned prompts without Python string soup; `version` selects subdirectory. Add **`jinja2`** to `engine/pyproject.toml`.

4. **Dual-message provider call** — Extend `LLMWrapper` (or the sync completion helper) minimally so the sync path passes **system** and **user** as separate chat roles; keep LiteLLM/session-03 behavior otherwise. **Rationale:** matches proposal and provider APIs; only message assembly changes.

5. **Structural evaluation** — Omit from HTTP response; optionally skip calling the evaluator on the sync path to avoid dead code paths, or keep internal logging-only—pick one during implementation for simplicity. **Rationale:** user response schema has no `validation` field.

6. **Streamlit placement** — New directory at repo root, e.g. `client/` with its own `pyproject.toml` (or `requirements.txt`) listing `streamlit`, `httpx`, `pydantic`. **Rationale:** prior rule “do not add streamlit to engine” stays satisfied; engine remains deployable without UI deps. Workspace OpenSpec design rule emphasizes `engine/` for **service** paths; the UI is intentionally outside `engine/`.

7. **Client typing** — Prefer `from app.schemas.estimation import EstimationRequest` only if the client runs with `PYTHONPATH` including engine; otherwise duplicate minimal models in `client/models.py` with matching field names and constraints. **Rationale:** optional per user; document the chosen approach in `client/README.md`.

8. **Template regression tests** — Pure unit tests under `engine/tests/prompts/test_estimation_v1.py` assert render behavior (description wrapper, `phases_table` vs `narrative` keyword presence, `detailed` vs `summary` assumptions instruction); no network. **Rationale:** locks template contracts from proposal.

## Risks / Trade-offs

- **[Risk] Redis cache keys** assume old request fingerprint → **Mitigation:** invalidate or redefine cache key input to new fields; disable cache for sync path temporarily if collision risk is high during transition.
- **[Risk] Tests and CI** assert old JSON shapes → **Mitigation:** rewrite `test_estimate_endpoint.py` and fixtures in one pass.
- **[Risk] `min_length=20` on description** vs old `50` on transcription → **Mitigation:** document in README; adjust examples in tests.

## Migration Plan

1. Land schema + router + service + engine tests behind the breaking change in one change set (no dual schema in production spec).
2. Add `client/` with README: run `streamlit run app.py`, set base URL, example values meeting `min_length`.
3. Rollback: revert commit; no DB migrations.

## Open Questions

- Whether to keep `POST /api/v1/estimate/stream` accepting `transcription` only or align its body with the new form fields (defer unless course requires parity).
- Whether to reuse the same Jinja `v1` pack for streaming in a later iteration (deferred; synchronous path ships first).
