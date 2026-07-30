# Downstream — Implementation Status

**Last updated:** 2026-07-31
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

---

## 3. Current state, at a glance

| Layer | Status |
|---|---|
| `docs/` | Frozen, unmodified, source of truth |
| `apps/*` (16 services) | **Scaffold only** — folder structure, placeholder README/Dockerfile/pyproject.toml. Zero business logic, zero APIs, zero database code. |
| `packages/*` (5 packages) | **Implemented** — real, tested Pydantic models and an ABC. This is Milestone 0. |
| `infra/` | Scaffold only — `docker-compose.yml` matches the blueprint exactly; `migrations/` and `mocks/` are empty placeholders. |
| Tests | 201 unit tests, all passing, covering only `packages/*` |
| Milestone (per blueprint §9) | Milestone 0 complete. Milestones 1–5 not started. |

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
- **No mocks running** — `mock-engineering-system` and `mock-erp` have empty `src/`.

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
