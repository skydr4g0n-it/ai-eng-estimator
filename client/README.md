# Estimator Streamlit client

Small **Streamlit** form that mirrors the engine's synchronous **`EstimationRequest`** (`description`, `project_type`, `detail_level`, `output_format`) and displays the returned **`text`** and **`prompt_version`**.

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `ESTIMATOR_API_BASE_URL` | Yes | Engine root URL, e.g. `http://localhost:8000` (no path suffix; the app calls `{base}/api/v1/estimate`). |

## Run

From this directory, with Python 3.11+:

```bash
uv sync
uv run streamlit run app.py
```

Use `ESTIMATOR_API_BASE_URL=http://localhost:8000` when running against a local engine.

## Tooling

Run linting and formatting from this directory:

```bash
uv run ruff check .
uv run ruff format .
```

Install the versioned pre-commit hooks with:

```bash
uv run pre-commit install --config .pre-commit-config.yaml
```

## Model parity with the engine

Field names and allowed string values match **`engine/app/schemas/estimation.py`**:

- **project_type:** `mobile_app`, `web_saas`, `internal_tool`, `data_pipeline`
- **detail_level:** `summary`, `medium`, `detailed`
- **output_format:** `phases_table`, `line_items`, `narrative`

Regenerate `models.py` after engine schema changes:

```bash
uv run scripts/export_models.py
```

The generated file is committed so the Streamlit client can import the same wire contract without installing the engine as a package.
