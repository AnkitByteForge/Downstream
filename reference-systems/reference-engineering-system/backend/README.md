# Reference Engineering System — Backend

A vendor-neutral, Procore/ACC-realistic construction engineering platform.
Produces the raw engineering events Downstream will later consume through
its own connector layer — this system is **not** a Downstream service; it
plays the role of the external system Downstream connects into.

See `docs/reference/The Reference Engineering System.md` (domain model) and
`docs/04_Downstream_Connector_Layer_Validation.md` (API/auth/webhook
behavioral fidelity) for the specifications this implementation follows.

## Architecture

Clean Architecture, four layers, dependency rule enforced by
`tests/architecture/test_layer_boundaries.py`:

```
api/            <- FastAPI routers, Pydantic schemas, composition root (deps.py)
application/    <- use cases, orchestration; depends only on domain
domain/         <- entities, value objects, state machines, repository ports
                   (zero framework imports — pure Python)
infrastructure/ <- SQLAlchemy repositories, OAuth2 + session auth, config
```

## Running locally

```bash
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"

# Point at a running Postgres (see infra/docker-compose.yml for the
# reference-engineering-db service, or run one directly):
export RES_DATABASE_URL="postgresql+psycopg://res:res@localhost:5433/reference_engineering"

.venv/Scripts/python -m alembic upgrade head
.venv/Scripts/python -m seed.run_seed   # (run from src/, or set PYTHONPATH=src)
.venv/Scripts/python -m uvicorn api.main:app --reload --app-dir src
```

API docs at `http://localhost:8000/docs`.

## Seeded demo accounts

All seeded human users share the password `downstream-demo` (see
`src/seed/meridian_tower.py`). `ananya.rao@meridiangc.example` is the
Project Manager from the Reference Execution Trace scenario.

Two OAuth2 integration clients are seeded for exercising
`acting_credential_scope` fidelity: `downstream-full` / `full-scope-secret`
(full visibility) and `downstream-partial` / `partial-scope-secret`
(scoped to `rfis`, `submittals`, `documents` — matching the trace's Phase
1.2 literally). Each has a single-use seeded `authorization_code` for the
initial `POST /oauth/token` exchange.

## Tests

```bash
pytest -q
```

`tests/unit/` — domain state machines and application use cases (the latter
against in-memory fake repositories, no database). `tests/architecture/` —
asserts `domain/` and `application/` never import FastAPI/SQLAlchemy/etc.
`tests/contract/` and `tests/integration/` are added starting RES-2/RES-3 as
webhook dispatch and further persistence surfaces come online.
