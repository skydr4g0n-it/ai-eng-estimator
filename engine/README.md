# Estimator (engine)

AI-powered **software estimation** API: the synchronous **`POST /api/v1/estimate`** path accepts a **typed form** (`description`, `project_type`, `detail_level`, `output_format`), renders **versioned Jinja2** prompts under `app/prompts/estimation/<version>/`, and calls **LiteLLM** with **separate `system` and `user` chat messages** (no merged single-user blob). **Session 3** adds primary + fallback models, **Redis** exact-match caching (keyed on full rendered prompts + model + `max_tokens` + optional thinking budget), **structlog**, and **SSE streaming** via `POST /api/v1/estimate/stream` (still **transcription**-based for this iteration). A small **static SSE demo** is at `/static/sse_demo.html`.

A **Streamlit** form client lives in the repo root **`client/`** (outside `engine/`); see `client/README.md`.

## Breaking change vs earlier transcription-only sync API

- **`POST /api/v1/estimate`** no longer accepts `transcription` or tuning knobs. The JSON body is **`EstimationRequest`**: `description` (20–2000 chars), `project_type`, `detail_level`, `output_format` (see `app/schemas/estimation.py`).
- The **200** JSON body is only **`{ "text", "prompt_version" }`**. There is no `usage`, `validation`, `cache_hit`, `cost_usd`, or `estimation` field on this endpoint.
- **Default models** (env): `PRIMARY_MODEL=gpt-4o-mini`, `FALLBACK_MODEL=claude-haiku-4-5-20251001` (or swap to another supported pair).

## Prompt layout (Jinja)

Templates ship next to the code under:

```text
app/prompts/
├── loader.py
└── estimation/
    └── v1/
        ├── system.j2   # role, output_format / detail_level branches, {% include %} examples
        ├── user.j2     # wraps description in <project_description>…</project_description>
        └── examples.j2 # few-shot examples
```

`render_estimation_prompt(request, version=...)` uses **StrictUndefined**, **trim_blocks**, and **lstrip_blocks**. **`ESTIMATION_PROMPT_VERSION`** (default `v1`) selects the `estimation/<version>/` folder; the HTTP **`prompt_version`** field matches that value.

## Environment variables

See **`.env.example`** for names read by `app.config.Settings`:

`OPENAI_API_KEY`, `ANTHROPIC_API_KEY` (at least one required), `APP_ENV` (`development` | `staging` | `production` | `test`), `LOG_LEVEL`, `PRIMARY_MODEL`, `FALLBACK_MODEL`, `LLM_TIMEOUT`, `LLM_RETRIES`, `REDIS_URL`, `CACHE_TTL`, **`ESTIMATION_PROMPT_VERSION`**.

## Quick start (Docker)

```bash
cd engine
cp .env.example .env
# Edit .env: set API keys. For uvicorn on the host, set REDIS_URL=redis://127.0.0.1:6379 if needed.
docker compose up --build
```

- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- SSE demo: `http://localhost:8000/static/sse_demo.html`

### Try the sync endpoint (new contract)

```bash
curl -sS -X POST http://localhost:8000/api/v1/estimate \
  -H "Content-Type: application/json" \
  -d "{\"description\": \"The client wants a web SaaS for managing restaurant reservations with user accounts, search, real-time availability, notifications, and an owner admin area. MVP in roughly two months.\", \"project_type\": \"web_saas\", \"detail_level\": \"medium\", \"output_format\": \"narrative\"}"
```

### Try SSE streaming (transcription body, unchanged)

```bash
curl -N -X POST http://localhost:8000/api/v1/estimate/stream \
  -H "Content-Type: application/json" \
  -d "{\"transcription\": \"We need a small CRM with auth, contacts and roles. MVP six weeks.\"}"
```

## Local development (without Docker)

Requires **Python 3.11+**, **Redis** at **`REDIS_URL`**, and API keys in `.env`.

```bash
cd engine
uv sync
uv run uvicorn app.main:app --reload
```

## Tests

```bash
cd engine
uv sync --dev
uv run pytest
```

CI / Docker: from `engine/`, **`docker compose run --rm tests`** runs the suite (Redis service + pytest).

## Project layout

```
engine/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   ├── prompts/           # Jinja packs + loader (copied with app/ in Docker)
│   ├── routers/estimations.py
│   ├── schemas/estimation.py
│   ├── services/llm_service.py, llm_wrapper.py, cache.py, evaluation.py
│   ├── context/examples.py
│   └── static/sse_demo.html
├── tests/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── uv.lock
```
