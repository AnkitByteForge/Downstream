# Reference Engineering System — Implementation Context

## Project boundary

RES is a vendor-neutral Procore/ACC-realistic external engineering
system used by Downstream as a reference integration target.

RES must never:
- import Downstream packages
- construct EngineeringEventEnvelope
- perform Downstream reasoning
- execute commercial workflows
- own commercial state

## Architecture

domain
→ application
→ infrastructure
→ api

...

## Completed milestones

RES-1 — VERIFIED
RES-2 — VERIFIED
RES-3 — VERIFIED
PRE-RES-4 stabilization — VERIFIED
RES-4A — VERIFIED (DesignChange domain entity + closed lifecycle state machine, ADR-007)
RES-4B — VERIFIED (migration 0012, ORM, repository, use cases, REST API, thin webhook on `issue`, `IssueDrawingVersion`)
RES-4C — VERIFIED (frontend register + detail pages, seed assertion test)
RES-4D — VERIFIED (canonical ASI-07 / DWG-E-1.1 seed, webhook subscription)
RES-4E — VERIFIED (design-changes API contract suite + canonical ASI-07↔RFI-214 source link)
RES-4F — VERIFIED (project isolation + scope-containment contract suite)
RES-4G — VERIFIED (final verification checkpoint from a fresh schema, 127 tests — see below)

## Current checkpoint

RES-4A/B verification passed (2026-08-09): backend full suite green
(111 passed against a migrated Postgres schema) plus a live API smoke test
of the design-changes lifecycle (list → get → issue → acknowledge) against
the seeded Meridian Tower project; thin webhook on `issue` is covered by the
unit suite. Checkpoint committed with RES-4A/B verified.

RES-4C/D completed (2026-08-09) in the same work session:
- RES-4C (frontend): design-changes register + detail pages, nav entry,
  `DesignChangeStatusBadge`, `designChangesApi` + `DesignChangeOut` types;
  `npm run build` (incl. TS) + ESLint clean; live dev-server render verified.
- RES-4D (canonical seed): `DWG-E-1.1` (Electrical Plan – Level 1) Rev 0 →
  Rev 1 supersession plus `ASI-07` (ISSUED, affecting Rev 1 and Spec 26 24 13)
  per Canonical_Demo_Dataset §8, and a `design_changes` webhook subscription.
  The full suite now runs 112 tests including the new seed assertion test
  `tests/integration/test_seed_data.py`.

RES-4E/F completed (2026-08-10, commits `fa48f44`):
- RES-4E: `tests/contract/conftest.py` + `test_design_changes_api.py` — auth,
  `X-Total`, pagination, contract-field shape, scoped-integration 404s,
  cross-project isolation, webhook dispatch on `issue` (+ recorded
  `webhook_deliveries` row), 409 already-issued, per-client rate limiting; the
  canonical seed carries the ASI-07↔RFI-214 `source_rfi_id` link, asserted to
  stay the lone Scenario-A trigger chain.
- RES-4F: `tests/contract/test_project_isolation.py` — human/integration and
  cross-project 404 semantics for projects, RFIs, activity, mutations across
  RES-3 + RES-4 surfaces.

RES-4G verified (2026-08-10, uncommitted this session):
- **Fresh schema**: `reference_engineering` recreated on `res-test-db`; 12
  alembic migrations → `head`, then `run_seed` on the empty schema.
- **127 passed** (all tiers, incl. architecture + seed assertion + contract
  suites). Frontend build + ESLint clean.
- **Live smoke**: login, design-changes list/detail (ASI-07), `issue` on a
  DesignChange and on a DrawingVersion (each thin webhook delivery recorded),
  state restored to canonical seed.
- **Data facts**: RFI-214 CLOSED sole Scenario-A trigger; SUB-118 Rev 0→Rev 1
  MCA 180→240 A / FLA 150→200 A preserved; ASI-07 ISSUED linked to RFI-214,
  not a Scenario-B trigger; DWG-E-1.1 Rev 0 superseded by Rev 1; thin webhook
  configs + canonical `webhook_deliveries` behavior intact.
- Working tree clean; `git diff --check` clean; no commit staged.

RES-5 backend surface — VERIFIED (2026-08-12): ScheduleActivity + ModelObject
domain/migration/API/seed/contract tests, 157 backend tests passing from a
fresh schema (see IMPLEMENTATION_STATUS.md §17, ADR-008). Frontend/Playwright/
Docker verification in progress. Field Issues remain unscoped — a flagged
contradiction with ADR-007's "FieldIssue is RES-5" phrasing; see §17.1.

## Canonical scenarios

Scenario A:
RFI-214 → ...

Scenario B:
SUB-118 Rev 1 → ...

## Non-negotiable architectural rules

...