# Downstream — Implementation Backlog Derived From the Reference Trace
### Build exactly what the trace exercises. Nothing else yet.

## Verdict up front

The full systems architecture named fourteen stages, five connector families, nine UI pages, and a five-stage reasoning pipeline. **This one trace exercises: one engineering connector (Procore), two synchronization tiers (email + one ERP), six backend services, six database stores, nine externally-callable APIs, and three UI surfaces — one of which is a single interaction, not a full page.** Everything else named in the product and systems design is real and eventually necessary, but nothing in this trace touches it. Building it now would be scope invented ahead of evidence — exactly what the mission's own discipline (Report on Downstream's category strategy) warned against. The backlog below builds only what this scenario requires, in the order its own dependencies demand.

---

## What the trace actually exercises

**Backend services (six):**
1. Procore Connector Adapter — inbound webhook receipt, enrichment GET-back, envelope construction
2. Ingestion & Normalization Service — dedup, event-worthiness filter, Trigger persistence
3. Key Resolution + Graph Layer — key lookup, candidate match, one versioned edge write
4. Reasoning Pipeline — all five sub-stages, run as one deployable service for this scope
5. Commercial Event Service — the Event/Impact/Action state machine
6. Synchronization Service — dispatch to two connector tiers (generic email, SAP)

Plus two infrastructure components with no business logic of their own: the **Event Bus** (topics used: `trigger.detected`, `keys.resolved`, `event.created`, `impact.tiered`, `severity.computed`, `action.drafted`, `action.approved`, `action.dispatched`, `action.confirmed`, `event.closed`) and the **Realtime Gateway** (WebSocket fan-out of the same topics, filtered by `project_id`).

The **Ledger/Audit Service** and the **Human Review & Approval Service** are both exercised but are thin enough to implement as one lightweight service each rather than separately staffed efforts at this scope — noted in the backlog below.

The **Notification Service** is exercised, but only its immediate-push path for a Severity-1 event — the digest-scheduling half of it is not touched by this trace and is deferred.

**Database stores (six):** `triggers`, `commercial_events`, `impacts`, `actions`, `approvals`, and an append-only `ledger`. Plus three supporting stores the trace's own steps require even though they weren't named as headline objects: a short-lived **connector idempotency cache** (Phase 1.1 of the trace), a **dispatch idempotency store** keyed on the `Idempotency-Key` header (Phases 11.3, 12.2, 13), and an **artifact identity map** — because the trace's own PO-4471-is-really-SAP-PO-4500018823 moment is not incidental, it is the literal mechanism that makes citations trustworthy, and it needs a real table, not a hardcoded lookup.

**APIs (nine, all literally called in the trace):**
- Inbound: `POST /connectors/procore/{project_id}` (webhook), `POST /connectors/email/callback` (delivery confirmation)
- Human-facing: `GET /events/{event_id}`, `POST /actions/{action_id}/approve`
- Outbound to Procore: `GET /rest/v1.0/projects/{id}/rfis/{id}`
- Outbound to the email connector: `POST connector://email/dispatch`
- Outbound to SAP: `GET .../A_PurchaseOrder('{po}')` (CSRF fetch), `PATCH .../A_PurchaseOrder('{po}')`, `PATCH .../to_PurchaseOrderItem('{item}')`
- Realtime: one WebSocket channel, subscribed per `project_id`

**UI (three surfaces, one of them partial):**
- **Commercial State** — only its hero line and severity count are exercised; no historical trend, no portfolio rollup.
- **Event Inbox** — only a single new row appearing, severity-sorted; bulk-acknowledge and multi-event sorting are not exercised.
- **Event Detail** — the most heavily exercised surface: severity-ordered impact list, per-impact evidence click-through, per-action approve, live containment counter, closing cost figure. The **Evidence Explorer** is exercised only as a click-through interaction from this page — build it as an embedded panel, not a separate routed page, at this scope.

---

## The backlog, in dependency order

Each item states what it builds, why it must come before the next, and what from the fuller design is explicitly not included yet.

### 1. Artifact identity map + connector configuration store
**Builds:** the table mapping Downstream's internal `artifact_ref` (e.g. `po_4471`) to each connected source system's real identifier (Procore's opaque `id` vs. `display_number`; SAP's 10-digit PO number, Company Code, Plant), plus stored OAuth credentials and the granted scope per connection.
**Why first:** every other service in this trace either reads from or writes to a system-of-record identifier through this map. The Procore adapter's `display_number` handling, the SAP adapter's `4500018823` lookup, and the `acting_credential_scope` field on the envelope all depend on this existing before a single event can be processed correctly.
**Deferred:** an admin UI to manage connections (the Integrations page). For this trace, seed the map and credentials directly — a human-facing connection wizard is real future work, not required to run this scenario.

### 2. Graph Layer, seeded
**Builds:** the graph store holding this project's key-index — the exact subgraph shown in Phase 4.1 (RFI → Spec → Cost Code → PO → Vendor, plus the two lower-confidence edges to PO-4512 and Sched-3410) — with a write path that appends new, versioned, non-destructive edges.
**Why next:** Key Resolution and the Reasoning Pipeline's Candidate Resolution stage both traverse this graph; nothing downstream can be tested without seed data in it.
**Deferred:** an automated calibration pipeline that builds this graph from a customer's full document history. For this trace, the graph is seeded directly from known project data — the general-purpose ingestion-and-graph-construction pipeline is real future work.

### 3. Event Bus (topics only)
**Builds:** the partitioned, ordered-per-project message backbone, provisioned with exactly the ten topics this trace uses.
**Why next:** every service from here on either publishes or consumes on it; standing it up before the first business service means every subsequent service can be tested against a real bus from day one instead of a mocked one later.
**Deferred:** the full topic catalog implied by the systems architecture for domains this trace never touches (nothing here — this trace's topic list is already complete for its own scope).

### 4. Procore Connector Adapter
**Builds:** the inbound webhook receiver, the connector-level idempotency cache (Phase 1.1), the enrichment GET-back, and `EngineeringEventEnvelope` construction — including `display_number`, split `item_id`/`version_id`, `region`, and `acting_credential_scope`, per the connector validation.
**Why next:** it is the trace's actual starting point; nothing upstream of it exists to test against until it can produce a real envelope.
**Deferred:** the Autodesk Construction Cloud, Oracle ERP, and ERPNext adapters — none are touched by this trace. Also deferred: Procore rate-limit backoff handling (this trace makes one callback call, never approaches the 3,600/hour ceiling) and webhook redelivery-storm handling beyond the basic idempotency check already scoped.

### 5. Ingestion & Normalization Service
**Builds:** envelope validation, the dedup check against the idempotency cache, the event-worthiness filter, the `triggers` table, and the `trigger.detected` emission.
**Why next:** it is the first consumer the Procore adapter's output must reach, and the first durable database write in the whole pipeline — everything after this depends on a real, persisted Trigger existing.
**Deferred:** tuning the event-worthiness filter against real noisy traffic (ASIs, typo-fix revisions) — this trace's one Trigger is unambiguously event-worthy, so the filter only needs to exist, not be tuned.

### 6. Key Resolution Service
**Builds:** the service consuming `trigger.detected`, querying the graph for `spec_section` and `drawing` key matches, and emitting `keys.resolved` with match scores.
**Why next:** depends on both the Graph Layer (step 2) and a real Trigger (step 5) existing; it is the first place the two converge.
**Deferred:** fuzzy/normalized matching across inconsistent naming conventions at scale — this trace's keys match cleanly against pre-seeded graph data; the harder matching logic for messy real-world naming is real, later work.

### 7. Reasoning Pipeline (all five sub-stages, one service)
**Builds:** 5a Trigger Understanding (document-intelligence extraction from the one cited PDF and drawing), 5b Candidate Resolution (graph traversal enriched with artifact lifecycle snapshots), 5c Confidence Tiering, 5d Severity Computation (the deterministic function), 5e Grounded Drafting (the four Action drafts).
**Why next:** depends on `keys.resolved` (step 6) and needs the artifact identity map (step 1) to fetch lifecycle snapshots — the first point where all upstream work is consumed together.
**Deferred:** a general-purpose vector index/RAG corpus spanning a project's entire document history. This trace's grounded drafting only needs to cite the specific documents Trigger Understanding already opened — a narrow, targeted retrieval, not a full semantic-search engine. Build the narrow version; the general one is real future work.

### 7a. Artifact snapshot cache
**Builds:** a lightweight store of each Commercial Artifact's `lifecycle_position` and `value`, populated by calling the SAP adapter's `fetchArtifactSnapshot` and cached for the Reasoning Pipeline's 5b stage to read without hammering SAP on every pass.
**Why here:** the Reasoning Pipeline (step 7) needs this data to compute severity; introducing it alongside the pipeline keeps the dependency visible rather than implicit.
**Deferred:** a live-refresh/subscription mechanism keeping this cache continuously current — this trace reads it once, synchronously, which is sufficient for one event.

### 8. Commercial Event Service
**Builds:** the `commercial_events`, `impacts`, and `actions` tables; the state-machine enforcement (`DETECTED → TRIAGED → ACTIONED → CONTAINED → CLOSED`, and the rule that closure requires every Impact resolved); consumption of the Reasoning Pipeline's output to create one Event with four Impacts and four Actions; emission of `event.created`, `impact.tiered`, `severity.computed`, `action.drafted`.
**Why next:** this is the domain core everything human-facing depends on — it cannot be built before the Reasoning Pipeline exists to feed it, and nothing after it can be tested without it.
**Deferred:** support for an Event with impacts spanning multiple Triggers, or multiple concurrent open Events on one project — this trace has exactly one Trigger producing exactly one Event.

### 9. Ledger / Audit Service
**Builds:** the append-only table and the write path that mirrors every state transition emitted above into it, plus the live query that computes Commercial State from open, non-closed events — the mechanism, not a UI, that proves "Commercial State is never stored, only computed."
**Why next:** it needs real events flowing (step 8) to have anything to append, and the Commercial State page (step 12) depends on its query existing first.
**Deferred:** the Timeline/Ledger UI page for human browsing and export — this trace never has a human open that page; the backend table and its live-query capability are required, the page is not.

### 10. Realtime Gateway
**Builds:** the WebSocket subscription layer, filtering the Event Bus by `project_id` and forwarding exactly the messages this trace uses (`event.created`, `impact.tiered`, `impact.status`, `event.closed`) to connected clients.
**Why next:** depends on the bus (step 3) actually carrying real messages (from step 8 onward) before there's anything meaningful to forward.
**Deferred:** entitlement filtering across many simultaneous users and roles beyond the one connected client this trace shows — the single-user case is what's proven here.

### 11. Notification Service (immediate-push path only)
**Builds:** the severity-based routing rule that fires an immediate push for Severity 1–2, wired to Slack for this trace's one recipient.
**Why here:** depends on `severity.computed` (step 8) existing; it's a narrow, almost standalone consumer and can be built any time after that, placed here because the trace's own sequence has it fire right after Event creation.
**Deferred:** the digest-batching path for Severity 3–4 — this trace's lower-severity impacts never generate their own notification, only the event-level Sev-1 push fires, so the digest scheduler is not required yet.

### 12. Human Review & Approval Service + Commercial State / Event Inbox / Event Detail UI
**Builds:** `GET /events/{event_id}`, `POST /actions/{action_id}/approve` (supporting exactly the two decision shapes this trace uses — `APPROVED` and `ACKNOWLEDGED_NO_ACTION`); the Commercial State page's hero line and top-of-list rendering; the Event Inbox's single-row severity-sorted appearance; the Event Detail page in full, including the embedded Evidence Explorer click-through to a cited source document.
**Why next:** this is the first human-facing surface, and it cannot be meaningfully built or demoed before an Event genuinely exists (step 8), the Ledger can answer "is anything open" (step 9), and the Realtime Gateway (step 10) can push updates into it live.
**Deferred:** `PATCH /actions/{id}` (edit-before-approve) and a reject flow — this trace only exercises approve-as-drafted and one acknowledge-with-no-action; both are real, near-term additions but not required to run this scenario. Also deferred: bulk-acknowledge across multiple events in the Inbox (only one event exists here), and the standalone Evidence Explorer *page* (a full document browser) — the embedded single-citation click-through is sufficient for this trace.

### 13. Synchronization Service — email tier
**Builds:** dispatch of an `ACTION.approved` event to the generic email connector, the `Idempotency-Key` generation and the dispatch idempotency store, and consumption of the delivery-confirmation webhook to emit `action.confirmed`.
**Why next:** depends on the Approval Service (step 12) actually producing `action.approved` events, and is the simpler of the two synchronization tiers — build it before the ERP tier to validate the confirmation-loop pattern on the easier case first.
**Deferred:** retry-with-backoff on dispatch failure and the dead-letter/human-escalation path — this trace's happy-path dispatch succeeds on the first attempt; failure handling is real, necessary, and explicitly out of scope for this exact scenario.

### 14. Synchronization Service — ERP (SAP) tier
**Builds:** the CSRF-token fetch-then-write ceremony, the OData PATCH for both the hold-flag and the reschedule field, and confirmation via SAP's own Change Documents.
**Why last:** it is the most demanding contract validated in this project, depends on the artifact identity map (step 1) for the real PO number, and depends on the email tier (step 13) having already proven the approve → dispatch → confirm → contain → close loop once on an easier path.
**Deferred:** the Oracle ERP and ERPNext write-back adapters (not touched by this trace), and org-structure collision handling across multiple Company Codes/Plants beyond the one seeded here.

---

## Master deferred list

Explicitly not required to run this scenario, and not built by the backlog above: Autodesk Construction Cloud, Oracle ERP, and ERPNext connectors; the Integrations admin UI; the Project Graph UI page; the Timeline/Ledger UI page; the Settings/Admin UI; reject and edit-before-approve action flows; bulk-acknowledge across events; the digest notification path; retry/backoff and dead-letter handling; rate-limit-aware backoff; a general-purpose vector index/RAG corpus; automated graph calibration from a document corpus; multi-project or portfolio-level Commercial State rollups; support for multiple concurrent open Events or Events spanning multiple Triggers; and forecasting of any kind. All of these are real, named parts of the frozen design — none of them is exercised by this trace, so none of them belongs in this backlog.

## Recommendations

1. **Build in the order above, not by service "importance."** The dependency chain is real: the artifact identity map and the seeded graph have no glamour, but nothing else in the trace can be honestly tested without them existing first.
2. **Treat steps 13 and 14 as a deliberate pair, in that order.** The email tier is the easier contract; proving the full approve-dispatch-confirm-close loop on it before attempting SAP's CSRF ceremony isolates which layer broke if something fails during integration testing.
3. **Resist adding anything from the master deferred list "while you're in there."** Every item on it is legitimate future work; none of it is required to make this exact scenario run, and the trace's value as a reference implementation depends on the backlog matching it exactly.

## Caveats

- This backlog reflects only what the single reference trace exercises. A second scenario (a rejected action, a failed dispatch, a second concurrent event) would surface additional requirements not listed here — this is a floor, not a ceiling, on what Downstream eventually needs.
- Sizing/estimation (days, story points) was deliberately not attempted here, since the trace establishes dependency order and scope, not team velocity — that's a separate exercise once a team and its capacity are known.