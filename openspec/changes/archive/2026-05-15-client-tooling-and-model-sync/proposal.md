## Why

The `client` currently uses legacy tooling (`requirements.txt`) and relies on a manual duplication of the engine's Pydantic schemas in its own `models.py` file. This manual duplication is fragile and prone to drift. Migrating the client to modern Python tooling (`uv`, `pyproject.toml`, `ruff`) brings consistency across the repository, faster dependency installations, and better dependency locking. Additionally, creating an automatic model sync or shared package prevents schema divergence between the engine and the Streamlit client.

## What Changes

- Migrate the `client` project from `requirements.txt` to `uv` and `pyproject.toml`.
- Configure `ruff` for the `client` to ensure linting and formatting consistency with the engine.
- Establish a mechanism for schema parity without manual duplication. This could be an automatic model export script, or a shared internal package for models if deployment allows.

## Capabilities

### New Capabilities
- `estimation-client`: Streamlit form-based UI, tooling (uv, ruff), and automated model synchronization with the engine.

### Modified Capabilities

## Impact

- `client/`: New `pyproject.toml`, removal of `requirements.txt`, addition of `ruff` configuration.
- `client/models.py`: Replaced or auto-generated.
- Tooling or scripts might be added to manage model synchronization.
