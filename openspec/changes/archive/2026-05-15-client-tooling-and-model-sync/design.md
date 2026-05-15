## Context

The client currently relies on a legacy `requirements.txt` and a manually duplicated `models.py`, causing friction and drift. The engine uses modern tooling (`uv`, `ruff`, `pyproject.toml`). Aligning the client improves consistency, installation speed, and linting.

## Goals / Non-Goals

**Goals:**
- Migrate the client to use `uv` and a `pyproject.toml` for dependency management.
- Configure `ruff` for linting/formatting to match the engine's standards.
- Provide an automated mechanism to keep Pydantic models in sync between engine and client.

**Non-Goals:**
- Refactor the client UI beyond the existing Streamlit form.
- Introduce new features unrelated to tooling or model sync.

## Decisions

1. **Package Manager:** Use `uv` (https://github.com/astral-sh/uv) for fast installation and deterministic lock files. `uv pip install -r requirements.txt` will be replaced with `uv sync`.
2. **Build System:** Adopt `pyproject.toml` with `build-system` using `hatchling` (or `setuptools`). This mirrors the engine's setup.
3. **Linting:** Configure `ruff` with the same rule set as the engine (`ruff.toml` at the repo root) and add a pre-commit hook.
4. **Model Synchronization:** Implement a small Python script `scripts/export_models.py` that imports the engine's Pydantic models and writes JSON schemas to the client package, which the client then loads via `pydantic.dataclasses.dataclass` conversion. This script will be part of the client repo and run as a post-install step.

## Risks / Trade-offs

- **Risk:** Developers may be unfamiliar with `uv`. *Mitigation:* Provide documentation and a one‑line command alias.
- **Risk:** Model export script adds a runtime dependency on the engine package. *Mitigation:* Pin the engine version and isolate the script.

## Migration Plan

1. Add `pyproject.toml` and `uv.lock` to the client repository.
2. Remove `requirements.txt` and update CI pipelines to use `uv sync`.
3. Add `ruff.toml` (copy from engine) and integrate with pre‑commit.
4. Add `scripts/export_models.py` and a post‑install hook (`[tool.uv.scripts] export-models = "scripts.export_models:main").
5. Run the export script locally and verify generated models match the engine.
6. Deploy and monitor for any migration issues.

## Open Questions

- Should the model export be a shared internal package or a script? (Decision pending based on deployment constraints.)
