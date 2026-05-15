## 1. Engine schemas and configuration

- [x] 1.1 Add `ProjectType`, `DetailLevel`, `OutputFormat` enums and replace synchronous `EstimationRequest` / `EstimationResponse` in `engine/app/schemas/estimation.py` per spec (keep streaming models separate or clearly named to avoid import collisions).
- [x] 1.2 Add **`jinja2`** to `engine/pyproject.toml` and lock/install as required by the project toolchain.
- [x] 1.3 Wire `prompt_version` (e.g. return `"v1"` when rendering `estimation/v1/`) via config or constants aligned with the loader’s `version` parameter.
- [x] 1.4 Update `engine/app/schemas/__init__.py` exports if the public import surface changes.

## 2. Prompts and loader

- [x] 2.1 Create `engine/app/prompts/loader.py` with `render_estimation_prompt(request, version="v1") -> tuple[str, str]` using Jinja2 `Environment(undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)` and a `FileSystemLoader` (or package loader) rooted at `app/prompts` so `version` selects `estimation/<version>/`.
- [x] 2.2 Add `engine/app/prompts/estimation/v1/system.j2`, `user.j2`, and `examples.j2`: conditionals for `output_format` and `detail_level`; `system.j2` includes `examples.j2`; `examples.j2` contains 2–3 invented few-shot examples; `user.j2` wraps `description` in `<project_description>` **or** `## Project description` (one convention only).
- [x] 2.3 Ensure template package data is included in builds (e.g. `MANIFEST.in` / `pyproject` package-data) if needed so `.j2` files ship with the app.

## 3. Engine service and router

- [x] 3.1 Extend `engine/app/services/llm_wrapper.py` (or equivalent) minimally so the synchronous completion accepts **system** and **user** strings as separate chat roles without concatenating them into one message; keep LiteLLM/session-03 behavior for the rest.
- [x] 3.2 Update `engine/app/services/llm_service.py` (or the sync entrypoint) to call `render_estimation_prompt`, then invoke the wrapper with the two messages; map result to plain `text` for `EstimationResponse`.
- [x] 3.3 Update `engine/app/routers/estimations.py` `POST /estimate` to use the new request model, call the service above, return `text` + `prompt_version` (e.g. `"v1"`), and strip legacy response fields (usage, validation, cache, etc.).
- [x] 3.4 Remove or bypass structural evaluation on the sync path to match the removed spec requirement; delete dead imports if any.
- [x] 3.5 Revisit Redis cache key construction in `engine/app/services/cache.py` (and call sites) for compatibility with the new request shape.

## 4. Engine tests and docs

- [x] 4.1 Add `engine/tests/prompts/test_estimation_v1.py` with **at least three** pure unit tests on `render_estimation_prompt`: (a) rendered user (or full render) contains literal `description` inside the chosen wrapper; (b) `phases_table` vs `narrative` keyword presence in system per proposal; (c) `detailed` includes “assumptions per phase” instruction and `summary` does not—no HTTP or LLM calls.
- [x] 4.2 Rewrite `engine/tests/test_estimate_endpoint.py` for the new JSON body and response shape (422 on short `description`, 200 with `text` + `prompt_version`).
- [x] 4.3 Adjust `engine/tests/conftest.py` and any other tests that import old schema fields (`transcription`, `evaluate`, rich response).
- [x] 4.4 Update `engine/README.md` API example for `POST /api/v1/estimate`, Jinja prompt layout, dual-message behavior, default model suggestions, and breaking change vs prior transcription API.

## 5. Streamlit client

- [x] 5.1 Create `client/` (or agreed folder) with dependency file (`pyproject.toml` or `requirements.txt`) including `streamlit`, `httpx`, and optionally `pydantic` for client-side models.
- [x] 5.2 Implement `st.form` UI: multiline `description`, selects for the three enums, submit → build request dict / `EstimationRequest` → `POST` to `{ESTIMATOR_API_BASE_URL}/api/v1/estimate`, display `text` (and errors).
- [x] 5.3 Add `client/README.md` with env var, run command (`streamlit run ...`), and parity notes with engine enums.

## 6. Verification

- [x] 6.1 From `engine/`, run `docker compose run --rm tests` (or equivalent CI command) and fix failures until green.
- [x] 6.2 Manual smoke: run engine locally, run Streamlit client against it, submit a valid form and confirm rendered `text`.
