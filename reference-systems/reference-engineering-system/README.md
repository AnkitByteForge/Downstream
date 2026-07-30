# Reference Engineering System

A realistic, vendor-neutral construction engineering platform — inspired by
Procore, Autodesk Construction Cloud, and Trimble ProjectSight, but cloning
no vendor's proprietary schema or branding. It is not a mock or a demo toy
(see `docs/adr/ADR-001.md`): its purpose is to faithfully model real
engineering workflows and produce the realistic engineering events Downstream
will later consume through its own connector layer.

Two independently deployable applications:

- **`backend/`** — FastAPI, Clean Architecture (Domain / Application /
  Infrastructure / API), PostgreSQL, Alembic. See `backend/README.md`.
- **`frontend/`** — Next.js, TypeScript, Tailwind, shadcn/ui. See
  `frontend/README.md`.

## Specifications this implementation follows

- `docs/reference/The Reference Engineering System.md` — the domain model
  (entities, relationships, state machines).
- `docs/04_Downstream_Connector_Layer_Validation.md` — the API/auth/webhook
  behavioral fidelity this system must exhibit (thin webhooks, OAuth2,
  permission scoping, rate limiting).
- `docs/05_Downstream_Reference_Execution_Trace.md` — the exact Meridian
  Tower / RFI-214 scenario this system's seed data reproduces field-for-field.

## Status

Implementing per `07_Downstream_Implementation_Blueprint.md`-style milestones
scoped to this subsystem (RES-1 through RES-5) — see the root
`IMPLEMENTATION_STATUS.md` for current progress.
