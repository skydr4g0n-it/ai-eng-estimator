## Context

The authoritative behavioral reference is the upstream `estimator/` tree on branch `session_3_live`. Local code must remain under `engine/` with the same `app` package layout inside the image/build context. The stakeholder confirmed: **full feature parity** with the reference except **no chat UI** (no Streamlit app or Streamlit dependencies); **Redis is mandatory**; **LiteLLM replaces** bespoke dual-client logic; **breaking API changes** are allowed.

## Goals / Non-Goals

- **Goals**: LiteLLM wrapper with fallback and observability fields; Redis exact-match cache with TTL; sync and streaming estimation endpoints; structural evaluation on the sync path when enabled; structlog; Docker Compose and CI that start Redis and wire `REDIS_URL`; tests mirroring reference coverage patterns with mocks/fakes.
- **Non-Goals**: Streamlit or other interactive chat UIs; documenting or shipping `ESTIMATOR_API_BASE_URL` as a first-class product setting (optional one-line README note only); preserving the previous minimal request/response JSON shapes.

## Decisions

- **Decision: LiteLLM as the only completion path**  
  All model calls go through `LLMWrapper` (LiteLLM `Router` for default routing, direct `litellm.completion` when the request overrides `model`, matching upstream semantics). Rationale: matches course architecture and removes duplicate provider client code.

- **Decision: Redis required in real environments**  
  Compose defines a `redis` service with health checks; the API service sets `REDIS_URL` to the in-network host. Local `uvicorn` outside Docker uses `redis://localhost:6379` per `.env.example`. Rationale: stakeholder requirement; cache behavior is part of the learning objectives.

- **Decision: Tests use fakeredis where practical**  
  Unit tests for cache and wrapper integration avoid needing a live Redis process unless an explicit integration job is added later. CI still runs Redis for realism if tests are written to hit real Redis—tasks will align test strategy with the chosen compose CI command (see `tasks.md`).

- **Decision: Omit Streamlit**  
  Do not add `streamlit` to `pyproject.toml`; do not add `streamlit_app.py`. Rationale: explicit exclusion of chat UI transport.

## Risks / Trade-offs

- **Dependency weight** — LiteLLM and Redis increase supply-chain and ops surface. Mitigation: pin versions in `uv.lock`, document env vars, keep CI minimal but Redis-backed.
- **Breaking clients** — Any consumer of the old API must update. Mitigation: call out **BREAKING** in `proposal.md` and README migration notes.

## Migration Plan

1. Land implementation behind this change; update README with new env vars and endpoints.
2. Remove or rewrite obsolete tests and schemas under `engine/` that assume the pre-LiteLLM contract.
3. After deployment/merge, archive this change with `openspec archive sync-engine-with-session3-live --yes` and fold deltas into `openspec/specs/`.

## Open Questions

- None for proposal approval; implementation may choose fakeredis-only vs Redis-in-CI for specific tests as long as acceptance criteria in specs are met.
