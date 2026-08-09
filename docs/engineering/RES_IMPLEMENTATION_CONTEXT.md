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
RES-4C — pending (frontend register + detail + seed)
RES-4D — pending

## Current checkpoint

RES-4A/B verification passed (2026-08-09): backend full suite green
(111 passed against a migrated Postgres schema) plus a live API smoke test
of the design-changes lifecycle (list → get → issue → acknowledge) against
the seeded Meridian Tower project; thin webhook on `issue` is covered by the
unit suite. Checkpoint committed with RES-4A/B verified.

In progress — RES-4C/D:
- RES-4C (frontend): design-changes register + detail pages, nav entry.
- RES-4D (seed + surface): canonical ASI / DWG-E-1.1 design-change seed data
  with DWG-E-1.1 Rev 0 → Rev 1 supersession, matching Canonical_Demo_Dataset §8.

DO NOT begin RES-4E/F/G until:
1. full verification passes (of the completed slice, including whatever
   E/F/G turn out to be per the repo's later plans)
2. implementation status is updated
3. git checkpoint is committed

## Canonical scenarios

Scenario A:
RFI-214 → ...

Scenario B:
SUB-118 Rev 1 → ...

## Non-negotiable architectural rules

...