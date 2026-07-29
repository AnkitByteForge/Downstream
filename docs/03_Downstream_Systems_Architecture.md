# Downstream — Internal Systems Architecture
### Chief Systems Architect blueprint · information flow first, technology in service of it

**Governing rule for this document:** every section is organized around *what information exists, in what shape, and what transforms it next*. A named technology only appears once the information-flow reason for that stage existing is fully argued. If your backend team reads only the stage headers and the object definitions, they should already understand the system; the technology notes are implementation guidance, not the argument.

**The one architectural law that disciplines every decision below**, inherited from the product design: **the Commercial Event is the only thing anyone writes. Commercial State is never stored — it is only ever computed.** This single law is why the system below is event-sourced rather than CRUD, and why the Ledger (Stage 11) is not a feature but the spine.

---

## 0. The end-to-end flow, in one pass, before the detail

An engineering change is detected → normalized into a canonical Trigger → resolved against the project's key-index to find candidate commercial artifacts → each candidate is tiered by confidence and the whole set is scored for severity → a Commercial Event is opened, carrying Impacts, each with drafted Evidence and an Action → the human is notified in proportion to severity → the human reviews, edits, and approves each Action individually → approved Actions are synchronized outward (drafted communication or ERP write-back) → confirmation closes the Impact → all Impacts closed closes the Event → every state transition, from detection to closure, is appended to an immutable Ledger, which is the only place "Commercial State" is ever computed from, live, on read.

Fourteen stages implement that sentence. Each is a **service boundary** — independently deployable, independently scalable, communicating only through the event bus or well-typed synchronous APIs, never through a shared database.

---

## 1. Connector Layer — the ingestion boundary

**What information exists here:** raw, heterogeneous payloads in whatever shape Procore, Autodesk Construction Cloud, SAP, or Oracle ERP natively produce them — an RFI approval webhook from Procore looks nothing like a PO status row from SAP.

**Why this boundary must exist as its own layer, not be absorbed into ingestion:** every future system we connect to (a new ERP, a new document platform, eventually a scheduling tool) must be addable by writing *one new adapter*, never by touching anything downstream. This is the single decision that keeps the system extensible instead of rebuilt per customer.

**The Connector Interface (the contract every adapter must implement, regardless of source system):**
- `fetchEngineeringEvents(since: cursor) → EngineeringEventEnvelope[]` — pull or webhook-push, adapter's choice internally, same output contract externally.
- `fetchArtifactSnapshot(artifactRef) → CommercialArtifactSnapshot` — on demand, get the current state (status, value, lifecycle position) of a specific PO/vendor/delivery.
- `pushAction(action: ActionPayload) → DispatchReceipt` — send a drafted communication or write-back transaction; always returns a receipt, never assumes success.
- `healthCheck() → ConnectionHealth` — scope granted, last successful sync, error state.

Two adapter families exist on day one: **Engineering Connectors** (Procore, ACC — surfacing RFIs, drawing revisions, spec changes) and **Commercial Connectors** (SAP, Oracle, Procore Commitments — surfacing POs, vendors, schedule of values, lifecycle status). Every adapter normalizes its native payload into one of exactly two canonical envelopes before anything else in the system ever sees it:

- **EngineeringEventEnvelope** — `{ source_system, source_id, type (RFI_APPROVED | DRAWING_REVISED | SPEC_UPDATED), spec_section_refs[], drawing_refs[], location_refs[], raw_document_ref, occurred_at }`
- **CommercialArtifactSnapshot** — `{ source_system, source_id, artifact_type (PO | VENDOR | DELIVERY), cost_code, spec_section_refs[], lifecycle_position, value, vendor_ref, project_ref }`

**Storage at this boundary:** none, beyond a short-lived idempotency cache (has this `source_id` + `occurred_at` already been enveloped?) to survive connector redelivery — connectors are notoriously "at least once," and this is the first of several places the system must absorb that honestly rather than pretend otherwise.

---

## 2. Ingestion & Normalization Service

**What information exists here:** validated canonical envelopes, still project-scoped but not yet meaningful — a Trigger doesn't exist yet, only a candidate for one.

**What it does:** deduplicates (via the idempotency cache above), validates envelope shape, resolves the `project_ref`, and — critically — decides whether an EngineeringEventEnvelope is even *event-worthy* (a drawing revision that only fixes a typo should never become a Commercial Event; a lightweight, fast, rule-based filter runs here so the expensive reasoning pipeline in Stage 6 is never wasted on noise).

**Output:** a persisted **Trigger** object — the first durable internal object in the system — and an emission onto the event bus.

**Trigger (internal object):** `{ trigger_id, project_id, type, source_envelope_ref, spec_section_refs[], drawing_refs[], location_refs[], raw_document_ref, occurred_at, status: PENDING_RESOLUTION }`

---

## 3. The Event Bus — the system's backbone

**Why an event bus, not request/response chaining:** everything from Stage 4 onward is a pipeline of independent, potentially slow, potentially-failing steps (graph traversal, an LLM call, a notification dispatch) acting on the same Trigger. Chaining them as synchronous calls means one slow AI call blocks the whole path and one failure loses the work. An event bus lets every stage consume, process, and emit independently, retry on its own, and lets us add a new consumer (a future Schedule domain, per the product roadmap) without touching a single existing service.

**Delivery guarantee:** at-least-once, ordered per `project_id` partition key (ordering matters within a project — a Trigger must be key-resolved before it can be tiered — but nothing requires cross-project ordering, so partitioning by project is both correct and how the system scales horizontally).

**Canonical topics (the schema registry is the real contract here — every message is a versioned, typed schema, never a loose JSON blob):**

| Topic | Emitted by | Consumed by |
|---|---|---|
| `trigger.detected` | Ingestion & Normalization | Key Resolution |
| `keys.resolved` | Key Resolution Service | Graph Layer (write), Reasoning Pipeline (read) |
| `graph.updated` | Graph Layer | Reasoning Pipeline |
| `event.created` | Commercial Event Service | Reasoning Pipeline, Ledger |
| `impact.tiered` | Reasoning Pipeline (confidence stage) | Commercial Event Service, Ledger, Realtime Gateway |
| `severity.computed` | Reasoning Pipeline (severity stage) | Commercial Event Service, Notification Service, Ledger, Realtime Gateway |
| `action.drafted` | Reasoning Pipeline (drafting stage) | Commercial Event Service, Ledger |
| `action.approved` | Approval Service | Synchronization Service, Ledger |
| `action.dispatched` | Synchronization Service | Ledger, Realtime Gateway |
| `action.confirmed` | Synchronization Service (receipt handler) | Commercial Event Service, Ledger, Realtime Gateway |
| `event.closed` | Commercial Event Service | Ledger, Realtime Gateway |

Every consumer is independently scalable and independently replaceable — this table *is* the system's real architecture diagram; the service list in the sections below is just who's allowed to touch each topic.

---

## 4. Key Resolution / Entity Linking Service

**What information exists here:** a Trigger with raw references (spec sections, drawing sheets, locations) that mean nothing yet to any purchase order.

**What it does:** resolves those raw references against the **Graph Layer's** key-index to find every Commercial Artifact that shares a key — the literal mechanism of "RFI cites Spec 23 31 13 → that's PO-4471's cost code." This is where naming inconsistency across documents and systems is absorbed: fuzzy/normalized matching where exact keys don't align, each match carrying its own match-quality score forward (this score becomes the raw material for the Confidence Tiering stage later — it is not itself the confidence tier, it's one input to it).

**Output:** a set of `(trigger_id, artifact_ref, match_score, match_basis)` candidate links, emitted as `keys.resolved`.

---

## 5. The Graph Layer — the project's persistent memory

**What information exists here:** the durable, versioned map of how a project's spec sections, cost codes, drawing references, schedule activities, purchase orders, and vendors interconnect. This is the only stateful "understanding" of a project that persists between events — everything upstream is stateless processing of a single Trigger; the Graph Layer is what makes the tenth Trigger smarter than the first.

**Two distinct access patterns, deliberately separated:**
- **Write path** — appends new nodes/edges as Commercial Artifacts change (a new PO issued, a vendor reassigned) and as Key Resolution discovers new or strengthened links. Writes are versioned, never destructive — an edge's confidence can be revised, but its history is retained, because a later dispute may need to know what the graph believed *at the time* a decision was made, not just what it believes now.
- **Read path** — the traversal a Trigger's resolved keys run against to find the full blast radius, including artifacts *not* directly key-matched but reachable within a small number of hops (the "second-order" impacts from the product design — the hanger steel that depends on the duct, not just the duct itself).

**Storage shape:** a native graph store, because the core operation — "traverse from this node outward N hops, weighted by edge confidence" — is exactly what graph databases are built to do efficiently and what a relational join-chain does badly at scale. The graph is *derived and rebuildable* from the Ledger and the Commercial Artifact store, which matters enormously: the graph is a read-optimized index, never the system of record for anything. If it's ever wrong or needs a schema change, it can be rebuilt from the append-only Ledger without losing a single fact.

---

## 6. The Reasoning Pipeline — the AI core, decomposed into five honest stages

This is the part of the system doing the work the mission names directly, and it is deliberately built as five separable stages rather than one opaque "AI does it" box — because every stage has a different failure mode, a different confidence profile, and a different reason to exist.

**6a — Trigger Understanding (document intelligence).** Input: the Trigger's raw source document (an RFI PDF, a drawing revision). Output: structured fields — the specific spec sections, quantities, and locations the change actually touches, each with an extraction confidence. This is a **vision-language + layout-aware extraction** step, not OCR — construction documents are visually structured (tables, callouts, revision clouds) and the model must read that structure, not just the text.

**6b — Candidate Resolution.** Consumes `keys.resolved` and traverses the Graph Layer (Stage 5's read path) to produce the full candidate blast radius — every Commercial Artifact reachable from the Trigger's keys, first-order and second-order.

**6c — Confidence Tiering.** For every candidate artifact, combines the key-match score (Stage 4), the extraction confidence (Stage 6a), and the graph edge's own confidence (Stage 5) into one of exactly three tiers — **Certain, Probable, Possible** — each carrying a plain-language reason, never a bare score. This stage's only job is honest calibration; it is explicitly forbidden from ever rounding a "Probable" up to "Certain" for a cleaner-looking demo, because the entire product's trust model depends on this stage refusing to lie.

**6d — Severity Computation.** A **deterministic function, not a model** — this is the one reasoning stage that must never be a black box, because it's the number the whole notification and prioritization system hangs on. `severity = f(artifact_value, lifecycle_position_weight, blast_radius_size, confidence_tier)` — a shipped, high-value, Certain impact is Severity 1; a draft, low-value, Possible impact is Severity 4. Deterministic and inspectable on purpose: a procurement manager must be able to ask "why is this a Sev-1" and get an arithmetic answer, not a model's opinion.

**6e — Grounded Drafting.** An LLM drafts the Action's content (the hold notice, the revision query) — but strictly **retrieval-grounded**, meaning it is only permitted to write sentences it can attach a citation to from the Trigger's source document or the artifact's own record. This is the stage that produces user-facing prose, and it is the *last* stage precisely because everything it writes must be traceable to facts already established, with certainty, by 6a–6d — the drafting stage never gets to introduce a new fact.

**Why five stages and not one model call:** each stage can fail, be measured, and be improved independently — extraction accuracy is a completely different problem from severity math, and conflating them into one prompt would make both undebuggable and would make the system's honesty about its own uncertainty impossible to enforce.

---

## 7. The Commercial Event Service — the domain core

**What information exists here:** the Commercial Event aggregate itself — the primary object, and the only thing in the whole system that owns a *lifecycle*.

**Internal objects owned by this service:**
- **CommercialEvent** — `{ event_id, project_id, trigger_id, severity, status: DETECTED|TRIAGED|ACTIONED|CONTAINED|CLOSED, created_at, closed_at }`
- **Impact** — `{ impact_id, event_id, artifact_ref, confidence_tier, confidence_reason, lifecycle_position_at_detection, evidence_refs[], action_id, status }`
- **Action** — `{ action_id, impact_id, type, drafted_content, status: DRAFTED|APPROVED|REJECTED|EDITED|SENT|COMPLETED }`
- **Approval** — `{ approval_id, action_id, user_id, decision, edited_content?, decided_at }` — deliberately its own object, immutable once written, separate from Action's own (mutable-until-approved) content, so the audit question "who decided what, when" can never be altered after the fact even if the action's draft could theoretically still be revised pre-approval.

**State machine discipline:** an Event cannot reach `CLOSED` until every one of its Impacts' Actions reaches `COMPLETED` or `REJECTED`-with-reason. This is enforced here, centrally, so "closed" always means what it claims to mean — this is the guarantee the Ledger and the whole trust model rest on.

**This service is the only writer of Commercial Event/Impact/Action state.** Everything upstream (reasoning) and downstream (synchronization) only ever *proposes* transitions via events; this service is where they become real, which is what makes it possible to say, truthfully, that nothing executes without passing through one auditable choke point.

---

## 8. Notification & Delivery Service

**What information exists here:** a `severity.computed` event and an org's notification policy (Stage-configured, per role, per severity).

**What it does:** routes — Severity 1–2 events push immediately through whatever channel the user has configured (in-app, email, Slack/Teams); Severity 3–4 events are held and rolled into a scheduled digest. This is a pure **routing** service with no reasoning of its own — severity was already decided upstream; this service's entire job is respecting the recipient's attention.

---

## 9. Human Review & Approval Service

**What information exists here:** the API surface the frontend actually talks to. This service is a thin, synchronous read/write layer over the Commercial Event Service's aggregates — it does not duplicate state, it exposes it.

**Key operations:** `GET /events?status=open&sort=severity`, `GET /events/{id}` (full Impact/Evidence/Action tree), `POST /actions/{id}/approve` (writes an Approval, which the Commercial Event Service consumes to advance the Impact and, potentially, the Event's status), `POST /actions/{id}/reject`, `PATCH /actions/{id}` (edit drafted content, pre-approval only). Every write here is synchronous and returns the updated state immediately — this is the one place in the system where request/response, not the event bus, is the right shape, because a human is sitting there waiting for confirmation that their click registered.

---

## 10. Synchronization Service — the write-back boundary

**What information exists here:** an approved Action, ready to leave the system.

**What it does:** dispatches through the Connector Layer's `pushAction` interface — either as a drafted, ready-to-send communication (email/PDF to a vendor — the default, lower-trust integration tier) or, where the org has granted write scope, as a proposed transaction into the ERP's own commitments workflow (a PO hold flag, a revision request) — **never as a silent write that bypasses that system's own controls.**

**Idempotency and retry, treated honestly:** every dispatch carries an idempotency key so a retried send can never double-notify a vendor or double-write an ERP hold. Failures retry with backoff; a dispatch that exhausts retries surfaces back to the human as an explicit, visible failure — it never fails silently, because a silent failure here is precisely the six-weeks-later discovery the entire product exists to prevent.

**Confirmation loop:** receipts from `pushAction` flow back as `action.confirmed`, which the Commercial Event Service consumes to move the Action to `COMPLETED` — synchronization is not "fire and forget," it's a loop that closes.

---

## 11. The Ledger / Audit Service — the system of record, and the only place "state" is computed

**What information exists here:** every state transition, ever, on every Trigger, Event, Impact, Action, and Approval — append-only, never edited, never deleted.

**Why this is architecturally separate from the Commercial Event Service's own database**, even though it stores overlapping facts: the Commercial Event Service's tables answer "what is true right now" (optimized for fast reads on open work); the Ledger answers "what was true, and known, at every point in the past" (optimized for complete, tamper-evident history). This is a deliberate **CQRS split** — the write model (Commercial Event Service) and the long-term read model (Ledger) are allowed to diverge in shape because they serve different questions, and reconciling them into one schema would compromise one or the other.

**The critical consequence:** *Commercial State — "3 open events, 1 critical" — is never a stored value anywhere in the system. It is a live query over the Ledger* (or, for hot-path UI performance, a cached projection rebuilt from the Ledger on every relevant event). This is the direct technical expression of the product law: the Event is real; the State is a view.

---

## 12. The Realtime Gateway — bridging the event bus to a live UI

**What information exists here:** the same domain events already flowing on the bus (`impact.tiered`, `severity.computed`, `action.confirmed`, `event.closed`), now needing to reach a specific human's open browser tab within milliseconds.

**What it does:** a thin, stateless gateway subscribing to the event bus on behalf of connected clients, filtered per `project_id` (and per-user entitlement — never leak another project's events across the wire) and fanned out over a persistent connection. This is the *only* new component required to make the UI feel alive; everything it forwards already exists as a real domain event, which is precisely what guarantees the frontend can never show an animation that isn't backed by something real (the Demo Mode discipline from the product design, now enforced architecturally rather than just by convention).

---

## Storage boundaries — who owns which store, and why they don't share

| Store | Owned by | Shape | Why this shape |
|---|---|---|---|
| Operational DB (relational) | Commercial Event Service | Normalized rows: Event, Impact, Action, Approval | Fast, transactional reads/writes on "what's open right now"; strong consistency for the state machine |
| Graph store | Graph Layer | Nodes/edges: spec sections, cost codes, artifacts, vendors | Multi-hop traversal is the native operation; a relational join-chain doesn't scale to this access pattern |
| Event log (durable, ordered) | Event Bus | Partitioned, replayable stream | The backbone every service consumes; replayable so a new consumer (a future Schedule domain) can be added and backfilled without re-triggering the world |
| Ledger store (append-only) | Ledger / Audit Service | Immutable transition log | Tamper-evident by construction; the long-term company asset; source of truth for Commercial State |
| Document/blob store | Connector Layer (cache) | Source document blobs, cached for citation display | Evidence must open to the *actual* document; cached copies exist for latency, never as the source of truth (the connector's origin system remains authoritative) |
| Vector index | Reasoning Pipeline (6a/6e) | Embeddings of project documents, scoped per project | Supports retrieval-grounded drafting (6e) and extraction context (6a); strictly project-partitioned, never cross-project |
| Read-model cache | Realtime Gateway / API layer | Precomputed Commercial State projections | Avoids recomputing the Ledger query on every dashboard load; invalidated/rebuilt on every relevant Ledger append, never independently written |

**The one rule that governs every row in this table:** no store above is ever the *only* place its information lives except the Ledger. The graph, the caches, and the read models are all rebuildable from the Ledger and the connectors' origin systems — which means the system can lose an entire derived store and recover completely, but can never lose the Ledger without losing the company's actual asset.

---

## Async workflow model — choreography where it's resilient, orchestration where a human is involved

**Stages 2 through 7 (detection through drafting) run as pure choreography** over the event bus: each service reacts to the topics it cares about and emits its own, with no central coordinator. This is correct here because the whole path is machine-speed and any single stage's failure should only block *that Trigger's* progress, retried independently, never the whole pipeline.

**Stages 9 through 10 (human approval through synchronization) are managed by a durable workflow orchestrator, not pure choreography.** The reason: a human may take minutes, hours, or days to approve an Action, and the system must hold that *exact* pending state durably, survive restarts, escalate on timeout (a Sev-1 unactioned for six hours should itself trigger an escalation notification), and resume synchronization exactly where it left off. This is a fundamentally different reliability shape than the fire-and-forget choreography upstream — it's a long-running, resumable process with a human as one of its steps, which is precisely what a durable workflow engine (rather than a stateless consumer) is for.

---

## Consistency, idempotency, and failure — stated plainly, not assumed away

- **Connector delivery is at-least-once.** The Ingestion service's idempotency cache (Stage 1) is the system's first and most important defense; every downstream stage can otherwise assume "I've seen this Trigger before" is already handled and never re-implement dedup itself.
- **The reasoning pipeline can fail per-stage without corrupting the Event.** A Trigger stuck mid-pipeline (say, 6a extraction failed) sits in a `PENDING_RESOLUTION` state, visibly, rather than silently producing a wrong or empty Event — an Event is only created once enough of the pipeline has succeeded to be honest about what it knows, tiering low-confidence-throughout as `Possible` rather than failing to include it.
- **External writes (Stage 10) are the system's highest-risk boundary** and carry idempotency keys plus explicit, human-visible failure surfacing on exhausted retry — this is a deliberate design bias toward "tell the human it didn't send" over "silently believe it did."
- **The Graph Layer is a rebuildable index, never a source of truth** — if it's ever inconsistent, it's cheaper and safer to rebuild it from the Ledger and connector snapshots than to attempt in-place repair.

---

## Multi-tenancy and security boundaries

Every store above is **partitioned by `project_id` at the schema or index level, never merely filtered in application code** — this is a hard boundary, not a convention, because a single cross-tenant leak in a construction-legal-evidence product is an existential failure, not a bug. Connector credentials are scoped per-project and per-integration-tier (read-only vs. read/write, as established in the product design's staged-trust onboarding) and stored in a secrets boundary the Connector Layer alone can access — no other service ever holds a customer's Procore or SAP credentials directly.

---

## What this means for the prototype, honestly

Not all fourteen stages need to be independently deployed services on day ten. The **information flow above must be fully real** — Trigger → Key Resolution → Graph → five-stage Reasoning → Event/Impact/Action → Approval → Synchronization → Ledger — because that flow *is* the product's credibility. But several stages can share a process and a database in the prototype without breaking the architecture's honesty, **as long as the boundaries above remain true logical boundaries** (separate schemas, separate object ownership, an internal function call standing in for what will later be an event-bus hop). The one boundary that must be real, even in the prototype, is the **Ledger as an actual append-only table that Commercial State is actually queried from live** — because that is the one architectural fact the whole demo's "count to zero, computed not scripted" moment depends on, and it is also the one piece of the real company you are already building, not simulating.

---

## The one-paragraph version, for anyone who only reads this far

A change enters through a connector and is normalized into a Trigger; Key Resolution finds what it touches via the Graph Layer's persistent key-index; a five-stage Reasoning Pipeline turns that into a tiered, severity-scored, evidence-cited, drafted Commercial Event with its Impacts and Actions; a human reviews and approves through a thin synchronous API; Synchronization dispatches the approved Action outward through the same Connector interface, idempotently, with a confirmation loop; every step, from the first detection to the final confirmation, is appended to an immutable Ledger — which is the only place "is everything okay?" is ever actually answered from, live, on demand. Nothing upstream of the Ledger is trusted as permanent; everything downstream of it is rebuildable. That asymmetry is the whole architecture.