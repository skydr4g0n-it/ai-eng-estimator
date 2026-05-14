# Estimator Streamlit client

Small **Streamlit** form that mirrors the engine’s synchronous **`EstimationRequest`** (`description`, `project_type`, `detail_level`, `output_format`) and displays the returned **`text`** and **`prompt_version`**.

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `ESTIMATOR_API_BASE_URL` | Yes | Engine root URL, e.g. `http://localhost:8000` (no path suffix; the app calls `{base}/api/v1/estimate`). |

## Run

From this directory, with Python 3.11+:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Optional: create a virtualenv first (`python -m venv .venv`, activate, then install).

## Enum parity with the engine

Field names and allowed string values match **`engine/app/schemas/estimation.py`**:

- **project_type:** `mobile_app`, `web_saas`, `internal_tool`, `data_pipeline`
- **detail_level:** `summary`, `medium`, `detailed`
- **output_format:** `phases_table`, `line_items`, `narrative`

The client duplicates these in `models.py` so it can run without installing the engine package. Keep both in sync when the wire contract changes.
