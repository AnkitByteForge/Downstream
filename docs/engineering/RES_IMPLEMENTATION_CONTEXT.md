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
RES-4B — 
RES-4C — 
RES-4D — 

## Current checkpoint

RES-4A-D implementation complete.
Verification checkpoint pending.

DO NOT begin RES-4E/F/G until:
1. full verification passes
2. implementation status is updated
3. git checkpoint is committed

## Canonical scenarios

Scenario A:
RFI-214 → ...

Scenario B:
SUB-118 Rev 1 → ...

## Non-negotiable architectural rules

...