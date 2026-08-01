# Downstream — Implementation Status

**Last updated:** 2026-08-02 (RES-3)
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
| `1880bf5` | Made directly by the user — added `docs/reference/The Enterprise Fidelity Review.md` and `docs/reference/Canonical_Demo_Dataset.md` (the latter authored by this assistant in an earlier turn, committed by the user alongside the former). |
| *(this commit)* | **Reference Engineering System — RES-3.** See §12 below. |

---

## 3. Current state, at a glance

| Layer | Status |
|---|---|
| `docs/` | Frozen, unmodified, source of truth |
| `apps/*` (16 services) | **Scaffold only** — folder structure, placeholder README/Dockerfile/pyproject.toml. Zero business logic, zero APIs, zero database code. This is Downstream's own service mesh — untouched by RES-1. |
| `packages/*` (5 packages) | **Implemented** — real, tested Pydantic models and an ABC. This is Milestone 0 (Downstream's own shared contracts — not used by the Reference Engineering System, see §10.1). |
| `infra/` | `docker-compose.yml` now wires the Reference Engineering System's three containers (db/backend/frontend); every other service entry is still scaffold-only, matching the blueprint. `mocks/Reference Engineering System/` was removed — superseded by `reference-systems/reference-engineering-system/` (see §10). `mocks/Reference Commercial System/` remains an empty placeholder. |
| `reference-systems/reference-engineering-system/` | **RES-1 + RES-2 + RES-3 implemented** — FastAPI backend (Clean Architecture) + Next.js frontend, both real, both tested, both containerized and verified end to end. RES-3 adds Submittals (parent/child revisioning, ADR-004), a configuration-driven procurement-release gate (ADR-003), Submittal Packages (ADR-005, unused by seed data), Vendors, minimal Commitments, the spec-driven Submittal Register, and the Submittal Register/Detail + Specification Browser frontend pages. See §10 (RES-1), §11 (RES-2), §12 (RES-3). |
| Tests | 201 `packages/*` unit tests (unchanged) + 61 Reference Engineering System backend tests (41 from RES-1/RES-2 + 20 new RES-3 tests across unit, application-with-fakes, integration, and contract tiers), all passing, twice in a row from a clean schema. Frontend: build + typecheck + lint clean; no automated frontend tests yet (Playwright suite is RES-5 scope). |
| Downstream Milestone (per blueprint §9) | Milestone 0 complete. Milestones 1–5 not started — unaffected by this phase. |
| Reference Engineering System Milestone (per RES-3 Plan v2 §3) | **RES-1, RES-2, and RES-3 complete.** RES-4 (Design Change family, Field Issues) and RES-5 (ScheduleActivity, ModelObject, ClashItem, Transmittal, cross-entity relationship UI, Playwright) not started. |

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
# expected: 61 passed
```

```bash
docker compose -f infra/docker-compose.yml up -d --build reference-engineering-db reference-engineering-backend reference-engineering-frontend
docker exec <backend-container> python -m alembic upgrade head
docker exec <backend-container> python -m seed.run_seed
curl http://localhost:8000/rest/v1.0/projects/1/submittals   # (with an Authorization header — see backend/README.md)
curl http://localhost:3100/projects/1/submittals
```
