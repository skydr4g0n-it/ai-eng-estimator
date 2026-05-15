## ADDED Requirements

### Requirement: Client uses modern Python tooling with uv and pyproject.toml
The system SHALL use `uv` for dependency management and a `pyproject.toml` file to declare dependencies, scripts, and build configuration for the client project.

#### Scenario: Install dependencies with uv
- **WHEN** a developer runs `uv sync` in the client directory
- **THEN** `uv` resolves and installs all dependencies according to the lockfile, ensuring reproducible environments.

### Requirement: Automatic synchronization of Pydantic models from engine to client
The system SHALL provide a script that exports Pydantic model definitions from the engine package and generates corresponding model files in the client package, keeping them in sync.

#### Scenario: Export models via sync script
- **WHEN** the synchronization script `scripts/export_models.py` is executed
- **THEN** it reads the engine's Pydantic model definitions and writes up-to-date `client/models.py` (or a package) reflecting any changes.
