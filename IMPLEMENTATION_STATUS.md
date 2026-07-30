# Downstream — Implementation Status

**Last updated:** 2026-07-31 (RES-1)
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
| *(this commit)* | **Reference Engineering System — RES-1.** See §10 below. |

---

## 3. Current state, at a glance

| Layer | Status |
|---|---|
| `docs/` | Frozen, unmodified, source of truth |
| `apps/*` (16 services) | **Scaffold only** — folder structure, placeholder README/Dockerfile/pyproject.toml. Zero business logic, zero APIs, zero database code. This is Downstream's own service mesh — untouched by RES-1. |
| `packages/*` (5 packages) | **Implemented** — real, tested Pydantic models and an ABC. This is Milestone 0 (Downstream's own shared contracts — not used by the Reference Engineering System, see §10.1). |
| `infra/` | `docker-compose.yml` now wires the Reference Engineering System's three containers (db/backend/frontend); every other service entry is still scaffold-only, matching the blueprint. `mocks/Reference Engineering System/` was removed — superseded by `reference-systems/reference-engineering-system/` (see §10). `mocks/Reference Commercial System/` remains an empty placeholder. |
| `reference-systems/reference-engineering-system/` | **RES-1 implemented** — FastAPI backend (Clean Architecture) + Next.js frontend, both real, both tested, both containerized and verified end to end. See §10. |
| Tests | 201 `packages/*` unit tests (unchanged) + 20 new Reference Engineering System backend tests (unit + application + architecture-boundary), all passing. Frontend: build + typecheck + lint clean; no automated frontend tests yet (Playwright suite is RES-5 scope). |
| Downstream Milestone (per blueprint §9) | Milestone 0 complete. Milestones 1–5 not started — unaffected by this phase. |
| Reference Engineering System Milestone (per Plan v2 §17) | **RES-1 complete.** RES-2 through RES-5 not started. |

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

**A pre-existing, repo-wide bug was discovered and fixed while verifying this:** every build path in `docker-compose.yml` (`./apps/connector-procore`, etc.) is written relative to the repo root, but Compose resolves build contexts relative to the *compose file's own directory* (`infra/`) unless `--project-directory` is passed explicitly. This means `docker compose -f infra/docker-compose.yml up` — the exact command the root `README.md` has documented since commit `49a12f8` — has never actually worked for any of the 16 pre-existing service definitions, not just the new ones. Fixed by documenting `--project-directory .` in `README.md`'s run instructions; `docker compose config` was used to confirm every path (old and new) now resolves correctly. No service definitions were rewritten — this was a one-line invocation fix, not a path-by-path rewrite.

**Verified against the actual containers, not just `config`:** built both images, brought up all three services via `docker compose ... up -d`, ran `alembic upgrade head` and the seed script *inside* the running backend container, then confirmed login + the full RFI-214 fetch from the host machine against the containerized backend, and confirmed the frontend container serves `/login` with a 200. All three containers were stopped (not removed) afterward.

**Known, pre-existing, out-of-scope issue left as-is:** `mock-erp`'s build path (`./infra/mocks/mock-erp`) is also stale — the folder was renamed to `infra/mocks/Reference Commercial System/` in commit `37b29c4` without updating `docker-compose.yml`. Not fixed here because Commercial System work is an explicit non-goal of this phase; flagged in both `docker-compose.yml` itself (inline comment) and here so it isn't silently forgotten.

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
# expected: 20 passed
```

```bash
# from the repo root
docker compose -f infra/docker-compose.yml --project-directory . up -d --build reference-engineering-db reference-engineering-backend reference-engineering-frontend
docker exec <backend-container> python -m alembic upgrade head
docker exec <backend-container> python -m seed.run_seed
curl http://localhost:8000/health
curl http://localhost:3100/login
```
