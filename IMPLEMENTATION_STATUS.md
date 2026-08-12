# Downstream — Implementation Status

**Last updated:** 2026-08-12 (DIP Phase C Reliability/Calibration milestone — scale-aware grid detection, engineering-safe field validation, full failure classification against the real corpus; see §19)
**Purpose of this document:** a single reference for exactly what has been built so far, in what order, and why — so any future session (human or agent) can pick up work without re-deriving decisions already made. This file is a living status record, not a frozen design document; it does not belong in `/docs` and carries no architectural authority of its own. If it ever disagrees with `/docs`, `/docs` wins.

---

## 1. Source of truth

Every decision below traces back to the seven frozen documents in `/docs`, read in this order:

1. `01_Downstream_The_Company.md` — the five-year vision and the "wedge" discipline
2. `02_Downstream_Product_Design.md` — personas, journeys, pages, information architecture
3. `03_Downstream_Systems_Architecture.md` — the 14-stage service boundary map
4. `04_Downstream_Connector_Layer_Validation.md` — real-world corrections to the two envelope schemas
5. `05_Downstream_Reference_Execution_Trace.md` — one complete scenario, every payload shown literally
6. `06_Downstream_Implementation_Backlog.md` — what the trace actually requires, in dependency order
7. `07_Downstream_Implementation_Blueprint.md` — the repo structure, DB schema, API contracts, and milestone roadmap

**The architecture is frozen.** Nothing built so far redesigns anything — every field name, service boundary, event topic, and folder name is a direct translation of what these documents already specify.

---

## 2. Commit history

| Commit | What it did |
|---|---|
| `b929f2b` | Pre-existing — added the backlog and blueprint docs to `/docs` |
| `49a12f8` | **Repository initialization** — created the full monorepo folder structure per the blueprint. No logic. |
| `84823f0` | Made directly by the user (not by this assistant) — added `repo_structure.txt` at the repo root. Not reviewed or incorporated into the work below. |
| `8e05eef` | **Milestone 0** — implemented and tested the five `packages/` shared contracts. |
| `37b29c4` | Made directly by the user — added the four `docs/reference/*` documents and renamed the two mock scaffold folders to `infra/mocks/Reference Engineering System/` and `infra/mocks/Reference Commercial System/` (docker-compose.yml's build paths were not updated to match at the time). |
| `90dd7c5` | Made directly by the user — added this document. |
| `cf6683e` | Made directly by the user — added `docs/adr/ADR-001.md` (Reference Engineering System includes a web UI) and `docs/adr/ADR-002.md` (implementation directories use kebab-case; document titles unchanged). |
| `cb53b04` | **Reference Engineering System — RES-1.** See §10 below. |
| `d2c58b3` | Made directly by the user — corrected the `reference-engineering-*` build paths in `docker-compose.yml` to `../reference-systems/...`, which is only correct under plain (no `--project-directory`) invocation. Reconciled in this session — see §10.7. |
| `4cd2743` | Made directly by the user — added `reference-systems/reference-engineering-system/RES-1_USER_GUIDE.md`, a practical run/test guide (not a design document). |
| `03e1d35` | **Reference Engineering System — RES-2.** See §11 below. |
| `1880bf5` | Made directly by the user — added `docs/reference/The Enterprise Fidelity Review.md` and `docs/reference/Canonical_Demo_Dataset.md` (the reference authored by this assistant in an earlier turn, committed by the user alongside the former). |
| `467077e` | **Reference Engineering System — RES-3.** See §12 below. |
| `53a205b` | PRE-RES-4 stabilization — FLA fields on SubmittalRevision + project-isolation guards (§13), plus this document's §13 and `AGENTS.md`. |
| `f0d83c1` | Added `docs/research/DSH_Atacadero_Reconnaissance.md` (read-only research; not implementation). |
| `7a9d075` | **RES-4A** — DesignChange domain entity + closed lifecycle state machine (ADR-007) + unit tests. |
| `d5b9611` | **RES-4B** — DesignChange migration, ORM, repository, application use cases (list/get/issue/acknowledge/void/supersede), REST API, thin webhook on `issue`, `IssueDrawingVersion` use case, deps wiring, unit/application tests. |
| `0aa6318` | **RES-4A/B verification checkpoint** (see §14). |
| `3bc9d27` | **RES-4C/D** — Design Changes register + detail frontend pages, `DesignChangeStatusBadge`, api client, canonical ASI-07 / DWG-E-1.1 seed + seed assertion test (see §15). |
| `fa48f44` | **RES-4E** — design-changes API contract suite (`tests/contract/conftest.py`, `test_design_changes_api.py`) + the canonical ASI-07↔RFI-214 source link in the seed (see §16). |
| *(this session — RES-4G, uncommitted)* | **RES-4G final verification + checkpoint** — full re-verification from a fresh schema at 127 tests + live API smoke, docs updated (see §16). |

---

## 3. Current state, at a glance

| Layer | Status |
|---|---|
| `docs/` | Frozen, unmodified, source of truth |
| `apps/*` (16 services) | **Scaffold only** — folder structure, placeholder README/Dockerfile/pyproject.toml. Zero business logic, zero APIs, zero database code. This is Downstream's own service mesh — untouched by RES-1. |
| `packages/*` (5 packages) | **Implemented** — real, tested Pydantic models and an ABC. This is Milestone 0 (Downstream's own shared contracts — not used by the Reference Engineering System, see §10.1). |
| `infra/` | `docker-compose.yml` now wires the Reference Engineering System's three containers (db/backend/frontend); every other service entry is still scaffold-only, matching the blueprint. `mocks/Reference Engineering System/` was removed — superseded by `reference-systems/reference-engineering-system/` (see §10). `mocks/Reference Commercial System/` remains an empty placeholder. |
| `reference-systems/reference-engineering-system/` | **RES-1 through RES-5 implemented** — FastAPI backend (Clean Architecture) + Next.js frontend, both real, both tested, both containerized and verified end to end. RES-3 adds Submittals (parent/child revisioning, ADR-004), a configuration-driven procurement-release gate (ADR-003), Submittal Packages (ADR-005, unused by seed data), Vendors, minimal Commitments, the spec-driven Submittal Register, and the Submittal Register/Detail + Specification Browser frontend pages. RES-4 adds the Design Change (ASI/CCD/Bulletin) family per ADR-007 — domain/lifecycle (RES-4A), backend surface (RES-4B), frontend register/detail (RES-4C), canonical ASI-07/DWG-E-1.1 seed (RES-4D), API contract suite + RFI-source link (RES-4E), project-isolation/scope-containment contracts (RES-4F), and RES-4G's final verification checkpoint — see §14, §15, §16. RES-5 adds ScheduleActivity/ModelObject per ADR-008 — read-only domain/backend surface + canonical `sched_3410` seed + contract tests (RES-5A/B/D/E), Schedule/Model Objects frontend registers (RES-5C), the system's first Playwright E2E suite (RES-5F), and Docker Compose verification (RES-5G) — see §17. |
| Tests | 201 `packages/*` unit tests (unchanged) + **157 Reference Engineering System backend tests** (all tiers) passing against a freshly migrated, freshly seeded schema — including the seed assertion tests and the design-changes/submittals/schedule-activities/model-objects/project-isolation contract suites. Frontend: build + typecheck + lint clean, including the two new RES-5 routes. **12 Playwright E2E specs, all passing** (§17.10) — the first browser-automation coverage for this system. |
| Downstream Milestone (per blueprint §9) | Milestone 0 complete. Milestones 1–5 not started — unaffected by this phase. |
| Reference Engineering System Milestone (per RES-3 Plan v2 §3) | **RES-1 through RES-5 complete** — ScheduleActivity/ModelObject backend+frontend+seed+contract tests+Playwright+Docker all verified (§17). Field Issues remain unscoped — a flagged, unresolved documentation contradiction (§17.1). |
| `reference-systems/document-ingestion-pipeline/` (DIP) | **New sibling subsystem, not a Downstream service, not a Reference Engineering System dependency** (see the DSH ingestion architecture + post-RES-5 reconciliation docs). Phase A (PDF manifest), Phase B (OCR benchmark, Tesseract vs. RapidOCR), Phase C (E0.4 New Unit block real extraction, this session), and Phase D (deterministic synthetic revision diff) implemented and tested. Phase E (promotion into RES) explicitly not started — see §18. |

---

## 4. Phase 1 — Repository initialization (commit `49a12f8`)

**Task given:** initialize the repo structure exactly as defined in the Implementation Blueprint — folders, placeholder files, Docker Compose — with explicit instructions **not** to generate business logic, APIs, database tables, or frontend code.

**What was created**, all matching `07_Downstream_Implementation_Blueprint.md` §2–§4 folder-for-folder:

### `apps/` — 16 independently-runnable services
- **9 core backend services**, each given the blueprint's standard template:
  `src/{domain, consumers, publishers, repository, config}`, `tests/{contract, unit}`, `Dockerfile`, `pyproject.toml`.
  - `ingestion-service`, `key-resolution-service`, `reasoning-pipeline`, `commercial-event-service`, `ledger-service`, `notification-service`, `synchronization-service` — pure event-bus consumers/publishers.
  - `approval-service`, `realtime-gateway` — additionally given a `src/api/` folder, since these are the only two services with a documented synchronous surface (REST and WebSocket respectively, per blueprint §7).
  - `migrations/` was added **only** to the services the blueprint's §6 SQL schema names as owning a table: `ingestion-service`, `commercial-event-service`, `approval-service`, `ledger-service`, `synchronization-service`, `reasoning-pipeline`. `key-resolution-service` was left without one — it owns the Graph DB, which is not relational.
- **6 connector adapters**, each given the connector template (`src/{inbound, client, mapper, idempotency, config}`, `tests/contract`):
  - `connector-procore`, `connector-sap`, `connector-email` — wired for Milestone 1.
  - `connector-acc`, `connector-oracle`, `connector-erpnext` — explicitly labeled stubs, matching the blueprint's `profiles: ["deferred"]` Docker Compose treatment. Present so their shape never needs rework later.
- **`web/`** — the frontend shell, with all seven page routes present as stub folders (`commercial-state`, `event-inbox`, `event-detail` for Milestone 1; `integrations`, `project-graph`, `timeline`, `settings` marked deferred), plus `realtime/`, `api-client/`, `components/`.

### `packages/` — 5 empty package skeletons (filled in during Phase 2)
`envelope-schemas`, `connector-interface`, `domain-models`, `event-contracts`, `shared-config` — each just a placeholder `README.md`/`pyproject.toml` and empty `src/`/`tests/` folders at this point.

### `infra/`
- `docker-compose.yml` — copied **verbatim** from blueprint §4, including the `deferred` Compose profile for the three stub connectors.
- `migrations/` — placeholder for the cross-cutting Milestone 0 setup (artifact identity map, connector config store) — still empty.
- `mocks/mock-engineering-system/` and `mocks/mock-erp/` — placeholders for the Procore-shaped and SAP-shaped mocks described in the Connector Layer Validation doc.

### Root
`README.md` (mission statement, doc index, folder map, run instructions) and `.gitignore`.

**Why this order/shape:** every folder decision is a direct copy of blueprint §2–§4. No SQL was written into any `migrations/` folder (that would violate "do not generate database tables"), no route logic was written into any `web/` page (would violate "do not generate frontend"), and no service was given actual consumer/publisher code (would violate "do not implement any service").

---

## 5. Phase 2 — Milestone 0: shared contracts (commit `8e05eef`)

**Task given:** implement **only** the five `packages/` — real Pydantic models, the canonical envelopes, `CommercialEvent`, event topic contracts, connector interfaces as ABCs — plus comprehensive unit tests. Explicitly still no services, no databases, no APIs.

Before writing any code, all seven `/docs` files were re-read in full to pull exact field names rather than work from memory. Python 3.11.9 / Pydantic 2.13.4 / pytest 9.0.3 were confirmed available so the packages and tests would actually be runnable, not just written.

### 5.1 `packages/envelope-schemas` — what a connector produces

| Model | Fields | Source |
|---|---|---|
| `DrawingRef` | `item_id`, `version_id` | Split into two fields (not one opaque string) because ACC's revision-diffing depends on distinguishing "Rev B" from "Rev C" — `docs/04` |
| `EngineeringEventEnvelope` | `envelope_type`, `source_system`, `source_id`, `display_number`, `type` (`RFI_APPROVED\|DRAWING_REVISED\|SPEC_UPDATED`), `spec_section_refs[]`, `drawing_refs[]`, `location_refs[]`, `raw_document_ref`, `region`, `acting_credential_scope`, `occurred_at` | Base shape from `docs/03` §1; the four additions (`display_number`, split drawing ref, `region`, `acting_credential_scope`) from `docs/04`'s real-system validation; exact wire shape verified against Phase 1.3 of `docs/05` |
| `OrgScope` | `company_code`, `plant`, `business_unit` (all optional) | Generalizes SAP's Company Code/Plant and Oracle's Business Unit — `docs/04` |
| `CommercialArtifactSnapshot` | `envelope_type`, `source_system`, `source_id`, `artifact_type` (`PO\|VENDOR\|DELIVERY`), `cost_code`, `cost_code_format` (5-value enum), `spec_section_refs[]`, `lifecycle_position` (free string — see note below), `value`, `vendor_ref`, `project_ref`, `org_scope`, `data_freshness_path` (`real_time_event\|polled\|bulk_import`), `fetched_at` | Base shape `docs/03` §1; three additions (`org_scope`, `cost_code_format`, `data_freshness_path`) from `docs/04` |

**Note on `lifecycle_position`:** left as a free-form string rather than a closed enum, because the product doc (`draft/issued/in fabrication/shipped/installed`) and the Reference Trace (`SCHEDULED/IN_FABRICATION/SHIPPED/N/A`) use two different, disagreeing vocabularies for it. Picking one would assert a canonical casing neither frozen document actually commits to.

All models are **frozen** (immutable) — they represent a point-in-time wire snapshot, not a mutable record.

### 5.2 `packages/domain-models` — the five objects the blueprint names for this package

Per blueprint §2's explicit comment (`# Trigger, CommercialEvent, Impact, Action, Approval`), **only these five** were modeled — other `docs/02` Part 5 entities (Organization, Project, User, Commercial Artifact, Integration, Ledger entry, Graph/KeyIndex) belong to the services that own them and were deliberately left out.

| Model | Key fields | Notes |
|---|---|---|
| `Trigger` | `trigger_id`, `project_id`, `type`, `source_envelope_ref`, `spec_section_refs[]`, `drawing_refs[]`, `location_refs[]`, `raw_document_ref`, `occurred_at`, `status`, `created_at` | `status` is a plain string defaulting to `"PENDING_RESOLUTION"` — the *only* value any frozen document names for it. No other transition states were invented. |
| `CommercialEvent` | `event_id`, `project_id`, `trigger_id`, `severity` (1–4), `status`, `created_at`, `closed_at` | `status`: `DETECTED → TRIAGED → ACTIONED → CONTAINED → CLOSED` |
| `Impact` | `impact_id`, `event_id`, `artifact_ref`, `confidence_tier` (`CERTAIN\|PROBABLE\|POSSIBLE`), `confidence_reason`, `lifecycle_position_at_detection`, `evidence_refs[]`, `action_id`, `severity` (1–4), `status` (`OPEN\|CONTAINED`) | See **discrepancy resolution** below |
| `Action` | `action_id`, `impact_id`, `type` (`VENDOR_HOLD_NOTICE\|ERP_HOLD_FLAG\|ERP_RESCHEDULE\|FLAG_FOR_REVIEW`), `drafted_content`, `status` (`DRAFTED→APPROVED/REJECTED/EDITED→SENT→COMPLETED`) | |
| `Approval` | `approval_id`, `action_id`, `user_id`, `decision` (`APPROVED\|REJECTED\|ACKNOWLEDGED_NO_ACTION`), `edited_content`, `decided_at` | Deliberately separate from `Action` so the audit trail can never be altered after the fact, even if the action's draft content could still be revised pre-approval |

**Discrepancy resolution — `Impact.status`:** the Reference Trace's illustrative SQL (Phase 6) inserts impacts with `status = 'TRIAGED'`, but the Implementation Blueprint's `impacts` table comment says `OPEN|CONTAINED`. These two frozen documents disagree. The Blueprint was treated as authoritative here — it is explicitly the "translation only, nothing redesigned" implementation handoff meant to be built against — and a test (`test_rejects_invalid_status` with `"TRIAGED"`) documents this choice rather than silently picking one and hiding the conflict.

### 5.3 `packages/event-contracts` — one schema per Event Bus topic

Ten topics, matching blueprint §8 **exactly**:

`trigger.detected`, `keys.resolved`, `event.created`, `impact.tiered`, `severity.computed`, `action.drafted`, `action.approved`, `action.dispatched`, `action.confirmed`, `event.closed`

Each schema's fields were reverse-derived from the literal JSON payloads shown in `docs/05` (the trace explicitly claims "nothing below is summarized — every payload shown is the literal shape that stage produces"), cross-checked against the WebSocket contract in blueprint §7 where both existed.

**Deliberate omission — `graph.updated`:** `docs/03` §3's canonical topics table names an eleventh topic, `graph.updated`. Blueprint §8 explicitly narrows the list to ten and states "all ten are the complete topic list this scope requires." `graph.updated` was left out on purpose, with the reasoning recorded in `topics.py`'s module docstring, rather than silently added or silently dropped without explanation.

`topics.py` holds the topic name constants (`TRIGGER_DETECTED`, etc.) plus `ALL_TOPICS` and a `TOPIC_SCHEMAS` registry mapping each topic string to its Pydantic model.

### 5.4 `packages/connector-interface` — the shared adapter contract

`ConnectorInterface` — an `abc.ABC` with four `@abstractmethod`s, translating `docs/03` §1's contract verbatim (method names converted to snake_case, a pure naming translation with no architectural effect, per the blueprint's own stated allowance for such translations):

```python
fetch_engineering_events(since: str) -> list[EngineeringEventEnvelope]
fetch_artifact_snapshot(artifact_ref: str) -> CommercialArtifactSnapshot
push_action(action: ActionPayload) -> DispatchReceipt
health_check() -> ConnectionHealth
```

Kept as **one** interface, not split by connector family (Engineering vs. Commercial) — `docs/03` states it applies "regardless of source system," and `docs/04`'s Procore analysis confirms a single connection may need to serve both envelope families at once.

Support types, derived minimally from the Reference Trace's two actual dispatch calls (never inventing a connector-specific field like an email address or a SAP OData field name, which belongs in that adapter's own `mapper/` layer, not this shared package):

- `ActionPayload` — `action_id`, `action_type`, `drafted_content`, `target_artifact_ref`, `idempotency_key`
- `DispatchReceipt` — `dispatch_id`, `status` (`SENT|DELIVERED|FAILED`), `detail`
- `ConnectionHealth` — `source_system`, `scope_granted`, `last_successful_sync`, `error_state` (three fields named verbatim in `docs/03`: "scope granted, last successful sync, error state")

Tests prove the ABC cannot be instantiated directly, cannot be instantiated with any one method missing, and that a minimal in-memory conforming subclass works end to end.

### 5.5 `packages/shared-config` — deliberately narrow scope

The **only** shared runtime convention any frozen document actually names is the ID format: `docs/07` §6 — *"IDs use short, prefixed identifiers (matching the Reference Trace's own style — `trg_…`, `evt_…`) rather than raw UUIDs."*

Implemented exactly that, and nothing more (no invented service ports, env-var names, or connection-string schemas, since none are specified anywhere):

- `ID_PREFIXES` — `{trigger: "trg", commercial_event: "evt", impact: "imp", action: "act", approval: "apr"}`
- `generate_id(entity)` — produces e.g. `evt_3f9a1c2b`
- `is_valid_id(entity, value)` — shape validation only, no store lookup

### 5.6 Testing

**201 unit tests, all passing**, across all five packages. Coverage per package:

- Every enum's full value set is exercised (parametrized tests for each Literal)
- Happy-path shapes are checked against the literal payloads shown in the Reference Trace
- Validation failures (missing required fields, invalid enum values, out-of-range severities/scores) are asserted to raise `pydantic.ValidationError`
- Immutability (`frozen=True`) is asserted on every model
- JSON round-trips (`model_dump_json` → `model_validate_json`) are asserted for every model

No warnings (including deprecation warnings) are produced by the suite.

### 5.7 Root `pyproject.toml` — test tooling only

A root-level `pyproject.toml` was added, containing **only** a `[tool.pytest.ini_options]` block (`pythonpath` pointing at each package's `src/`, `testpaths` pointing at each package's `tests/`). This lets `pytest` run from the repo root and resolve cross-package imports (e.g. `domain-models` importing `envelope-schemas`) without a full editable-install step. It configures no service, no API, and no database — it exists solely so "generate comprehensive unit tests" was actually verifiable, not just written.

Each package's own `pyproject.toml` was also updated from the Phase 1 placeholder to a real installable package definition (`pydantic>=2,<3` dependency, `[tool.setuptools.packages.find]` src-layout, declared inter-package dependencies where one package imports another).

---

## 6. What is explicitly NOT implemented yet

- **No service logic** in any of the 16 `apps/*` directories — every `src/{domain,consumers,publishers,...}` folder is still empty (`.gitkeep` only).
- **No database** — every `migrations/` folder (both per-service and `infra/migrations/`) is still an empty placeholder. No table has been created anywhere, per Milestone 0's explicit constraint.
- **No APIs** — `approval-service/src/api/` and `realtime-gateway/src/api/` are empty; no FastAPI route exists anywhere in the repo.
- **No event bus wiring** — Kafka is declared in `docker-compose.yml` but nothing publishes or consumes from it yet.
- **No connector adapter logic** — `connector-procore`, `connector-sap`, `connector-email` have no `inbound/client/mapper/idempotency` code; the three deferred connectors (`connector-acc`, `connector-oracle`, `connector-erpnext`) remain stubs by design.
- **No frontend** — `apps/web` has no actual page code, just the route-stub folder structure.
- **No mocks running** — `mock-erp` still has empty `src/`. (`mock-engineering-system` no longer exists as a concept — superseded by the Reference Engineering System, §10.)

This section describes **Downstream's own** `apps/*`/`packages/*` only. The separate `reference-systems/reference-engineering-system/` subsystem has its own implementation status — see §10.9.

---

## 7. Milestone roadmap (for reference — from blueprint §9)

| Milestone | Scope | Status |
|---|---|---|
| **0 — Foundational data layer** | Artifact identity map, connector config store, seeded Graph Layer, Event Bus provisioned with all ten topics | **Shared contracts done** (`packages/`); the artifact identity map, connector config store, and seeded graph themselves are service/infra work, not yet started |
| **1 — Ingestion path** | Connector-Procore (against the mock), Ingestion & Normalization Service | Not started |
| **2 — Reasoning** | Key Resolution, the five-stage Reasoning Pipeline, artifact snapshot cache, Connector-SAP's `fetchArtifactSnapshot` | Not started |
| **3 — Domain core** | Commercial Event Service (full state machine), Ledger Service, live Commercial State query | Not started |
| **4 — Realtime and human approval** | Realtime Gateway, Approval Service, the three Milestone-1 frontend surfaces | Not started |
| **5 — Synchronization, both tiers** | Sync Service against email, then SAP's full CSRF ceremony — the entire Reference Trace end to end | Not started |
| **6+** | Reject/edit flows, digest notifications, retry/backoff, ACC/Oracle/ERPNext connectors, deferred UI pages, portfolio rollups, forecasting | Explicitly out of scope until Milestone 5 is proven |

Per the blueprint: *"Milestone 5 is the only true 'done' for this phase of work... none of them alone proves the product's central claim — only the full closed loop does."*

---

## 8. How to verify this state yourself

```bash
# from the repo root
python -m pytest -q
# expected: 201 passed
```

```bash
git log --oneline
# b929f2b docs
# 49a12f8 repository initialization
# 84823f0 (user commit — repo_structure.txt, not part of this work)
# 8e05eef Milestone 0 shared contracts
```

---

## 9. Open item

`repo_structure.txt` (root of the repo, 559 lines) was added directly by the user in commit `84823f0`. It has not been read or reconciled against anything in this document or in `/docs`. Flagging here so it isn't silently forgotten.

---

## 10. Phase 3 — Reference Engineering System: RES-1

**Task given:** implement RES-1 of the approved Reference Engineering System Implementation Plan v2 — a Clean Architecture FastAPI backend and a Next.js frontend, covering Project/Discipline/Location/SpecSection/Drawing/DrawingVersion/RFI, integration OAuth2 + human session auth, seed data reproducing the Reference Execution Trace's Meridian Tower/RFI-214 scenario, and the Login/Dashboard/Project Explorer/RFI Register/RFI Detail pages. Plan v2 itself was revised from v1 per explicit instruction to treat this system as a full enterprise application (not a mock), with a Next.js frontend and strict Domain/Application/Infrastructure/API/Presentation separation — see the conversation history for the full plan text; it is not duplicated here.

This system is **not** a Downstream service. It plays the role of the external system (Procore/ACC-shaped) that a future `connector-procore` will connect into. It shares no code with `packages/*` or `apps/*` by design (§10.1).

### 10.1 Where it lives, and why

`reference-systems/reference-engineering-system/{backend,frontend}/` — a new top-level directory, sibling to `apps/`, `packages/`, `infra/`. Originally scaffolded under `infra/mocks/mock-engineering-system/` per the Blueprint, then renamed by the user to `infra/mocks/Reference Engineering System/` (commit `37b29c4`) alongside the four new reference docs. Relocated again here per the user's explicit approval of Plan v2 §22.1: *"The system is no longer considered a mock."* `infra/mocks/Reference Engineering System/` (the old scaffold — Dockerfile/README/`.gitkeep` only, no logic) was deleted as part of this move; nothing of substance was lost.

Directory name is kebab-case per `docs/adr/ADR-002.md`; the reference document it implements keeps its title-case name (`docs/reference/The Reference Engineering System.md`) unchanged, per that same ADR.

Deliberately **zero dependency** on `packages/*`: those packages define Downstream's internal canonical wire shapes (`EngineeringEventEnvelope`, etc.). This system must produce *raw, vendor-shaped* payloads (Procore's own `id`/`display_number`/`status` shape) — translating raw→envelope is the future Connector-Procore adapter's job. If this system imported `envelope-schemas`, it would silently do the adapter's job for it, defeating the "swap the mock for real Procore, zero Reasoning Engine changes" guarantee `docs/04` is built around.

### 10.2 Backend — Clean Architecture, four layers

```
backend/src/
├── domain/          # entities (dataclasses), value objects, state machines, repository ports (ABCs), exceptions
│                     # zero imports of fastapi/sqlalchemy/httpx/jwt — enforced by tests/architecture/
├── application/      # use cases, DTOs, outbound ports (clock, password hasher, token service)
│                     # imports only domain — same enforcement
├── infrastructure/   # SQLAlchemy ORM models + repositories, OAuth2 + session auth, config, db session
└── api/              # FastAPI routers (thin — call exactly one use case each), Pydantic schemas, deps.py (composition root)
```

Entities implemented: `Project`, `Discipline`, `Location` (recursive tree), `SpecDivision`, `SpecSection`, `Drawing`, `DrawingVersion` (with `RevisionCloud` value objects), `RFI` (with `BallInCourt` value object), `User`, `IntegrationUser`, `OAuthClient`, `OAuthToken`.

State machines (pure functions in `domain/state_machines/`, `dataclasses.replace`-based, no mutation):
- **RFI**: `DRAFT → OPEN(BIC=assignee) → RESPONDED(BIC=manager) → CLOSED`, matching `docs/reference/The Reference Engineering System.md` §16 exactly. `close_rfi` also accepts a direct `OPEN → CLOSED` transition carrying its own response text, because the Reference Trace's own scenario closes RFI-214 in one step alongside its response — the formal `RESPONDED` intermediate exists but isn't mandatory.
- **DrawingVersion**: `DRAFT → ISSUED → REVISED → SUPERSEDED`, per the same doc.

Both are covered by `tests/unit/domain/` — every legal transition, every illegal one raises `InvalidTransition`, business-rule violations (e.g. closing with no response) raise `DomainRuleViolation`.

### 10.3 Two distinct auth surfaces (as scoped in Plan v2 §10)

1. **Integration-client OAuth2** (`infrastructure/auth/`, `api/v1/oauth.py`) — `authorization_code` and `refresh_token` grants, opaque bearer tokens (not JWT), single-use seeded authorization codes. Models the real Procore posture from `docs/04`.
2. **Human-user session** (`api/v1/auth.py`) — httpOnly JWT cookie (`res_session`), issued on `POST /auth/login`, verified per-request. Four roles seeded, taken directly from `docs/reference/The Reference Engineering System.md` §1's "Role division observed in practice": `PROJECT_MANAGER`, `PROJECT_ENGINEER`, `SUBCONTRACTOR`, `ARCHITECT_ENGINEER_OF_RECORD`, plus `ADMIN`.

Both resolve to one `ActingContext` union type (`api/deps.py`) so every router asks exactly one question — `ctx.can_see(resource_type)` — regardless of which auth surface answered it.

**Verified behavior, not just implemented:** a partially-scoped integration credential (seeded scope `["rfis","submittals","documents"]`, matching the Reference Trace Phase 1.2's `partial:[rfis,submittals,documents]` literally) gets a **silently empty list**, not a 403, when it queries `spec_sections` — confirmed by live `curl` against a running instance, not just asserted in a unit test. This is the specific behavior `docs/04` calls out as the highest-value thing to get right: *"a partially-scoped integration user will silently return incomplete data rather than erroring."*

### 10.4 Database

PostgreSQL 16, Alembic, 4 migrations (`0001` core project structure → `0002` users/OAuth2 → `0003` drawings → `0004` RFIs — reordered from Plan v2's original 1/2/3/4 grouping because `RFI.ball_in_court_user_id` FKs to `users.id`, so auth had to move before RFIs; noted here as the one deviation from the plan's literal migration order, made for a concrete FK-dependency reason, not a scope change).

**Verified, not assumed:** all four migrations applied cleanly to a brand-new Postgres 16 instance (both an ad-hoc container and, separately, the actual `docker-compose` `reference-engineering-db` service); the resulting schema's table set was diffed programmatically against the SQLAlchemy `Base.metadata` and found to match exactly (only the expected `alembic_version` bookkeeping table differs).

### 10.5 Seed data

`backend/src/seed/meridian_tower.py` reproduces `docs/05_Downstream_Reference_Execution_Trace.md` field-for-field: Project "Meridian Tower", Discipline M, Location tree (Site → Building → Level 4 → Grid B-4), SpecSection `23 31 13`, Drawing `M-2.1` with Rev B (superseded) and Rev C (current, revision-clouded, exact description *"Duct DN200 rerouted 0.6m south of Beam B-14"*), and RFI-214 itself — closed at the trace's literal timestamp (`2026-07-28T09:14:03Z`) with the trace's literal response text. The RFI is seeded through its real state machine (`open_rfi → respond_to_rfi → close_rfi`), not inserted pre-closed, so the seed script doubles as an integration exercise of the domain layer. Five `User` rows (one per role) and two `IntegrationUser` + `OAuthClient` pairs (full-scope and partial-scope) are included so the frontend's Login page and the OAuth flow both have real accounts to run against — this is beyond what the trace itself specifies, added because Plan v2's frontend requires real login accounts to be demoable.

**Verified end to end** (live `curl` session against a running instance, both locally and inside the Docker Compose stack): login → `GET /rest/v1.0/projects/1/rfis/1` returns the exact trace-shaped payload; `POST /oauth/token` with `grant_type=authorization_code` issues a real token pair and the code is provably single-use (a second exchange attempt returns 400); the drawing revision timeline endpoint returns Rev B (`SUPERSEDED`, pointing at Rev C) and Rev C (`REVISED`, carrying the seeded revision cloud) in issuance order.

### 10.6 Frontend

Next.js 16 (App Router, Turbopack), TypeScript, Tailwind CSS v4, shadcn/ui — scaffolded via `create-next-app`/`shadcn init` rather than hand-rolled, so the tooling itself matches current upstream conventions rather than this assistant's training-data assumptions about Next.js (the installed version's own `AGENTS.md` warns training data may be stale for breaking API changes; its bundled docs were read before writing any page).

Pages: `/login`, `/dashboard`, `/projects` (Project Explorer), `/projects/[projectId]/rfis` (RFI Register), `/projects/[projectId]/rfis/[rfiId]` (RFI Detail) — exactly Plan v2 §17's RES-1 scope, no more, no less. Drawing Register/Detail/Timeline, Submittal Register, Specification Browser, Location Hierarchy, and Activity Feed are explicitly deferred to RES-2/RES-3/RES-4 per the approved milestone table, even though the backend already exposes enough (`documents`, `documents/{id}/versions`) to build some of them now — resisted per the plan's own discipline against building ahead of the milestone that calls for it.

Every page is a client component calling the backend's own REST API with `credentials: "include"` (`src/lib/api-client/`) — no bypass, no fabricated data. Auth state is never cached client-side; every protected page asks the backend's `GET /auth/session` on mount and redirects to `/login` on a 401 (`src/lib/auth/use-session.ts`).

**One backend addition beyond the original plan**, made while building the RFI Detail page: `GET /rest/v1.0/projects/{project_id}/documents/versions/{version_id}` — RFIs reference `DrawingVersion` IDs directly (per `docs/04`'s split `item_id`/`version_id` requirement), but the originally-planned document endpoints only supported listing versions *by drawing*, with no way to resolve a single cited version back to its sheet/revision label. This is a genuine gap discovered during implementation, not a scope expansion — the `GetDrawingVersion` use case already existed from RES-1's own domain/application layers, this only added the missing route.

**Verified:** `npm run build`, `npm run lint`, and TypeScript all pass clean. The login page's real HTML shell (title, form, seeded demo-password hint) was confirmed via direct HTTP request against a running dev server, and again against the containerized production build. Full interactive browser click-through (Playwright) was **not** performed — that's explicitly RES-5 scope in the approved plan, not RES-1.

### 10.7 Docker Compose

`infra/docker-compose.yml` gained three services: `reference-engineering-db` (Postgres 16, dedicated volume), `reference-engineering-backend` (port 8000), `reference-engineering-frontend` (port 3100, standalone Next.js build). `connector-procore`'s `depends_on` was updated to point at `reference-engineering-backend` instead of the now-deleted `mock-engineering-system`.

**A pre-existing, repo-wide path-resolution issue was discovered while verifying this**, and reconciled across two commits: Compose resolves every service's build context relative to the *compose file's own directory* (`infra/`), not the repo root — so every `apps/*` path (`./apps/connector-procore`, etc.), written as if relative to the repo root, has silently resolved to a nonexistent `infra/apps/connector-procore` since commit `49a12f8`. RES-1 (commit `cb53b04`) initially "fixed" this by documenting `--project-directory .`, which correctly repoints the `apps/*` paths — but the follow-up commit `d2c58b3` (made directly by the user) corrected the two new `reference-engineering-*` paths to `../reference-systems/...`, which is only correct under the *plain* invocation (no `--project-directory`), the opposite convention. `README.md`'s run instructions were updated to match the user's commit (plain `docker compose -f infra/docker-compose.yml up`) rather than reverting it, since that change was explicit and intentional. **Net state: the two `reference-engineering-*` services resolve correctly under plain invocation; the pre-existing `apps/*` paths remain broken under that same invocation, exactly as they were before RES-1 touched this file.** Neither is a regression from where the repo already stood — fixing `apps/*` is real, deferred work for whenever the first of those services gets real build content.

**Verified against the actual containers, not just `config`:** built both images, brought up all three services via `docker compose ... up -d`, ran `alembic upgrade head` and the seed script *inside* the running backend container, then confirmed login + the full RFI-214 fetch from the host machine against the containerized backend, and confirmed the frontend container serves `/login` with a 200. All three containers were stopped (not removed) afterward.

**Known, pre-existing, out-of-scope issue left as-is:** `mock-erp`'s build path (`./infra/mocks/mock-erp`, resolved relative to `infra/`) points at a folder that was renamed to `infra/mocks/Reference Commercial System/` in commit `37b29c4` without updating `docker-compose.yml` — under the now-confirmed plain-invocation convention the correct relative path would be `./mocks/Reference Commercial System`. Not fixed here because Commercial System work is an explicit non-goal of this phase; flagged in both `docker-compose.yml` itself (inline comment) and here so it isn't silently forgotten.

### 10.8 Testing

20 new backend tests, all passing, run alongside the existing 201 `packages/*` tests (root `pyproject.toml` unaffected — this system has its own separate `pyproject.toml`/`pytest` config, not merged into the root one, since it's a fully independent subsystem):
- `tests/unit/domain/` — RFI and DrawingVersion state machine transitions, `PermissionScope` scoping logic.
- `tests/unit/application/` — use cases tested against in-memory fake repositories (`tests/unit/application/fakes.py`), zero database — proving the port/adapter split actually buys the testability Clean Architecture is supposed to buy, not just adding layers for their own sake.
- `tests/architecture/test_layer_boundaries.py` — parses every `.py` file under `domain/` and `application/` with `ast` and asserts none of them import `fastapi`, `sqlalchemy`, `httpx`, `jwt`, or `api`/`infrastructure` — "business rules must never depend on FastAPI" as a checked fact, per your explicit instruction, not a convention someone could accidentally violate later.

### 10.9 What is explicitly NOT implemented yet (RES-2 through RES-5)

- **Webhook dispatch** — no thin-payload webhook fires on RFI close yet (RES-2).
- **Rate limiting and pagination** (`X-Total`, `per_page`) — not implemented (RES-2).
- **Submittals, Vendor/Commitment, procurement-gate enforcement** — not implemented (RES-3).
- **DesignChange (ASI/Bulletin/CCD/ChangeOrder), ChangeEvent/PCO/COR, FieldIssue, ClashItem, Transmittal** — not implemented (RES-4).
- **ScheduleActivity, ModelObject** — not implemented (RES-5).
- **Drawing Register/Detail/Revision Timeline, Submittal Register, Specification Browser, Location Hierarchy, Activity Feed pages** — backend groundwork exists for some (documents, spec_sections, locations), frontend pages deferred per plan (RES-2 through RES-4).
- **Playwright e2e suite** — RES-5.
- **`tests/contract/`** (the docs/04-mandated behavioral fidelity suite — thin webhook shape, 429 on rate limit) — depends on webhook dispatch and rate limiting existing first (RES-2/RES-3).

### 10.10 How to verify this state yourself

```bash
cd reference-systems/reference-engineering-system/backend
python -m venv .venv && .venv/Scripts/pip install -e ".[dev]"
# point RES_DATABASE_URL at a running Postgres, then:
.venv/Scripts/python -m alembic upgrade head
.venv/Scripts/python -m pytest -q
# expected (as of RES-2): 41 passed — see §11.8
```

```bash
# from the repo root
docker compose -f infra/docker-compose.yml up -d --build reference-engineering-db reference-engineering-backend reference-engineering-frontend
docker exec <backend-container> python -m alembic upgrade head
docker exec <backend-container> python -m seed.run_seed
curl http://localhost:8000/health
curl http://localhost:3100/login
```

---

## 11. Phase 4 — Reference Engineering System: RES-2

**Task given:** before starting RES-2, review RES-1 for non-behavioral architectural improvements (explicitly: improve, don't redesign); then implement RES-2 exactly as scoped in Plan v2 §17 — webhook dispatch (RFI only), rate limiting, pagination on the backend; Drawing Register, Drawing Detail, Drawing Revision Timeline, and Activity Feed on the frontend. Maintain Clean Architecture boundaries, keep all tests passing, add comprehensive tests for every new feature.

### 11.1 Pre-RES-2 review: two real findings, fixed

1. **`api/deps.py` had ~10 near-identical `get_X_repo` provider functions** (session → repo, five lines each). Replaced with a `_repo_provider(repo_cls)` factory — each provider is now a one-line call. Zero behavior change.
2. **`locations.py`'s list endpoint was missing the `ctx.can_see("locations")` scope check** that every other list endpoint (`rfis`, `documents`, `spec_sections`) already had — a genuine inconsistency, not a design choice: a partially-scoped integration credential could see *all* locations regardless of its declared scope, silently violating the `acting_credential_scope` guarantee docs/04 is built around. Fixed by extracting the repeated `if not ctx.can_see(...): raise HTTPException(404)` pattern (used identically in `documents.py` and `rfis.py`) into `ActingContext.require_scope()`, and adding the missing check to `locations.py`. Verified live: a partial-scope OAuth token that previously got all 4 seeded locations now gets `[]`, matching the same token's already-correct behavior on `spec_sections`.

Both changes were made and verified (20/20 tests green) *before* any RES-2 code was written, per the instruction to review first.

### 11.2 Architectural summary

New Application-layer port: `WebhookDispatcherPort` (`dispatch(subscription, payload) -> bool`, never raises — a delivery failure is a fact to record, not an exception that should roll back the domain transition that triggered it). New domain entities: `WebhookSubscription`, `WebhookDelivery` — kept in `domain/` because "which resource/event-type this project has asked to be notified about" and "what was attempted" are real business facts of this system's own domain (mirroring how real Procore's webhook registrations are themselves an owned resource), not infrastructure incidental. Rate limiting, by contrast, was kept **entirely out of domain and application** — it's a protocol-level concern of exposing this system as an HTTP API (no engineering-domain meaning), implemented as `infrastructure/rate_limit/store.py` plus a single `api/deps.py` dependency (`enforce_rate_limit`), never touching `domain/` or `application/` at all. This distinction — model what's a real business fact as a domain entity, keep what's purely a wire/protocol concern out of the domain — is the main architectural judgment call this milestone made.

`CloseRFI` (the one use case with a side effect worth persisting) grew three new constructor dependencies (`webhook_subscription_repo`, `webhook_delivery_repo`, `webhook_dispatcher`) — still fully testable with in-memory fakes and zero database, per `tests/unit/application/test_rfi_use_cases.py`'s new webhook-dispatch tests. Pagination was deliberately implemented at the **API layer** (`api/pagination.py`), not inside use cases — `page`/`per_page` are HTTP concepts, and putting them in the application layer would leak a wire concern into code that's supposed to be transport-agnostic. Pagination is in-memory (paginate the full list the use case already returns) rather than pushed into the SQL query — a deliberate, stated simplification appropriate at this system's current data scale, not a performance oversight (see §11.9).

### 11.3 Migration summary

Two new migrations, applied cleanly from a running RES-1 database (0001–0004 already applied) and, separately, verified from an empty database alongside 0001–0004 in one `alembic upgrade head` run:

- **`0005_webhooks`** — `webhook_subscriptions` (id, project_id, resource_name, event_type, target_url, secret) and `webhook_deliveries` (id, project_id, subscription_id, resource_name, resource_id, event_type, occurred_at, status, dispatched_at) — the latter is the append-only log the Activity Feed reads from.
- **`0006_rate_limit_state`** — `rate_limit_state` (client_id PK, window_start, request_count) — a fixed-window counter per OAuth `client_id`.

Schema-vs-ORM-metadata diff (same method as RES-1's verification) confirmed an exact match after both migrations.

### 11.4 API changes

**New:**
- `POST /webhook_subscriptions?project_id=` / `GET /webhook_subscriptions?project_id=` — this system's own admin/setup surface (not Procore-shaped, kept outside `/rest/v1.0/` and outside the rate-limit budget, matching how registering a webhook is a one-time Developer-Portal action on real Procore, not a resource API call).
- `GET /rest/v1.0/projects/{project_id}/activity` — backs the Activity Feed, reads the `WebhookDelivery` log.

**Changed (backward-compatible additions, no existing field removed or renamed):**
- `GET /rest/v1.0/projects/{project_id}/rfis`, `.../documents`, `.../spec_sections`, `.../locations` now accept `?page=&per_page=` (default `page=1`, `per_page=20`, max `per_page=100`) and set an `X-Total` response header — matching docs/04's pagination requirement, verified via contract test.
- `PATCH /rest/v1.0/projects/{project_id}/rfis/{rfi_id}/close` now dispatches a webhook (see §11.5) as a side effect — the response shape is unchanged, only the side effect is new.
- Every route under `/rest/v1.0/` now enforces a per-`client_id` rate limit (OAuth2 traffic only — human sessions are exempt); exceeding it returns `429` with a `Retry-After` header.

### 11.5 Webhook dispatch — verified against a real HTTP server, not just a fake

On `PATCH .../rfis/{id}/close`, `CloseRFI` looks up every `WebhookSubscription` matching `(project_id, "rfis", "update")`, builds the exact five-field thin payload from Reference Trace Phase 0 (`resource_name`, `resource_id`, `project_id`, `event_type`, `timestamp` — nothing else), HMAC-signs it (`X-Signature: sha256=...`), POSTs it (one retry on connection failure, then logged and dropped — no dead-letter queue, explicitly deferred), and records a `WebhookDelivery` row (`SENT` or `FAILED`) regardless of outcome. A delivery failure never rolls back the RFI's own state transition.

**End-to-end verification performed**, beyond the automated contract test: started a real local HTTP server, seeded a subscription pointing at it, closed a real RFI through the real running API, and confirmed the server received a POST with the exact five JSON keys and a signature that independently recomputing `hmac.new(secret, body, sha256)` matched byte-for-byte.

The default seeded webhook target is `http://localhost:9999/webhook-sink` (overridable via `RES_SEED_WEBHOOK_TARGET_URL`) — a placeholder receiver, since no real subscriber exists yet; this is exactly the seam a future Connector-Procore would attach to.

### 11.6 Rate limiting

Fixed-window counter, one row per `client_id` in `rate_limit_state`. Default budget: 3,600 requests/hour (matching the real Procore ceiling docs/04 cites), configurable via `RES_RATE_LIMIT_MAX_REQUESTS`/`RES_RATE_LIMIT_WINDOW_SECONDS`, overridden to a tiny budget in tests. Applies only to Bearer-token (OAuth2 integration-client) traffic — human sessions are never throttled, matching docs/04's framing of this as an API-client concern.

**One real bug found and fixed during verification:** the first implementation mutated `response.headers["Retry-After"]` on the injected `Response` object before raising `HTTPException`. FastAPI discards that `Response` once an exception is raised and builds a fresh error response from scratch, so the header never actually reached the client — the contract test caught this immediately (`assert "Retry-After" in response.headers` failed against a real request). Fixed by passing `headers={"Retry-After": ...}` directly to `HTTPException`, which does propagate. Documented here because it's a genuinely non-obvious FastAPI behavior worth remembering.

### 11.7 Frontend changes

New pages, consuming only real backend endpoints (`credentials: "include"`, no bypass):

| Route | Backed by |
|---|---|
| `/projects/[projectId]/drawings` | `GET .../documents` — sheet number, title, discipline |
| `/projects/[projectId]/drawings/[drawingId]` | `GET .../documents/{id}` + `.../documents/{id}/versions` — the Revision Timeline is embedded here as a vertical timeline (newest first), showing each version's status badge, revision clouds, supersession pointer, and a "Current" marker tied to `Drawing.current_version_id` — not a separate route, consistent with how the backend already models a version as a child of its drawing |
| `/projects/[projectId]/activity` | `GET .../activity` — reads the same `WebhookDelivery` log webhook dispatch writes to, per the plan's explicit instruction to reuse that stream rather than invent a second one |

`AppShell`'s project-context nav gained "Drawings" and "Activity" links. `npm run build` and `npm run lint` both pass clean with the new routes.

Pagination controls (page/per_page UI) were **not** added to the frontend — the backend's pagination fidelity (docs/04's stated requirement) didn't imply a UI requirement, and with the current seed data's small row counts a pager would be inert. Noted in §11.9 as a scope boundary, not an oversight.

### 11.8 Test results

**41 backend tests, all passing** (20 carried over from RES-1 + 21 new), across four tiers:
- `tests/unit/domain/` — unchanged from RES-1.
- `tests/unit/application/` — new: `CloseRFI` webhook-dispatch tests against `FakeWebhookDispatcher`/in-memory subscription+delivery repos (dispatches to matching subscriptions with the exact 5-key payload; records `FAILED` without raising when the dispatcher reports failure; ignores subscriptions for other resource types). New: `application/webhook_payloads.py`'s exact-key-set assertion.
- `tests/unit/api/` (new tier) — `paginate()` math (first page, last partial page, page beyond range).
- `tests/unit/infrastructure/` (new tier) — HMAC signing determinism/secret-sensitivity.
- `tests/integration/` (new tier) — `RateLimitStore` against a real Postgres connection (rollback-isolated per test): allows under budget, denies over budget with a positive `retry_after`, resets after the window elapses, independent budgets per `client_id`.
- `tests/contract/` (new tier) — full `TestClient(app)` + real database, real committed-and-torn-down fixture rows (not rollback-isolated, since the app's own request-handling connection is separate from the test's): the exact thin-payload contract test (asserts the dispatched payload's key set, catches any future "helpful" field addition), the 429 + `Retry-After` contract test (the one that caught the header bug above), a human-sessions-are-never-rate-limited test, and three pagination contract tests (`X-Total` header, `per_page=0` rejected with 422, page-beyond-range returns `[]` with an accurate total).
- `tests/architecture/test_layer_boundaries.py` — unchanged, still passing with the new `domain/entities/webhook.py` and `application/ports/webhook_dispatcher_port.py` in place (confirms they don't import FastAPI/SQLAlchemy).

Frontend: `npm run build` and `npm run lint` clean, zero errors/warnings.

**Full-stack verification**: rebuilt both Docker images, brought up `reference-engineering-db`/`-backend`/`-frontend` via Compose, ran migrations 0001–0006 and the seed script inside the running backend container, then re-ran the real-HTTP webhook test (§11.5) and a rate-limit smoke check against the containerized backend.

### 11.9 Known limitations

- **In-memory pagination** — `paginate()` slices the full result list the use case already fetched, rather than pushing `LIMIT`/`OFFSET` into SQL. Correct and simple at this system's current row counts; would need revisiting before real production data volumes.
- **No dead-letter queue or retry/backoff schedule for webhook dispatch** — one retry, then logged and dropped, per the approved plan's explicit RES-2 scope boundary (real retry/backoff is Synchronization Service territory in a much later Downstream milestone, not this system's job).
- **No frontend pagination UI** — the backend's pagination is real and tested; nothing in the UI exposes `page`/`per_page` yet.
- **No Playwright/browser-automation test suite** — RES-5 scope per the approved plan. One manual headless-Chrome screenshot of the login page was captured for this summary (see chat); authenticated-page screenshots would require a scripted login session, not attempted here to stay within RES-2's scope.
- **`docker-compose.yml`'s pre-existing `apps/*` path-resolution issue remains unfixed** — see §10.7's updated account; still out of scope, still not a regression.
- **Webhook coverage is RFI-only as of RES-2** — DrawingVersion/Submittal webhook coverage was floated for RES-3; see §12.9 for what RES-3 actually shipped (Submittal, not DrawingVersion) and why.

---

## 12. Phase 5 — Reference Engineering System: RES-3

**Task given:** implement the approved RES-3 Implementation Contract — Submittals (parent/child revisioning per ADR-004), a configuration-driven procurement-release gate (ADR-003), Submittal Packages (ADR-005), Vendors, minimal Commitments, the spec-driven Submittal Register, and the corresponding frontend — preceded by a review of `The Enterprise Fidelity Review.md`, `Canonical_Demo_Dataset.md`, and every frozen/reference document to confirm no entity introduced required a new domain model outside those two sources (see the entity-verification turn preceding this contract; full detail there, not repeated here).

### 12.1 Architectural summary

Three ADRs govern this milestone's structural decisions, all recorded as their own files (`docs/adr/ADR-003.md`, `ADR-004.md`, `ADR-005.md`) matching the existing ADR-001/002 precedent:

- **ADR-003** — `SubmittalReviewStatus` is a seeded, project-scoped config table (`code, label, gates_procurement, is_terminal, sort_order`), not a closed Python enum like `RFI.status`/`DrawingVersion.status`. The domain state machine (`domain/state_machines/submittal_transitions.py`) enforces transition *shapes* generically off the `is_terminal`/`gates_procurement` booleans — it never matches a specific status code, so the whole gate mechanism works for any customer-configured vocabulary, not just the nine seeded defaults.
- **ADR-004** — `Submittal` (envelope: project, spec_section, package, vendor, commitment, lead time) + `SubmittalRevision` (per-revision: review_status, ball_in_court, equipment fields, drawing/location refs) — the same parent/child pattern already proven for `Drawing`/`DrawingVersion` in RES-1, applied here because Intelligence Spec §13's canonical demo trigger requires diffing one revision's equipment schedule against the prior one, which a scalar `rev` field (the frozen doc's literal depiction) cannot support.
- **ADR-005** — `SubmittalPackage` is a new grouping entity sourced from the Fidelity Review (absent from `The Reference Engineering System.md`'s entity list). Implemented as a real, functional table; `submittals.package_id` is nullable and the seed data instantiates zero packages, matching `Canonical_Demo_Dataset.md`'s own scoping.

Vendor/Commitment stayed deliberately minimal — no `lifecycle_position`, no fabrication/shipped tracking — per the entity verification's finding that rich, lifecycle-bearing PO records (the Enterprise Fidelity Review's `po_5201`/`po_5202`/`req_5203`) belong entirely to the not-yet-built Reference Commercial System, never to RES-3's own domain model. `SUB-118`'s `commitment_id` is `NULL` in seed data for exactly this reason.

### 12.2 Migration summary

Four new migrations, verified from a completely empty database (both an ad-hoc local Postgres and, separately, inside the actual `reference-engineering-db` container) alongside `0001`–`0006`:

| # | Contents |
|---|---|
| `0007` | `vendors`, `commitments` |
| `0008` | `submittal_packages` (ADR-005), `submittal_review_statuses` (ADR-003) |
| `0009` | `submittals`, `submittal_revisions` (ADR-004), `submittal_drawing_refs`, `submittal_location_refs` |
| `0010` | `submittal_requirements` (the spec-driven register) |

Schema-vs-ORM-metadata diff confirmed an exact match after all ten migrations, using the same method established in RES-1.

### 12.3 API endpoints

```
GET   /rest/v1.0/projects/{project_id}/submittals
GET   /rest/v1.0/projects/{project_id}/submittals/{submittal_id}
GET   /rest/v1.0/projects/{project_id}/submittals/{submittal_id}/revisions
GET   /rest/v1.0/projects/{project_id}/submittals/revisions/{revision_id}
PATCH /rest/v1.0/projects/{project_id}/submittals/{submittal_id}/revisions/{revision_id}/disposition
GET   /rest/v1.0/projects/{project_id}/vendors
GET   /rest/v1.0/projects/{project_id}/submittal_requirements
GET   /rest/v1.0/spec_divisions
```

All mounted in the existing rate-limited `_rest` router group — inherited `enforce_rate_limit`, `PageParams`/`paginate()`, and `ActingContext.require_scope()` automatically, with zero new cross-cutting code. `/spec_divisions` is global (no `project_id` — `SpecDivision` has no such column) and requires authentication but no resource-scope check, since `PermissionScope` binds to a project and CSI MasterFormat divisions are shared reference data.

### 12.4 Frontend functionality

| Route | What it shows |
|---|---|
| `/projects/[id]/submittals` | Register: number, spec section, ball-in-court, gate-colored status badge (green when `gates_procurement`, red when not — never keyed to a specific status code, per ADR-003), long-lead flag |
| `/projects/[id]/submittals/[id]` | Revision timeline (mirrors Drawing Detail), equipment tag/manufacturer/model/capacity per revision, a long-lead warning banner, vendor |
| `/projects/[id]/specifications` | CSI Division → Section tree, each section's submittal register requirements |

Nav gained "Submittals" and "Specifications" links. `npm run build`/`lint` clean (TypeScript checked as part of `next build`).

### 12.5 Seed data

Extends `meridian_tower.py` exactly per `Canonical_Demo_Dataset.md` §2–9 — Discipline `E`, SpecDivision `26`/SpecSection `26 24 13`, SpecSection `23 74 13`, three new Locations (Level 1, Level 1 Electrical Room, Roof), three new Vendors (Coastal Aire Equipment, Voltrex Switchgear Inc., Ferro Electrical Supply — the latter two unused by any Commitment in RES-3, seeded for continuity per the canonical dataset's own instruction), nine `SubmittalReviewStatus` rows, and `SUB-118` seeded through its **real domain state machine** (create → `submit_revision` → `record_disposition`) for both Rev 0 (→ `REVISE_AND_RESUBMIT`, disposed by Kabir Mehta) and Rev 1 (→ `NO_EXCEPTIONS_TAKEN`, disposed by Rhea Fernandes) — not inserted pre-disposed, matching the discipline already established for RFI-214's own seeding. RFI-214 and all RES-1/RES-2 fixtures are untouched. A `submittals`/`update` webhook subscription was added alongside the existing `rfis`/`update` one.

### 12.6 Webhook behavior

`RecordSubmittalDisposition` dispatches on **every** disposition change — gating or blocking — exactly mirroring `CloseRFI`'s always-fire pattern, never rolling back the disposition itself on a delivery failure. **Verified against the actual running application, twice:** once via a real local HTTP receiver (independently-recomputed HMAC signature matched byte-for-byte, exact 5-key payload confirmed), and once inside the Docker Compose stack, where the seeded target (`localhost:9999`, unreachable from inside the container) produced the correct `FAILED`-but-recorded outcome in the Activity Feed without blocking the disposition's own 200 response — the identical resilience proof already established for RFI webhooks in RES-2, now confirmed for `resource_name="submittals"` too.

### 12.7 Tests

**20 new tests, 61 total, all passing** (verified twice in a row from a freshly-migrated, empty schema, confirming no hidden state dependency):
- `tests/unit/domain/test_submittal_transitions.py` — `submit_revision`, `record_disposition` (gating → `ball_in_court="closed"`, blocking → `ball_in_court="submitter"`), terminal-status rejection, current-status-mismatch rejection.
- `tests/unit/application/test_long_lead.py` — the pure `is_long_lead()` function, including both "not computable" (missing field) cases.
- `tests/unit/application/test_submittal_use_cases.py` — `RecordSubmittalDisposition` against in-memory fakes, asserting the exact 5-key webhook payload and that both gating and blocking dispositions dispatch.
- `tests/integration/test_submittal_repository.py` — real-Postgres round trip for `Submittal`/`SubmittalRevision`, confirming `gates_procurement` survives the repository boundary.
- `tests/contract/test_submittal_webhook_and_gate.py` — full `TestClient(app)` + real DB: exact thin-payload shape, gating vs. blocking API response shape, 409 on re-disposing a terminal revision, `X-Total` pagination header.

### 12.8 Bugs discovered and fixed during verification

1. **A genuine test-design bug** (not a production bug): `test_record_disposition_rejects_mismatched_current_status` originally passed a *terminal* status as the deliberately-mismatched `current_status`, so it hit the (correct) terminal-check branch before ever exercising the mismatch-check branch it was meant to isolate. Fixed by introducing a second, non-terminal status (`SUBMITTED`) for that specific test.
2. **A genuine test bug, caught only by running the suite against a truly empty schema**: the new contract tests hardcoded `disposed_by_user_id: 1`, which happened to succeed against the shared dev database only because a leftover row with `id=1` existed from earlier manual verification — against a fresh schema it failed with a foreign-key violation. Fixed by having `submittal_contract_fixture` create a real `User` row and having the tests reference its actual id. This is exactly the class of bug the "apply from a completely empty database" requirement exists to catch, and it did.

No production code changes were required for either fix — both were test-fixture corrections.

### 12.9 Remaining limitations

- **DrawingVersion webhook coverage was not added** — the approved RES-3 Implementation Contract's file/endpoint list named only Submittal changes; an earlier planning-stage document had floated DrawingVersion too, but per the explicit instruction not to expand scope beyond the approved contract, only what the contract specified was built. Revisit in a future milestone if DrawingVersion-triggered events are needed.
- **Submittal Package (ADR-005) is unused** — the entity is real and fully functional, but no seed data instantiates one, matching `Canonical_Demo_Dataset.md`'s own scope.
- **`SubmittalReviewStatus` vocabulary has no admin/config API** — it's seeded, config-driven storage (ADR-003), but nothing lets a user add a custom status at runtime yet; "configurable" is honored at the storage layer, not via a live UI.
- **No Design Change, Field Issue, ClashItem, Transmittal, ScheduleActivity, or ModelObject** — all remain RES-4/RES-5 scope per the approved RES-3 plan's re-scoping (§3 of that plan).
- **Scenario B ("The HVAC Upsize") is only half-producible** — RES-3 makes the Submittal-side trigger (`SUB-118` Rev 1 → `NO_EXCEPTIONS_TAKEN`) real and API-visible, exactly matching Intelligence Spec §13's canonical demo walkthrough's own starting condition. The commercial-side artifacts it should eventually resolve to (`po_5201`, `po_5202`, `req_5203`) remain specification-only in `Canonical_Demo_Dataset.md` §10, pending the Reference Commercial System.
- **`docker-compose.yml`'s pre-existing `apps/*` path issue remains unfixed** — unchanged from RES-2, still out of scope.

### 12.10 How to verify this state yourself

```bash
cd reference-systems/reference-engineering-system/backend
.venv/Scripts/python -m alembic upgrade head
.venv/Scripts/python -m pytest -q
# expected: 82 passed
```

```bash
docker compose -f infra/docker-compose.yml up -d --build reference-engineering-db reference-engineering-backend reference-engineering-frontend
docker exec <backend-container> python -m alembic upgrade head
docker exec <backend-container> python -m seed.run_seed
curl http://localhost:8000/rest/v1.0/projects/1/submittals   # (with an Authorization header — see backend/README.md)
curl http://localhost:3100/projects/1/submittals
```
---

## 13. PRE-RES-4 stabilization (2026-08-07)

A small, focused stabilization patch applied *before* RES-4 begins. This is
**not** RES-4 — no Design Change / ASI / CCD / Bulletin, no DrawingVersion
issuance/webhook, no new webhook behavior, no PDF ingestion / OCR / RAG. It
corrects three defects found during the handoff review and adds the missing
data-fidelity for Scenario B.

### 13.1 Defects corrected

- **Activity Feed was unauthenticated.** `GET /rest/v1.0/projects/{id}/activity`
  previously had no `get_acting_context` dependency (only router-level rate
  limiting, which is a no-op without a bearer token). Now it requires an
  authenticated `ActingContext`, enforces project ownership, and enforces the
  `activity` resource scope (under-scoped clients get an empty list).
- **Project isolation was not actually enforced.** Every authenticated
  project-scoped route now verifies the `ActingContext` belongs to the URL's
  project (`ActingContext.require_project`). Get-by-id and mutation endpoints
  additionally verify the fetched resource belongs to that project
  (`ensure_resource_in_project`), so a caller can never reach or mutate
  another project's record through their own project path. The project
  catalog (`GET /projects`, `GET /projects/{id}`) now requires authentication
  and only exposes the caller's own project, consistent with the rest of RES
  (no frozen doc requires a public catalog; docs/03 mandates hard
  project partitioning).
- **SUB-118 lost FLA.** Only MCA was modeled (via `capacity_value`/unit,
  seeded as `A_MCA`). FLA is now a first-class, nullable revision field.
  Canonical values:

  | Rev | MCA | FLA |
  |---|---|---|
  | Rev 0 | 180 A | 150 A |
  | Rev 1 | 240 A | 200 A |

### 13.2 ADR added

- **ADR-006** — MCA and FLA are explicit, nullable, first-class engineering
  fields on `SubmittalRevision` (a scalar pair mirroring `capacity_value`/
  `capacity_unit`), deliberately **not** a generic electrical-properties
  framework, per Canonical_Demo_Dataset.md's own "fields, not an entity"
  directive. Backward compatible: existing rows stay NULL until a revision
  supplies FLA.

### 13.3 Migration added

- **`0011_submittal_fla.py`** — adds `fla_value` (`Numeric(10,2)`, nullable)
  and `fla_unit` (`String(20)`, nullable) to `submittal_revisions`.

### 13.4 Tests added

- `tests/unit/api/test_project_guards.py` — unit coverage of
  `ActingContext.require_project` and `ensure_resource_in_project` (404-hide).
- `tests/contract/test_project_isolation.py` — two-project fixture proving,
  for **both** human-session and OAuth-integration auth: cross-project
  get-by-id and list → 404; cross-project mutation → 404; resource-project
  mismatch via one's own path → 404; project catalog requires auth and only
  exposes one's own project; activity requires auth (401), same-project
  succeeds (200), cross-project → 404, under-scoped integration → isolated.
- `tests/contract/test_submittal_webhook_and_gate.py::test_submittal_revision_response_exposes_mca_and_fla`
  — MCA+FLA round-trip through the API.
- `tests/integration/test_submittal_repository.py` — extended round-trip to
  assert FLA is persisted and read back.

### 13.5 Final test counts

Backend full suite: **82 passed** (unit + architecture + contract +
integration) against a freshly migrated empty Postgres schema.

Frontend: `npm run build` (includes TypeScript check) succeeds for all routes;
the two changed TS/JSX files pass ESLint.

### 13.6 Known limitations (unchanged from §12.9)

- **DrawingVersion issuance/webhook gap** — intentionally **not** closed here;
  it belongs to RES-4's `IssueDrawingVersion` use case.
- All other §12.9 limitations (Submittal Package unused, no review-status
  admin API, scenario B half-producible on the commercial side, the
  `docker-compose.yml` `apps/*` path issue) are unchanged — out of scope for
  this stabilization.

---

## 14. Phase 6 — Reference Engineering System: RES-4A/B (Design Change family)

### 14.1 Scope and authority

RES-4 brings the **Design Change** family to the Reference Engineering
System — the first milestone that is not purely read/seed. Per ADR-007:

- One entity, `DesignChange`, with a **closed type enum**
  (`ASI`, `CCD`, `BULLETIN`) — the single engineering-authorization entity
  for the three in-scope instrument labels (RES's scope deliberately excludes
  the commercial ChangeOrder/PCO/COR chain, which belongs to the future
  Reference Commercial System).
- One lifecycle: `DRAFT -> ISSUED -> ACKNOWLEDGED`, with `SUPERSEDED` and
  `VOID` as terminal `SUPERSEDED`/`VOID` states (ADR-007).
- **No direct DesignChange–Submittal relationship** (ADR-007): a design change
  affects drawings/specs via `affected_drawing_version_ids` /
  `affected_spec_section_ids`, mirroring how a change becomes effective in the
  drawings.
- The issue step (`DRAFT → ISSUED`) emits the **thin webhook** for
  `resource_name="design_changes"`; acknowledge/void/supersede emit nothing
  (RES-4 approved decision).

### 2026-08-09 — RES-4A/B implementation (commits `7a9d075`, `d5b9611`)

**RES-4A — domain model:**
- `domain/entities/design_change.py` — dataclass + closed `DESIGN_CHANGE_TYPES`
  / `DESIGN_CHANGE_STATUSES`; `entity_validation` of type/status in
  `__post_init__`.
- `domain/state_machines/design_change_transitions.py` — pure
  `issue` / `acknowledge` / `supersede` / `void` transitions (nullable clocks).
- `domain/repositories/design_change_repository.py` and
  `tests/unit/domain/test_design_change_transitions.py` (state machine only,
  ADR-007's "no ORM/migration/API changes with RES-4A" boundary).

**RES-4B — the surface:**
- Migration `0012_design_changes.py` — `design_changes` + three join tables
  (`design_change_drawing_versions`, `design_change_spec_sections`,
  `design_change_locations`); `superseded_by_id` self-FK.
- ORM `orm_models/design_change.py`, repository
  `SqlAlchemyDesignChangeRepository` (with `_replace_refs` for the joins).
- Use cases (`application/use_cases/design_change_use_cases.py`): list/get
  (project-scoped), `issue` (with thin webhook via `WebhookDispatcherPort`),
  `acknowledge`, `void`, `supersede`.
- **`IssueDrawingVersion`** (`application/use_cases/drawing_use_cases.py`) —
  closes the RES-3 drawing-issuance gap: applies the legal
  DrawingVersion issuance transition, stamps the issuance date, supersedes the
  prior current version of the same sheet, repoints the Drawing at the newly
  issued version, and emits the thin `documents/update` webhook
  (resource_id = the issued version).
- API layer: `api/schemas/design_change.py` (`DesignChangeOut`),
  `api/v1/design_changes.py` (GET list/get, PATCH issue/acknowledge/void —
  with `ctx.require_project` / `can_see` / `require_scope` guards and
  correct 404 vs 403 semantics), `api/deps.py` wiring, `api/v1/router.py`.
- Architectural tests: unit tests for the new use cases
  (`tests/unit/application/test_design_change_use_cases.py`,
  `test_drawing_issue_use_cases.py`) plus fakes in
  `tests/unit/application/fakes.py`.

### Verification checkpoint (this session, 2026-08-09)

- **Test suite green**: 111 passed (was 82 at RES-3) — unit + architecture +
  integration + contract, run twice in a row against a freshly migrated
  Postgres schema.
- **Live smoke test** (backend on :8000, seeded Meridian Tower project):
  - `GET /rest/v1.0/projects/{id}/design_changes` → `200`, scoped, `X-Total`
    correct.
  - `GET .../design_changes/{id}` → returns `DesignChangeOut` with all
    contract fields (type/ball_in_court/status, etc.).
  - `PATCH .../design_changes/{id}/issue` → `ISSUED` with `issued_at`
    populated (the webhook-worthy step).
  - `PATCH .../design_changes/{id}/acknowledge` → `ACKNOWLEDGED` with
    `acknowledged_at`.
  - Smoke-test row cleaned up; DB left at canonical seed state.

### Link to RES-4C/D

RES-4C/D — the frontend Design Changes register + detail pages and the
canonical DesignChange/DWG-E-1.1 seed — now proceed under §15 below.

---

## 15. Phase 6 — Reference Engineering System: RES-4C/D

### 15.1 Scope

- **RES-4C (frontend):** the Design Changes Register and Design Change Detail
  pages behind the project shell, plus a register nav entry, a
  `DesignChangeStatusBadge`, and the `designChangesApi`/`DesignChangeOut`
  client wiring. The register is a server page that proxies to the backend;
  the detail page is a client component that loads the change via
  `GET .../design_changes/{id}` and renders its status, ball-in-court,
  affected drawings/specs/locations, and the issue→acknowledge timeline —
  wired into `AcknowledgeDesignChange` internally, with no client-side state
  forging.
- **RES-4D (canonical seed):** extends `meridian_tower.py` with the Design
  Change that the *Canonical Demo Dataset* (§8) prescribes and the project
  plan needs, in particular:
  - `DWG-E-1.1` (Electrical Plan — Level 1) as a `DRAWING`, starting at
    Rev 0 and being superseded to Rev 1 in the seed.
  - An **ASI-07** `DesignChange` (`type=ASI`) driving that supersession,
    issued via the ASI-07 issue use case, targeted at the DWG-E-1.1 Rev 1
    version and Spec 26 24 13 (no direct DesignChange→Submittal link, per
    ADR-007), plus `affected_drawing_version_ids` / `affected_spec_section_ids`
    / `location_ids` fill-in.
  - The default webhook subscription now also targets `design_changes` (in
    addition to `rfis` / `documents`), so issue/acknowledge of the seeded ASI
    dispatches the thin payload to the seeded webhook.
  - `design_change_repo` + imports added to the seed.

### 15.2 Verification

- `tests/integration/test_seed_data.py` — a new **seed assertion test**: seeds
  the canonical dataset inside a rolled-back transaction and asserts the
  resulting shape (supersession + ASI present, drawing superseded pointer,
  spec/locations, and RFI-214 stays the only Scenario-A trigger). This proves
  the canonical seed is idempotent and future-proof — it runs whether or not
  `run_seed` has been executed against the DB.
- Full backend suite: **112 passed** (was 111 at §14) including the new seed
  test, run against the migrated schema.
- Frontend: `npm run build` (incl. real TypeScript check) + targeted ESLint
  clean; live dev-server smoke of `/projects/1/design-changes` and
  `/.../design-changes/1` returned 200 with the seeded ASI-07 data.

### 15.3 Files

- `backend/src/seed/meridian_tower.py` — DWG-E-1.1 + ASI-07 seed, webhook
  subscription.
- `backend/tests/integration/test_seed_data.py` — seed assertion test.
- `frontend/src/app/projects/[projectId]/design-changes/page.tsx` — register.
- `frontend/src/app/projects/[projectId]/design-changes/[changeId]/page.tsx`
  — detail.
- `frontend/src/components/status-badge.tsx` — `DesignChangeStatusBadge`.
- `frontend/src/components/app-shell.tsx` — nav entry.
- `frontend/src/lib/api-client/types.ts`, `index.ts` — `DesignChangeOut` +
  `designChangesApi`.

### 15.4 Next

Begin the next milestone only when §15's verification passes, the status is
updated, and the git checkpoint is committed. RES-4E/F/G are defined under §16
below.

---

## 16. Phase 6 — Reference Engineering System: RES-4E/F/G

### 16.1 RES-4E — API contract suite + canonical RFI-source link (commit `fa48f44`)

- `tests/contract/conftest.py` — contract fixtures that stand up the real API
  surface (asgi transport, auth, scope) against a DB session.
- `tests/contract/test_design_changes_api.py` — end-to-end contract tests:
  auth required, seeded rows with `X-Total`, pagination, contract-field shape,
  scoped-integration 404 semantics, cross-project isolation, webhook dispatch
  on `issue` including a recorded `webhook_deliveries` row and the 409
  already-issued case, per-client rate limiting.
- The canonical seed now carries the **ASI-07↔RFI-214 source link**
  (`source_rfi_id`), per the RES-4E contract: ASI-07 stays a closed-loop
  annotation on the Scenario-A RFI and must *not* spin up a new trigger chain.
  Asserted in `tests/integration/test_seed_data.py`.

### 16.2 RES-4F — project isolation + scope containment (contracts)

- `tests/contract/test_project_isolation.py` — human-vs-integration and
  cross-project 404 semantics for projects, RFIs, activity, and mutations
  (`get_project_cross_project_is_404`, `integration_cross_project_get_rfi_is_404`,
  `cross_project_mutation_respond_is_404`, under-scoped integration cannot
  retrieve, same-project full-scope success).
- Confirms RES-3's project-isolation guards hold for the Design Change paths
  too (`test_design_changes_*` cross-project / scope / mismatch 404s).

### 16.3 RES-4G — final verification + checkpoint (this session, 2026-08-10)

Full re-verification from a **completely fresh schema**, not the persistent
test DB:

- **Fresh DB**: `reference_engineering` dropped and recreated on the
  `res-test-db` container; all 12 alembic migrations ran clean
  (`alembic upgrade head`), then `meridian_tower.py` seeded on the empty schema.
- **Full backend suite**: **127 passed** against the fresh schema (was 112 at
  §15) — unit + architecture + integration/contract, including the seed
  assertion test and the design-changes contract/project-isolation suites.
  `tests/architecture/test_layer_boundaries.py` passes.
- **Frontend**: `npm run build` (incl. real TypeScript) + targeted ESLint on
  design-changes routes/components/api-client — clean.
- **Live API smoke** (backend on :8000, seeded Meridian Tower):
  - login → `GET .../design_changes` (listed), `GET .../design_changes/1`
    detail = ASI-07 ISSUED with all contract fields.
  - `PATCH .../design_changes/{id}/issue` → ISSUED with `issued_at`;
    `PATCH .../documents/versions/{id}/issue` → ISSUED; each recorded a thin
    `webhook_deliveries` row (FAILED = no receiver on :9999, as expected).
  - Smoke rows + delivery rows cleaned up; DB restored to canonical seed.
- **Data facts re-verified on the fresh DB**:
  - RFI-214 (Scenario A) CLOSED, sole trigger chain; spawned ASI-07.
  - SUB-118 Rev 0 (CA-RTU-40, MCA 180 A, FLA 150 A) → Rev 1 (CA-RTU-55,
    MCA 240 A, FLA 200 A) — Scenario B equipment data preserved verbatim.
  - ASI-07 ISSUED, `source_rfi_id = RFI-214`, affects DWG-E-1.1 Rev 1 + switchgear
    spec section + electrical-room location; **not** a Scenario-B trigger.
  - DWG-E-1.1: Rev 0 `SUPERSEDED`, superseded-by Rev 1 (`ISSUED`, current).
  - Thin webhook subscriptions intact (`rfis`, `submittals`, `design_changes` →
    the :9999 sink).
- **Repo hygiene**: working tree clean, `git diff --check` clean, no commit on
  this session's doc updates (per standing instruction).

---

## 17. Phase 7 — Reference Engineering System: RES-5 (ScheduleActivity, ModelObject)

### 17.1 Scope, authority, and a flagged contradiction

RES-5 completes the entity list `The Reference Engineering System.md` §16
names and RES-4 explicitly deferred: `ScheduleActivity` and `ModelObject`
(ADR-008). Per the approved RES-5 milestone scope: these two entities, their
required relationships/APIs, contract/architecture tests, frontend
navigation/UX, Playwright E2E coverage, Docker/README/final verification,
and canonical seed-data integration where already approved — **not**
`FieldIssue`, `ClashItem`, `Transmittal`, or any Downstream/Reasoning
Pipeline work.

**Flagged, not silently resolved (per instruction):** no standalone "RES-5
plan" document exists anywhere in this repository or its git history — RES-5
scope is derived entirely from the reference docs
(`The Reference Engineering System.md` §16), `Canonical_Demo_Dataset.md`
§10/§13/§21, and the RES-5 boundary already stated consistently across
`IMPLEMENTATION_STATUS.md` §10.9/§12.9, `RES-1_USER_GUIDE.md`, and
`docs/engineering/RES_IMPLEMENTATION_CONTEXT.md` ("RES-5 and Field Issues
remain not started" — two separate items). `ADR-007`'s own line "FieldIssue
is RES-5" contradicts that consistent framing; RES-5 as implemented here
follows the majority framing and the explicit instruction that opened this
milestone (which does not list FieldIssue), and does **not** build
FieldIssue. Recorded in `ADR-008` as well as here so the contradiction is not
lost.

The repository was verified at the expected RES-4 state before this
milestone began: `IMPLEMENTATION_STATUS.md` §16 (RES-4G) matched `HEAD`
(`f64d1ad`) exactly, and the full backend suite reproduced the documented
127-passed baseline before any RES-5 code was written.

### 17.2 Architectural summary (ADR-008)

Both entities are **read-only reference data** — `GET` list/get only, no
mutation endpoints, no lifecycle, no webhook dispatch (unlike every RES-4
entity). Key judgment calls, each recorded in `ADR-008`:

- `ScheduleActivity` carries no status/lifecycle field — the "Submittal ->
  Approval -> PO -> Fabrication -> Delivery" procurement chain §16 describes
  is expressed as a relationship (`linked_submittal_ids`, realizing
  `Submittal —SCHEDULED_WITH→ ScheduleActivity`), never an entity-local
  state, per ADR-007's own "relationship, not state" precedent.
- Predecessor/successor is **one** directed edge table
  (`schedule_activity_predecessors`); `successor_ids` is the reverse query,
  never an independently-stored second list.
- `ScheduleActivity —DELIVERS→ Material` is **not implemented** — no
  `Material` entity exists anywhere in RES's frozen scope, and inventing one
  to satisfy a single relationship line would violate the standing
  "do not invent entities" rule.
- `ModelObject.resource_link_id` is a direct nullable FK to
  `ScheduleActivity.id`, collapsing SYNCHRO's Resource intermediary into one
  field, per the source doc's own caveat permitting the abstraction. No
  separate `Resource` entity was introduced.
- No location field on `ScheduleActivity` — `Canonical_Demo_Dataset.md`
  §13's `(Grid B-4)-[location_adjacent, confidence:0.44]->(Schedule Activity
  3410)` edge is a Downstream Reasoning Pipeline output (confidence-scored),
  never an RES-owned field; `location_id` is not named among §16's
  ScheduleActivity fields.

### 17.3 Migration

- **`0013_schedule_activities_and_model_objects.py`** — `schedule_activities`
  (id, project_id, activity_code, type, wbs nullable, delivery_milestone
  nullable), `schedule_activity_predecessors` (self-join edge table),
  `schedule_activity_submittals` (join to `submittals`), `model_objects`
  (id, project_id, discipline_code, appearance_profile, location_id nullable
  FK -> `locations`, resource_link_id nullable FK -> `schedule_activities`).
  Verified twice: applied cleanly against the running dev schema (0012 head),
  and separately from a **completely empty** database (`reference_engineering`
  dropped and recreated on `res-test-db`) alongside migrations 0001–0012 in
  one `alembic upgrade head` run.

### 17.4 API endpoints

```
GET /rest/v1.0/projects/{project_id}/schedule_activities
GET /rest/v1.0/projects/{project_id}/schedule_activities/{schedule_activity_id}
GET /rest/v1.0/projects/{project_id}/model_objects
GET /rest/v1.0/projects/{project_id}/model_objects/{model_object_id}
```

Both mounted in the existing rate-limited `_rest` router group — inherit
`enforce_rate_limit`, `PageParams`/`paginate()`, `X-Total`,
`ActingContext.require_project`/`require_scope`/`ensure_resource_in_project`
automatically, zero new cross-cutting code (same pattern as `vendors.py` for
list, `design_changes.py` for get-by-id's 404-hide semantics).

### 17.5 Canonical seed data (RES-5D)

`meridian_tower.py` seeds exactly one `ScheduleActivity` — the frozen
`sched_3410` / "Schedule Activity 3410" row from `Canonical_Demo_Dataset.md`
§10/§13, `activity_code="3410"`, inserted immediately after RFI-214 closes
(the same Scenario A section that row belongs to). Per the canonical row's
own placeholders ("—" wbs, "N/A" lifecycle position, no relationships):
`wbs=None` (left null, not invented), `type="PROCUREMENT"` (an inferred,
documented judgment call — ADR-008), no predecessors/successors/linked
submittals. **No `ModelObject` is seeded** — no canonical instance is named
anywhere in the frozen or reference docs, matching RES-3's own precedent for
`SubmittalPackage` (real, functional entity; zero seeded rows).
`tests/integration/test_seed_data.py::test_canonical_seed_schedule_activity_3410`
asserts the seeded row's exact shape and that it is the project's only
`ScheduleActivity`.

### 17.6 Tests

**157 backend tests, all passing** (was 127 at RES-4G; 12 new domain +
4 new application + 13 new contract + 1 new seed-assertion test = 157),
run twice in a row against a **completely fresh** schema (dropped/recreated
`reference_engineering`, 13 migrations, then `run_seed`):

- `tests/unit/domain/test_schedule_activity.py`,
  `tests/unit/domain/test_model_object.py` — closed-vocabulary validation
  (every `SCHEDULE_ACTIVITY_TYPES`/`APPEARANCE_PROFILES` value accepted, an
  invalid value rejected), default-empty relationship lists.
- `tests/unit/application/test_schedule_activity_model_object_use_cases.py`
  — `List*`/`Get*` against in-memory fakes (`InMemoryScheduleActivityRepository`,
  `InMemoryModelObjectRepository`, added to `tests/unit/application/fakes.py`),
  project-filtering and `NotFound` on a missing id.
- `tests/contract/test_schedule_activities_and_model_objects_api.py` (new
  `res5_contract_fixture` in `tests/contract/conftest.py`, two isolated
  projects) — auth required, `X-Total`, full contract-field shape,
  under-scoped-integration empty-list/404-get, cross-project list/get 404 —
  for both entities.
- `tests/integration/test_seed_data.py` — extended with the `sched_3410`
  assertion (§17.5).
- `tests/architecture/test_layer_boundaries.py` — unchanged, still passes
  with the new `domain/entities/schedule_activity.py`,
  `domain/entities/model_object.py`,
  `application/use_cases/schedule_activity_use_cases.py`,
  `application/use_cases/model_object_use_cases.py` in place (confirms
  neither imports FastAPI/SQLAlchemy).

**Live API smoke test** (backend on :8000, seeded Meridian Tower, fresh
schema): login as Ananya Rao → `GET .../schedule_activities` returns
`X-Total: 1`, the seeded `sched_3410` row with every contract field present
and correctly null/empty; `GET .../schedule_activities/1` matches;
`GET .../model_objects` returns `X-Total: 0`, `[]` (correctly unseeded).

### 17.7 Files

- `docs/adr/ADR-008.md` — this milestone's structural decisions.
- Migration: `0013_schedule_activities_and_model_objects.py`.
- Domain: `domain/entities/{schedule_activity,model_object}.py`,
  `domain/repositories/{schedule_activity,model_object}_repository.py`.
- Infrastructure: `orm_models/{schedule_activity,model_object}.py`,
  `repositories/sqlalchemy_{schedule_activity,model_object}_repository.py`.
- Application: `use_cases/{schedule_activity,model_object}_use_cases.py`.
- API: `schemas/{schedule_activity,model_object}.py`,
  `v1/{schedule_activities,model_objects}.py`; `api/deps.py` and
  `api/v1/router.py` wiring.
- Seed: `seed/meridian_tower.py` (sched_3410).
- Tests: as listed in §17.6.

### 17.8 Remaining limitations / what RES-5's backend does not do

- **No frontend, no Playwright E2E coverage yet** — §17.9/§17.10 below.
- **No `Material` entity** — `ScheduleActivity —DELIVERS→ Material` is
  unimplemented by design (§17.2); revisit only if a future milestone
  actually needs it, with real canonical seed data to ground it.
- **No mutation/lifecycle** on either entity, by design (ADR-008) — nothing
  in the frozen docs describes RES itself authoring schedule activities or
  model objects; both are synced-in reference data in real practice.
- **`FieldIssue` remains fully unscoped** — see §17.1's flagged contradiction.
- **`docker-compose.yml`'s pre-existing `apps/*` path issue** — unchanged,
  still out of scope.

### 17.9 Frontend (RES-5C)

Two new register pages, consuming only real backend endpoints
(`credentials: "include"`, no bypass), following the existing register
pattern (`vendors`-style read-only list, no detail sub-route — neither entity
has enough sub-structure to warrant one):

| Route | Backed by |
|---|---|
| `/projects/[projectId]/schedule` | `GET .../schedule_activities` — activity code, type, wbs, predecessor/successor codes (cross-referenced within the page's own fetched list), linked-submittal count, delivery milestone |
| `/projects/[projectId]/model-objects` | `GET .../model_objects` — discipline, appearance profile, location name (`locationsApi`), resource-link activity code (`scheduleActivitiesApi`) |

`AppShell`'s project-context nav gained "Schedule" (`CalendarClock` icon) and
"Model Objects" (`Boxes` icon) links. `api-client/types.ts` gained
`ScheduleActivityOut`/`ModelObjectOut`; `api-client/index.ts` gained
`scheduleActivitiesApi`/`modelObjectsApi`.

**Verified:** `npm run build` (incl. real TypeScript check) — both new routes
listed, zero errors; targeted ESLint on the new pages, api-client, and
`app-shell.tsx` — clean; live dev-server smoke of both routes returned 200.

### 17.10 Playwright E2E suite (RES-5F)

The first browser-automation coverage for the Reference Engineering System
frontend — explicitly deferred by every prior milestone (§10.6, §11.9, §16).
`@playwright/test` added as a dev dependency (`npm run test:e2e`),
`playwright.config.ts` (chromium only, `baseURL` :3100, assumes the backend
and a seeded database are already running — the suite reads the canonical
seed, it creates no fixtures of its own).

12 specs across three files, all passing against the canonical seed:

- `e2e/login.spec.ts` — valid login reaches the dashboard; invalid password
  shows an error and stays on `/login`; an unauthenticated visit to a
  project page redirects to `/login` (`useRequireSession`'s 401 handling).
- `e2e/navigation.spec.ts` — golden-path click-through of every pre-existing
  register/detail page via the sidebar nav (RFIs, RFI detail, Drawings,
  Submittals, Design Changes, Specifications, Activity), each asserted to
  render real seeded content (RFI-214, M-2.1, SUB-118, ASI-07/ISSUED,
  Spec 23 31 13) — not just a 200 status.
- `e2e/schedule-and-model-objects.spec.ts` — RES-5's own two pages: the
  Schedule register shows the canonical `sched_3410` row with its `PROCUREMENT`
  type and null-`wbs` em-dash placeholder (not a fabricated value); the Model
  Objects register shows its empty state, since no canonical instance exists
  (§17.5/ADR-008).

One real bug caught on the first run: `login.spec.ts`'s dashboard assertion
matched two elements ("Meridian Tower" appears in both the page subtitle and
a stat card) — a strict-mode violation, not a product bug. Fixed with
`.first()`. All 12 pass on the second run.

### 17.11 Docker Compose verification (RES-5G)

Base images (`node:20-slim`, `python:3.11-slim`) required a retry after a
transient registry connectivity failure on the first pull — not a code
issue. Rebuilt both images
(`docker compose -f infra/docker-compose.yml up -d --build
reference-engineering-db reference-engineering-backend
reference-engineering-frontend`); the frontend build log shows the same
clean `npm run build` output (both new routes, zero TypeScript errors) as
the host-side build in §17.9.

The compose DB volume held three-day-old data from a prior verification
session (pre-RES-5) — dropped and recreated for a genuinely fresh check,
matching RES-4G's precedent: `alembic upgrade head` ran all 13 migrations
clean on the empty containerized database, `python -m seed.run_seed` seeded
successfully (`schedule_activity_id: 1` in its output), and a live smoke test
against the running containers confirmed `GET
/rest/v1.0/projects/1/schedule_activities` returns the exact `sched_3410`
payload and both new frontend routes return 200. All three containers
stopped (not removed) afterward, per established convention.

**One incidental port conflict, unrelated to Docker itself:** this session's
own earlier host-side dev-server smoke test (§17.9) had left a stray `next
dev --port 3100` process running, which collided with the frontend
container's port binding. Identified via `Get-NetTCPConnection`/`Get-Process`
and stopped before retrying — not a docker-compose or code defect.

---

## 18. Document Ingestion Pipeline (DIP) — Phases A, B, C, D

### 18.1 Scope and authority

`reference-systems/document-ingestion-pipeline/` — a new sibling of
`reference-engineering-system/` under `reference-systems/`, per
`docs/architecture/DSH_Ingestion_Pipeline_Architecture.md` and its
post-RES-5 reconciliation. **Not a Downstream service, not an RES
dependency, no new service boundary, no Kafka, no Neo4j, no LLM
extraction.** DIP turns the real DSH-Atascadero PDF corpus
(`data/reference-projects/dsh-atascadero/raw/`, four files, untouched,
never modified — verified by content-hash before/after in
`tests/golden/test_manifest_against_real_corpus.py::test_source_pdfs_are_never_modified`)
into provenance-preserving, deterministic evidence. Its own
`pyproject.toml`/pytest config, fully independent of the root repo's 201
`packages/*` tests and of RES's own suite — mirroring the precedent RES
itself already established (§10.1).

Approved in two sessions: Phase A (manifest) / Phase B (OCR benchmark) /
Phase D (synthetic diff) first, then — after a dedicated OCR investigation
and implementation plan — Phase C (real E0.4 New Unit block extraction).
Phase E (promotion into RES) remains explicitly not started; no RES file
was touched by any part of this work (verified via `git status` on
`reference-systems/reference-engineering-system/` — empty).

### 18.2 Phase A — PDF manifest

Opens a source PDF read-only via `pypdfium2`, walks pages using page-object/
text-layer inspection only (never rendering), classifies each page
(`native_text`/`raster_embedded`/`vector_curve`/`mixed`) via named,
tunable thresholds (`dip.config`), and writes a per-document manifest JSON
plus a document registry, keyed by a streaming-computed sha256 (never loads
a 250MB+ file whole). Idempotent by content hash.

Verified directly against the real corpus, independently reproducing the
DSH reconnaissance report's own hand-measured numbers: E0.4 (doc02 p.373)
→ `raster_embedded`, 37.53% image coverage (recon: ~36.9%); E0.6 (p.375) →
`raster_embedded`, 51.85% (recon: ~51.9%); EE5.1 (doc03 p.43) →
`vector_curve`, 41,070 path objects. One honest heuristic imperfection
documented, not hidden: E0.7 (p.376, same schedule family as E0.6)
classifies `native_text` at 17.52% coverage — just under the 20% floor.

### 18.3 Phase B — OCR benchmark

Renders exactly the 3 named benchmark pages (E0.4/E0.6/EE5.1 — never the
whole corpus) and runs every *available* OCR engine against them, recording
results without ever computing or claiming an accuracy percentage.
Tesseract **v5.4.0.20240606** installed via
`winget install --id UB-Mannheim.TesseractOCR` (binary resolved via
`DIP_TESSERACT_CMD` → `PATH` → well-known install path — never assumed to
be on `PATH`, since winget doesn't retroactively update an already-open
shell). RapidOCR (`rapidocr-onnxruntime`) is the pure-pip fallback
candidate, chosen and documented before running anything (lighter install
than `easyocr`, no PyTorch dependency, PP-OCR models tuned toward
dense/tabular text).

Both engines correctly recovered `AH-9C`/`MR6`/`MR7` from the real E0.4
sheet — independently validating that the architecture doc's illustrative
example reflects real sheet content (though not, it turns out, the *correct*
real relationship — see §18.4's AH-9C finding). No engine declared an
overall winner from this benchmark alone. Real, sometimes-surprising
findings, all measured not assumed: Tesseract's E0.6 runtime (110–150s) was
an 8–9x outlier against its own E0.4/EE5.1 runtimes (12–23s) in every run;
RapidOCR produced garbled CJK-looking artifacts localized to one dense
small-font region of EE5.1 (~21% non-ASCII tokens there, 0% on E0.4/E0.6).

### 18.4 Phase C — E0.4 New Unit block extraction (this session)

**OCR investigation, before implementation.** Re-examined the real
benchmark `results.json` (word-box level) and, critically, the actual
rendered E0.4 sheet directly (cropped and read, not OCR-mediated).
Findings:

- **Tesseract's E0.6 runtime outlier correlates with, not merely
  coincides with, a measured spike in tiny/single-character word
  fragments** (1036 single-char / 677 tiny boxes on E0.6 vs. 552/270 on
  E0.4 and 483/420 on EE5.1) — reported as correlation, not proven root
  cause.
- **RapidOCR's EE5.1 garbling has a concrete, located signature**: a
  repeating `■` token at a near-fixed x-position with a ~54px vertical
  step (almost certainly a misread graphic/legend symbol column, not
  text), plus a second cluster of genuine CJK-character tokens
  spatially confined to one ~1200×550px region — localized, not
  page-wide. Tesseract, checked against the exact same region, produced
  plausible engineering fragments instead.
- **Render-scale experiment** (2.0/4.0/6.0, both engines, all 3 pages —
  `scripts/run_render_scale_experiment.py`,
  `data/.../derived/render_scale_experiment/results.json`): scale 4.0
  measurably best for raw OCR quality (matches scale 6.0's peak Tesseract
  token recovery on E0.4 at far lower runtime/noise; fixes E0.6's
  scale-2.0 pathology outright, 149.6s→30.35s); scale 6.0 offered no
  measurable benefit anywhere and costs more. Neither scale improved
  EE5.1's garbling at all — confirming it's a recognition-model issue, not
  a resolution issue.
- **Real, unresolved integration gap found and flagged, not silently
  resolved**: switching the live pipeline to scale 4.0 broke
  `dip.tablegrid`'s row-band detection (59 rows → 33 — the merge/pitch
  thresholds were calibrated and visually validated only at scale 2.0),
  and reloading a scale-4.0+ render from the cache trips PIL's
  `DecompressionBombWarning` (104.5MP vs. PIL's 89.5MP default limit; scale
  6.0 exceeds PIL's *hard* error threshold outright). `dip.config.RENDER_SCALE`
  was **deliberately left at 2.0** — the scale `dip.tablegrid` is actually
  validated against — with both findings documented in `config.py`'s own
  comment as an open, unresolved decision, not quietly picked.
- **A genuine correction to an earlier illustrative example**: direct
  visual inspection of the real E0.4 sheet found AH-9C's real "New Unit →
  Fed From Panel" value is **MR4**, not the MR6→MR7 story used in Phase D's
  clearly-labeled `SYNTHETIC` fixture and the architecture doc's example.
  The synthetic fixture was never claimed to be real and is left unchanged
  (Phase D's job was always to prove the diff *mechanism*, not to describe
  E0.4) — but real-source extraction (this phase) now supersedes it as the
  source of truth for any future real-data example.

**Table reconstruction — ruling-line grid detection**
(`dip.tablegrid.grid.detect_grid`), a classical projection-profile
technique (row/column darkness projections on the binarized rendered
bitmap), not ML, chosen because the real E0.4 sheet has genuine drawn
table borders (confirmed by direct visual inspection). Row and column
density floors are deliberately **different constants**, both empirically
calibrated against the real render (not guessed): rows at 0.3 (a clean
signal), columns at 0.85 (columns needed a higher floor to separate
genuine full-height rule lines, measured ≥0.9 density, from coincidental
digit-column alignment noise, measured in the 0.3–0.6 range — a real,
measured bimodal split, not an arbitrary threshold). Detected **59 rows ×
35 columns** on the real E0.4 render at scale 2.0, visually validated by
drawing the detected grid lines back onto the source image and reading the
result directly. **Known limitation, measured not assumed**: row detection
covers only the table's first ~59 rows (y∈[458, 2231]); the remainder of
the visible table (to ~y=3200) has row-density that drops below the
detection floor almost everywhere in that region — root cause not fully
diagnosed (plausibly a lighter rule-line weight in that portion of the
source CAD drawing), documented in `grid.py`'s own module docstring, not
masked. Does not block v1 scope — AH-9C and all 8 ground-truth rows fall
within the successfully-detected band.

**Header scoping** (`dip.extract.header_scope.locate_new_unit_columns`) —
never hardcoded column indices. Anchors on real header text: `"CONDUIT"`
(confirmed unique, only in the New Unit block) and `"DESIGNATION"`
(confirmed exactly two occurrences — identity columns), then locates the
New Unit block's other five columns (FLA, MCA, Volts, Panel, Breaker
Rating) at fixed offsets *relative to* the CONDUIT anchor — validated
against real Tesseract OCR output of the actual header region, byte-exact
match on all 6 New Unit columns.

**Corrected data model** (`dip.diff.models.EquipmentRow`, modified in
place — not a parallel model): `circuit_number`/`hp` **removed** (neither
exists in the New Unit block — only in the two deferred Existing blocks);
`conduit` **added** (a real New Unit column the original placeholder
missed). `fla`/`mca` keep their original names/types (raw/display
strings) for backward compatibility with the existing Phase D synthetic
fixtures and tests; `fla_numeric`/`mca_numeric` are new, separate,
null-on-parse-failure fields (decision 12). New:
`mca_fla_suspicious`(bool, flags MCA≤FLA, never corrects — decision 13),
`tag_pattern_flag` (bool, advisory-only AH-* mismatch — decision 15),
`field_provenance: dict[str, FieldProvenance]` (per-New-Unit-field OCR
confidence + extraction confidence + `EvidenceRef`, kept as two always-
separate numbers — decision 9). `EvidenceRef` gained one new optional field,
`ocr_engine` (decision 11) — confirmed backward compatible: every existing
Phase A/B/D test and fixture still passes unchanged, since Pydantic's
default field defaults make every addition here purely additive.

**Numeric normalization** (`dip.extract.normalize.normalize_numeric`) —
edge-noise tolerant (strips stray brackets/pipes *only* from the two ends
of a string, never the middle — measured directly against real E0.4 OCR
output, which occasionally appends such noise adjacent to a
ruling-line-crossing cell), never coerces internally-garbled text, never
fabricates a value from nothing. **Tag extraction**
(`dip.extract.build._clean_tag_text`) required a second real-data-driven
fix beyond edge-stripping: Tesseract was found, across different real runs
of the *same* cell, to prepend a *different* stray punctuation-like
character each time (U+FFFD once, U+2018 another time) — not one fixed,
whitelistable character. Fixed by searching for the known-valid `AH-*`
shape within the cell text and extracting just that substring (the tag's
own digits/letters were correct in every case observed; only an adjacent
non-content glyph wasn't) — falling back to edge-stripped raw text, never
silently discarding an unusual tag, when no such pattern is found.

**Engine policy** (decision 5): Tesseract is the sole default engine for a
whole-page OCR pass. RapidOCR is invoked **only** as a per-cell fallback —
cropping just the one New Unit field cell that came back empty from
Tesseract and re-OCR-ing that tiny crop — never a second whole-page pass.
Tesseract's `block_num`/`par_num`/`line_num` hierarchy is captured onto a
new, optional `OcrWord.line_group` field (decision 8) as a documented
supporting signal for future cross-checks; v1's `extraction_confidence`
computation (geometric word-box/cell-boundary overlap fraction, independent
of OCR confidence by construction) does not yet consume it — stated
explicitly as a scope boundary, not a silently-skipped feature.

**Ground truth** (`tests/fixtures/e04_ground_truth.json`, explicitly
`"SYNTHETIC": false, "SOURCE": "manual transcription of real E0.4"` — never
to be confused with the wholly-fictional
`tests/fixtures/synthetic_rev_{a,b}.json`): 8 rows (AH-9A, AH-9C, AH-17B,
AH-2B, AH-GSA, AH-K1, AH-MH1, AH-24CTA), chosen for real variability already
observed (fully-populated rows, TBD-placeholder rows, an unusual
"Bucket 3"/"Penthouse MCC" row, a footnoted row) — transcribed by direct,
independent visual reading of a precisely-cropped composite image, not
derived from or cross-checked against any OCR engine's output before being
locked in.

**Measured accuracy** (`tests/golden/test_e04_extraction_against_ground_truth.py`,
excluded from the default run, self-skips if the corpus is absent): **91.1%
exact field match (51/56)** across the 8 ground-truth rows × 7 compared
fields (`existing_designation` + the 6 New Unit fields), asserted against
an 80% floor (set with real margin under the measured 91.1%, not equal to
it, so ordinary OCR non-determinism doesn't make the test flaky). Every
mismatch printed, not hidden — 5 found, all genuine, real Tesseract OCR
errors, not extraction-logic bugs: three dropped-decimal-point MCA
misreads (`"22.0"`→`"220"`, `"26.0"`→`"260"`, `"34.0"`→`"340"`), one
`"/"`-misread-as-`"1"` breaker rating (`"25/3"`→`"2513"`), one missing-space
existing-designation (`"(E) GSA UNIT"`→`"(E) GSAUNIT"`). None of the three
dropped-decimal errors happened to flip an MCA>FLA comparison, so
`mca_fla_suspicious` never false-fired on these 8 rows — asserted as its own
test, not assumed. Every extracted New Unit field on the (error-free)
AH-9A row carries full provenance: `document_id`, `file_name`, `page_index`,
`page_label`, `bounding_box`, `extraction_method`, `extractor_version`,
`extracted_at`, `ocr_engine` — asserted directly.

### 18.5 Phase D — deterministic synthetic revision diff (prior session)

`dip.diff.engine.diff_schedule` — pure, deterministic, no I/O, no OCR
import, generic over any Pydantic row model (proven by a dedicated test
using a wholly different row type, unaffected by Phase C's `EquipmentRow`
correction). Synthetic fixtures explicitly labeled `SYNTHETIC` with a
disclaimer, using a sheet name (`SYNTHETIC-DEMO-SCHEDULE`) that can never be
mistaken for a real DSH sheet.

### 18.6 Test results

| Suite | Command | Result |
|---|---|---|
| DIP fast (default) | `pytest -q` from the DIP directory | **94 passed**, 9 deselected (golden), <1s |
| DIP golden | `pytest -q -m golden` | **9 passed** (3 new E0.4 extraction tests + 6 manifest tests against the real corpus), ~131s |
| Root repo | `pytest -q` from repo root | **201 passed**, unchanged, unaffected |
| RES | not re-run this session | confirmed untouched via `git status` (no diff on `reference-systems/reference-engineering-system/`) — re-running its own suite would require standing up its Postgres dependency, outside this session's scope |

### 18.7 Files

New this session (Phase C): `src/dip/tablegrid/{__init__,grid,models}.py`,
`src/dip/extract/{__init__,assignment,header_scope,normalize,build}.py`,
`scripts/run_render_scale_experiment.py`,
`tests/fixtures/e04_ground_truth.json`,
`tests/golden/test_e04_extraction_against_ground_truth.py`,
`tests/unit/{test_grid,test_assignment,test_header_scope,test_normalize,test_confidence_provenance}.py`.
Modified: `src/dip/config.py` (grid-detection constants, E0.4 identity
constants, render-scale decision + comment), `src/dip/provenance.py`
(`ocr_engine` field, new `FieldProvenance` model), `src/dip/diff/models.py`
(`EquipmentRow` corrected per §18.4), `src/dip/ocr/render.py` (scale
parameter, backward compatible), `src/dip/ocr/engines/base.py` (`line_group`
field), `src/dip/ocr/engines/tesseract_engine.py` (populates `line_group`),
`pyproject.toml` (`numpy` core dependency), `README.md`.

### 18.8 Known limitations / what remains deferred

- Existing Supply Fan / Existing Return Fan / Conductors / Motor
  Controller / Motor Disconnect / Notes columns — not extracted, by
  approved v1 scope, not an oversight.
- Grid row-band detection covers only ~59 of the table's ~60+ visible
  rows on E0.4 (§18.4) — root cause not fully diagnosed.
- `RENDER_SCALE` is left at 2.0 despite scale 4.0 measuring better raw OCR
  quality, because `dip.tablegrid`'s thresholds aren't yet recalibrated for
  a different pixel density — an open decision, not a silent one.
- `OcrWord.line_group` is captured but not yet consumed by any
  cross-validation logic.
- No other sheet (E0.6, EE5.1, or any DSH document beyond E0.4) is
  extracted — explicitly out of scope, per the approved decisions.
- Phase E (promotion into RES — `CreateDrawingVersion`,
  `RevisionCloud.source_evidence_ref`, the DSH→RES loader) remains fully
  unstarted, pending its own narrow ADR, per the post-RES-5 reconciliation.

---

## 19. DIP Phase C Reliability / Calibration milestone

### 19.1 Scope

Not a scope expansion — E0.4 New Unit block only, same as §18. This
milestone hardens what §18 already built: scale-aware grid geometry,
engineering-safe field validation with an explicit ambiguity state, and a
fully classified (not aggregate-only) accuracy report. No E0.6/EE5.1
extraction, no RES/Downstream/Kafka/Neo4j/LLM work, no RES file touched
(confirmed via `git status`).

### 19.2 Task 1 — scale-aware grid detection: two real findings, not one

Investigated directly against the real E0.4 render at each scale, not
tuned until a number matched. Two genuinely pixel-distance thresholds
(`GRID_LINE_MERGE_GAP_PX`, `GRID_MAX_ROW_PITCH_PX`) were confirmed
scale-dependent — measured row pitch was ~30px at scale 2.0 and exactly
~60px at scale 4.0, matching the 2x scale ratio precisely — and are now
computed via `dip.config.grid_line_merge_gap_px()`/`grid_max_row_pitch_px()`,
linearly scaled from a calibrated reference. The two density floors and the
binarization threshold were confirmed scale-**independent** (fractions/
color, not distances) and left unchanged. Result, measured across all three
required scales on the real page:

| Scale | Rows | Cols | Render+grid time |
|---|---|---|---|
| 2.0 | 59 | 35 | 0.29s |
| 4.0 | 59 | 35 | 1.20s |
| 6.0 | 59 | 35 | 3.88s |

Grid geometry is now fully scale-consistent — the row/column count no
longer depends on which scale is used. Getting scale 6.0 measurable at all
required a second, real fix: reloading a scale-6.0 render from cache raised
PIL's actual `DecompressionBombError` (235MP vs. Pillow's ~179MP hard
limit) — `Image.MAX_IMAGE_PIXELS` is now deliberately, boundedly raised in
`dip.config` with an explicit justification comment (every image DIP opens
is self-produced and scale-bounded, never arbitrary untrusted input).

**Critical finding, corrected from the original hypothesis**: with grid
detection now fully scale-aware, re-running the *full* pipeline
(`extract_new_unit_rows`) at scale 4.0 still recovers only **33 of 59
rows** — proving the original 59→33 diagnosis (attributed to grid
threshold miscalibration) was incomplete. Traced directly: at scale 4.0,
Tesseract's OCR pass finds **zero words anywhere** in the tag/existing-
designation/existing-supply-fan column region (confirmed by inspecting the
actual word list per missing row) for roughly half the rows — a Tesseract
OCR-completeness behavior at that resolution, entirely separate from and
unaffected by grid geometry. This is the real reason scale 4.0 is not
adopted (§19.6), not the grid thresholds.

### 19.3 Task 2 — the "missing row" was a documentation error, corrected

Direct visual inspection of the exact boundary where row detection stops
(a fresh, precise crop of the real page at that y-range) found **AH-MH1 is
confirmably the table's true last row**, immediately followed by prose
("Numbered Notes:", "General Notes:") — not another equipment row. Row-
pitch uniformity across all 59 detected rows was measured directly (min
29.5px / max 31.5px / mean 30.05px at scale 2.0, zero anomalous gaps),
ruling out a merged-row pair as well. **Conclusion: there is no missing or
merged row.** The original Phase C report's "known limitation" (claiming
the table continued to ~y=3200 with more rows) was a documentation error —
conflating the Notes section's prose (which does extend to that y-range,
as text, not table rows) with missing table content — now corrected in
`dip.tablegrid.grid`'s own module docstring. A regression test
(`test_e04_row_count_is_stable_and_ah_mh1_is_confirmed_the_last_real_row`)
guards this finding going forward.

### 19.4 Tasks 3/4 — engineering-safe, field-specific normalization

Added `dip.provenance.ValidationStatus` (`VALID`/`AMBIGUOUS`/`INVALID`/
`MISSING`) and a dedicated validator per New Unit field in
`dip.extract.normalize` — never one generic function reused everywhere:
`validate_fed_from_panel` (`MR\d+`), `validate_breaker_rating` (`\d+/\d+` —
the `/` is load-bearing), `validate_conduit` (size + literal unit `in`),
`validate_volts` (bare integer), `validate_numeric_field` (fla/mca, with a
plausibility cross-check: MCA/FLA ratio > 3.0 in either direction, a
generous margin above the real ~1.0-1.3x NEC convention, flags without
correcting). `EquipmentRow` gained `field_validation: dict[str,
ValidationStatus]`, additive and backward compatible (existing Phase D
fixtures/tests unaffected — confirmed by the full suite still passing).

**Every validator only classifies — none of them can return a corrected
value; there is no return channel for one.** Verified directly against the
real, previously-mismatched fields:

| Field | Raw (unchanged) | Before this milestone | After |
|---|---|---|---|
| AH-9C.breaker_rating | `"2513"` | stored, unflagged | stored, **AMBIGUOUS** |
| AH-9C.mca | `"220"` | stored, unflagged | stored, **AMBIGUOUS** |
| AH-K1.mca | `"260"` | stored, unflagged | stored, **AMBIGUOUS** |
| AH-24CTA.mca | `"340"` | stored, unflagged | stored, **AMBIGUOUS** |

The raw string is byte-identical before and after — only a new, additive
classification exists now that didn't before.

### 19.5 Task 5 — regression tests for real observed failures

`tests/unit/test_normalize.py` extended with per-validator test classes
(73 tests total in that file now) using the literal real values (`25/3`,
`2513`, `22.0`, `220`, `MR4`, `60/3`, `1 in`, `TBD`, `-`, `?`) — including
`TestFieldSpecificPatternsAreDistinctNotGeneric`, which directly proves a
breaker-shaped value fails panel validation and vice versa (Task 4's core
requirement, not just implied by separate functions existing).

### 19.6 Task 6 — render-scale decision, re-evaluated with full evidence

**Scale 2.0 remains the production scale — confirmed, not merely
unchanged by default.** Grid geometry is no longer the blocker (§19.2) —
scale 4.0 is fully viable geometrically. The blocker is the OCR-
completeness finding in §19.2: scale 4.0's full-pipeline row recovery,
re-measured after every grid fix, is still 33/59 (56%), against scale
2.0's 59/59 (100%). This is a Tesseract behavior this milestone did not
attempt to fix (out of scope — no OCR-engine internals work was
authorized), so the render-scale decision is unchanged in outcome but is
now backed by a materially more precise diagnosis: not "the grid detector
needs recalibration" (done, and insufficient alone) but "Tesseract itself
drops the left third of the table at this resolution," a different,
still-open problem for a future milestone.

### 19.7 Task 7 — golden validation, fully classified

`tests/golden/test_e04_extraction_against_ground_truth.py` rewritten to
report row-level and field-level breakdowns and classify every mismatch
(`KNOWN_MISMATCH_CLASSIFICATION`) rather than one aggregate number; an
*unclassified* mismatch now fails the test outright, stricter than the
aggregate floor. Result on the real page: **51/56 (91.1%)**, all 5
mismatches classified **OCR** — zero classified GRID, CELL_ASSIGNMENT,
NORMALIZATION, or GROUND_TRUTH. A new test
(`test_e04_every_known_mismatch_is_flagged_ambiguous_by_field_validation`)
proves the Task 3/4 safety net actually catches every one of these 5 known
mismatches, not just that they differ from ground truth. A new
`test_grid_detection_is_scale_consistent_at_2_4_and_6` proves §19.2's
finding directly, every run.

### 19.8 Task 8 — the explicit safety property

`tests/unit/test_safety_property.py` (new, 6 tests) proves, using the
literal real observed values: no validator has a return channel for a
corrected value; an `EquipmentRow` built with a known-ambiguous raw value
(`"2513"`, `"220"`) stores that value completely unmodified regardless of
its `field_validation` status; an ambiguity flag never causes a field to
become `None` (ruling out "silently discard" as a disguised form of the
same forbidden behavior).

### 19.9 Task 9 — regression

| Suite | Result |
|---|---|
| DIP fast | **155 passed**, 12 deselected (was 94/9 before this milestone) |
| DIP golden | **12 passed** (was 9) — includes the new scale-consistency and classification tests, ~163s |
| Root repo | **201 passed**, unchanged |
| RES | confirmed untouched via `git status` (empty diff on `reference-systems/reference-engineering-system/`) |

### 19.10 Files changed

Modified: `src/dip/config.py` (scale-aware grid functions, `MAX_IMAGE_PIXELS`
fix), `src/dip/tablegrid/grid.py` (scale-aware thresholds, corrected
docstring), `src/dip/provenance.py` (`ValidationStatus`), `src/dip/diff/models.py`
(`field_validation`), `src/dip/extract/normalize.py` (field-specific
validators), `src/dip/extract/build.py` (`field_validation` wiring),
`tests/golden/test_e04_extraction_against_ground_truth.py` (full rewrite
per Task 7), `tests/unit/test_normalize.py` (extended). New:
`tests/unit/test_safety_property.py`, `tests/unit/test_scale_aware_grid_thresholds.py`.

### 19.11 Is E0.4 reliable enough for the next promotion step?

**Not yet, and specifically not because of accuracy — because of the
scale-4.0 OCR-completeness gap remaining genuinely unresolved.** At the
validated scale 2.0: grid geometry is now proven stable and correct
end-to-end (no known geometry failures at all, across three scales), and
every currently-known data error is both classified and automatically
flagged via `field_validation`, never silently trusted. That is a
defensible reliability floor for the *scale 2.0, E0.4, New Unit block*
slice specifically. It is not yet a general "any scale, any table" claim,
and the underlying question of *why* Tesseract drops text in that column
region at scale 4.0 remains open.

### 19.12 Remaining risks

- The scale-4.0 OCR-completeness gap is unexplained, not just unfixed —
  root cause not diagnosed beyond "Tesseract found nothing there."
- `MCA_FLA_MAX_PLAUSIBLE_RATIO = 3.0` is a reasonable, documented margin
  above the real NEC convention, but is itself a threshold calibrated
  against only 3 known-bad + several known-good pairs — not a large
  sample.
- `existing_designation` has no dedicated validator (out of Task 4's
  named field list) — its one observed mismatch (a dropped space) is
  classified but not caught by any automated flag.
- Only E0.4 has been validated at all — no evidence yet on whether the
  scale-awareness fix or the validators generalize to a different sheet.

### 19.13 Recommended next milestone

Diagnose the scale-4.0 Tesseract OCR-completeness gap specifically (e.g.,
page-segmentation-mode experiments on the tag-column region alone) before
either adopting a higher scale or declaring 2.0 permanent — this is now a
narrow, well-isolated question, not a broad "improve accuracy" one. Do not
expand to E0.6/EE5.1 or Phase E until that is resolved or explicitly
deferred.

