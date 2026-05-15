## 1. Project Setup

- [x] 1.1 Create a new branch `client-tooling-migration`
- [x] 1.2 Ensure local development environment has Python 3.11+ installed

## 2. Migrate to UV & pyproject.toml

- [x] 2.1 Install UV (`pip install uv`) if not already present
- [x] 2.2 Generate `pyproject.toml` from existing `requirements.txt` using `uv pip compile -r requirements.txt -o pyproject.toml`
- [x] 2.3 Remove `requirements.txt` from the repository
- [x] 2.4 Add `uv.lock` to version control
- [x] 2.5 Verify that `uv sync` installs dependencies correctly

## 3. Configure Ruff Linting & Formatting

- [x] 3.1 Add Ruff configuration to `pyproject.toml` under `[tool.ruff]`
- [x] 3.2 Create a pre-commit hook that runs `ruff check` and `ruff format`
- [x] 3.3 Run `ruff check` across the `client/` codebase and fix any violations

## 4. Automatic Model Synchronization

- [x] 4.1 Identify the engine Pydantic models to share (e.g., `engine/app/schemas/*.py`)
- [x] 4.2 Write a script `scripts/export_models.py` that imports the engine models and writes equivalent Pydantic definitions into `client/models.py`
- [x] 4.3 Add a CLI entry `uv run scripts/export_models.py` to regenerate client models
- [x] 4.4 Run the script and verify that generated `client/models.py` matches the engine definitions

## 5. Integration & Testing

- [x] 5.1 Update the client code to import models from the generated `client/models.py`
- [x] 5.2 Run existing client unit tests and fix any breakages
- [x] 5.3 Add integration tests that ensure the exported models work with the client UI
- [x] 5.4 Perform a full end-to-end test of the Streamlit client against a local engine instance

## 6. Documentation & Clean-up

- [x] 6.1 Update `README.md` with new setup instructions (UV, ruff, model export script)
- [x] 6.2 Remove any leftover references to `requirements.txt`
- [x] 6.3 Commit all changes and open a pull request for review
