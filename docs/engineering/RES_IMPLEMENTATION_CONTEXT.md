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
RES-4A — VERIFIED
RES-4B — VERIFIED
RES-4C — VERIFIED (frontend register + detail pages, seed assertion test)
RES-4D — VERIFIED (canonical ASI-07 / DWG-E-1.1 seed, webhook subscription)

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

The seed assertion test clears all tables inside its own rolled-back
transaction (so it passes whether or not `run_seed` has been run) and
asserts RFI-214 stays the sole Scenario-A trigger, the ASI does not create a
new RFI, DWG-E-1.1 supersession is exact, and SUB-118's MCA/FLA table is
preserved.

DO NOT begin RES-4E/F/G until:
1. full verification passes (of whatever E/F/G turn out to be per the
   repo's later plans)
2. implementation status is updated
3. git checkpoint is committed

## Canonical scenarios

Scenario A:
RFI-214 → ...

Scenario B:
SUB-118 Rev 1 → ...

## Non-negotiable architectural rules

...