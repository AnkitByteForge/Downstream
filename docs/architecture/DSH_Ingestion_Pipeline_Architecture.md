# DSH-Atascadero → Downstream: Data-Flow Architecture

### Planning document · not frozen · requires approval before implementation

**Status:** proposal for review. Nothing in `/docs` (01–07) is changed or reinterpreted by this document. Nothing here is implemented. This document answers one question: *how does the real DSH-Atascadero PDF corpus become fuel for the already-frozen Downstream pipeline, without inventing a new service, a new event, or a new service boundary.*

**Read before this document, in this order** (per `IMPLEMENTATION_STATUS.md` §1): `03_Downstream_Systems_Architecture.md`, `07_Downstream_Implementation_Blueprint.md`, `06_Downstream_Implementation_Backlog.md`, `docs/reference/The Reference Engineering System.md`, `docs/adr/ADR-007.md`, `docs/reference/Canonical_Demo_Dataset.md`, `docs/research/DSH_Atascadero_Reconnaissance.md`, `IMPLEMENTATION_STATUS.md` in full, plus the actual code in `packages/*`, `apps/ingestion-service` (empty scaffold), `apps/connector-procore` (empty scaffold), and `reference-systems/reference-engineering-system/backend/src/domain/*`.

---

## 0. The one-sentence answer

**The DSH-Atascadero document-ingestion pipeline is a new producer *into* the Reference Engineering System — not a new Downstream service, not a new connector family, not a new entity type.** It plays exactly the role RES-1's hand-written `meridian_tower.py` seed script already plays (populating `Drawing`/`DrawingVersion`/`DesignChange` rows), except it derives those rows from real PDFs instead of from a human typing literal values, and it does so as a second RES project (`DSH-Atascadero`, project #2) sitting alongside the existing `Meridian Tower` (project #1) — reusing RES's already-built, already-tested project isolation. Once a fact lands in RES as a real `DrawingVersion` and is `issue`d, **everything downstream of RES is already fully specified and requires zero new design**: RES's existing thin webhook fires → the not-yet-built `connector-procore` (already scoped to talk to RES, per `IMPLEMENTATION_STATUS.md` §10.1) receives it and enriches it into a real `EngineeringEventEnvelope` → the rest of the frozen 14-stage pipeline runs unmodified.

This means the "new" work is entirely **upstream of the Connector Layer**, in a region the frozen architecture deliberately left unspecified because it belongs to whatever real system a customer's engineering data already lives in (real Procore, real ACC) — for DSH-Atascadero, no such system exists yet, so this document specifies the pipeline that stands in for "a human data-entry team transcribing the drawing set into Procore," except deterministic, provenance-preserving, and auditable.

---

## 1. Twelve objects, defined and owned

| # | Object | Definition | Owner | New? |
|---|---|---|---|---|
| 1 | **Document** | One immutable source PDF (`02_Main_Plans_Bldg_3319.pdf`) | Document Ingestion Pipeline (DIP) — raw blob store | New (DIP) |
| 2 | **Page** | One page of a Document, classified by extractability (`native_text`\|`raster_embedded`\|`vector_curve`\|`mixed`) | DIP — page manifest | New (DIP) |
| 3 | **Drawing / Specification** | A named sheet (`E0.4`) or spec section (`23 74 13`) — the human-meaningful unit a page (or page range) represents | DIP identifies it (via bookmark/title-block parsing); **RES owns the persistent record** (`Drawing`, `SpecSection`) once created | Frozen shape (RES), new *population mechanism* (DIP) |
| 4 | **Extracted evidence** | The literal output of a deterministic extraction step against one page: native text, OCR text + word bounding boxes, or reconstructed table rows — always carrying provenance | DIP — evidence store, immutable per (document, page, extractor_version) | New (DIP) |
| 5 | **Structured engineering object/state** | A typed, DIP-internal working record built from evidence — e.g. one row of the E0.4 schedule: `{new_designation, fed_from_panel, volts, hp, fla, mca, ...}` with a provenance pointer | DIP — internal only, never persisted past promotion or exposed outside DIP | New (DIP) |
| 6 | **Revision/version** | RES's own `DrawingVersion` (`revision_label`, `issuance_date`, `status`, `revision_clouds[]`, `superseded_by_id`) | **RES** (frozen shape, ADR-007-adjacent, already implemented for RFI-214/DWG-E-1.1) | Frozen |
| 7 | **Detected engineering change** | A deterministic diff between two Structured-engineering-state snapshots of the same sheet (Rev A's row vs. Rev B's row for the same equipment tag) | DIP — change-detection stage; its output is *promoted* into a new RES `DrawingVersion` (+ optional `DesignChange`) | New (DIP) |
| 8 | **EngineeringEventEnvelope** | The canonical, source-agnostic shape (`packages/envelope-schemas`) | **Connector Layer** (`connector-procore`, already scoped to talk to RES) | Frozen, unbuilt |
| 9 | **Trigger** | The first durable Downstream-internal object (`packages/domain-models/trigger.py`) | Ingestion & Normalization Service | Frozen, unbuilt |
| 10 | **Commercial Event** | The primary Downstream aggregate | Commercial Event Service | Frozen, unbuilt |
| 11 | **Impact** | Join between Event and Commercial Artifact, carrying `evidence_refs[]` | Commercial Event Service (written by Reasoning Pipeline output) | Frozen, unbuilt |
| 12 | **Action** | The drafted, human-approvable containment step | Commercial Event Service (drafted by Reasoning Pipeline 5e) | Frozen, unbuilt |

**The load-bearing boundary is between #7 and #8.** Everything left of it (#1–#7) is new work this document specifies. Everything right of it (#8–#12) is already fully designed in `/docs` and simply unbuilt — this document changes nothing about it.

---

## 2. Complete data lifecycle, stage by stage — concrete example

**Scenario:** DSH-Atascadero, sheet `E0.4` (Air Handler Replacement Schedule, per the reconnaissance report — a real, confirmed sheet at doc02 p.373). Baseline `Rev A` schedule row for equipment tag `AHU-9C` reads `Fed From Panel: MR6`. A reissued sheet set (e.g. from a later addendum or bid-set revision, hypothetical for this walkthrough since only Addendum 1 was reconnoitered and it did not touch E0.4 — the mechanism below is identical whichever real revision eventually supplies `Rev B`) reads `Fed From Panel: MR7`.

### Stage 1 — Document ingestion
- **Input:** `02_Main_Plans_Bldg_3319.pdf` (Rev A set) and, later, its reissued counterpart (Rev B set).
- **Output:** a content-hashed, immutable copy under `data/reference-projects/dsh-atascadero/raw/`, a `Document` record `{document_id: sha256(bytes), filename, page_count, producer, project_id}`.
- **Owner:** DIP.
- **Persistence:** filesystem/blob store (or later S3-compatible), keyed by content hash.
- **Provenance:** the hash *is* the provenance anchor — any downstream fact can always be traced to "byte-identical to this exact file."
- **Identifiers:** `document_id` (content hash), `project_ref` (`dsh-atascadero`).
- **Consumption by next stage:** Stage 2 opens the document via `pypdfium2` (per reconnaissance recommendation) and walks its pages.
- **Deterministic.** No LLM. Synchronous open, but run inside an offline batch job — never request-driven.

### Stage 2 — Page manifest
- **Input:** the opened Document.
- **Output:** one `page_manifest` entry per page: `{page_index, char_len, image_coverage_pct, path_object_count, classification, needs_ocr, bookmark_t
itle}` — `E0.4` maps to page 373 via the bookmark string `"E0.4 - AIR HANDLER REPLACEMENT SCHEDULE"` (confirmed reliable in reconnaissance: 431 bookmarks, ~1:1 with pages).
- **Owner:** DIP.
- **Persistence:** `derived/page_manifest/<document_id>.json`.
- **Provenance:** each entry carries `document_id` + `page_index`.
- **Consumption:** Stage 3 reads `needs_ocr` and `classification` to route each flagged page to the right extractor.
- **Deterministic.** No LLM. Synchronous per page, batched per document (~40–150s per large PDF per the reconnaissance timing).

### Stage 3 — Extracted evidence
- **Input:** page 373, classified `raster_embedded` (the AHU schedule is a raster image covering 36.9% of the page, per reconnaissance §2).
- **What happens:** render the page (`page.render(scale=2.0)`, already proven to produce crisp 6048×4320 output), run OCR (Tesseract or an equivalent deterministic OCR engine — **never an LLM**, per the architecture constraint) against the rendered image, producing word-level text + bounding boxes.
- **Output:** `ocr_cache/<document_id>/373.json` — `{words: [{text, bbox, confidence}], extractor: "tesseract-5.x", extractor_version, run_at}`.
- **Owner:** DIP.
- **Persistence:** evidence cache, immutable per `(document_id, page_index, extractor_version)` — a version bump creates a new cache entry, never overwrites.
- **Provenance:** every word carries its own bounding box; the cache entry carries the extractor identity and version.
- **Consumption:** Stage 4 reconstructs table structure from these word boxes.
- **Deterministic.** No LLM. Asynchronous batch job (OCR is the slow step).

### Stage 4 — Structured engineering state
- **Input:** the OCR word-box output for page 373.
- **What happens:** a heuristic column-reconstruction pass (word-box x-clustering into columns, y-clustering into rows — per reconnaissance's own recommendation: "OCR output... reconstructed into columns heuristically") turns the flat word list into typed schedule rows.
- **Output:** one `ScheduleRecord` per equipment tag: `ScheduleRecord{sheet="E0.4", new_designation="AHU-9C", existing_designation=..., fed_from_panel="MR6", circuit_number=..., breaker_rating=..., volts=..., hp=..., fla=..., mca=..., evidence_ref={document_id, page_index: 373, bbox: [...]}}`.
- **Owner:** DIP (internal working model — this type does not exist in RES's domain and is never persisted past this pipeline).
- **Persistence:** `structured_state/<document_id>.jsonl`, one row per record — a working cache, not a system of record.
- **Provenance:** carried per-record via `evidence_ref`.
- **Consumption:** Stage 5 diffs this against the prior revision's equivalent records for the same sheet.
- **Deterministic** (rule-based column reconstruction). No LLM.

### Stage 5 — Revision / detected engineering change
- **Input:** `ScheduleRecord{AHU-9C, fed_from_panel="MR6", ...}` (from Rev A's ingestion run) and `ScheduleRecord{AHU-9C, fed_from_panel="MR7", ...}` (from Rev B's ingestion run).
- **What happens:** a deterministic field-level diff, keyed by `new_designation` (the stable equipment tag), across two ingestion runs of the same sheet.
- **Output:** a `DetectedChange`: `{sheet="E0.4", prior_document_id, new_document_id, changed_rows: [{key: "AHU-9C", field: "fed_from_panel", before: "MR6", after: "MR7", evidence_before, evidence_after}], summary: "AHU-9C fed-from-panel changed from MR6 to MR7"}`.
- **Owner:** DIP (change-detection stage).
- **Persistence:** `detected_changes/<sheet>/<timestamp>.json` — an audit trail of every diff DIP ever ran, kept even for diffs that turn out not to be event-worthy.
- **Provenance:** carries both revisions' evidence refs.
- **Consumption:** Stage 6 (promotion) turns this into a real RES fact.
- **Deterministic.** No LLM. This is the literal "revision detected" moment, and it is intentionally boring — a field comparison, not a model inference, per the constraint that deterministic extraction stay deterministic.

### Stage 6 — Promotion into RES (the seam)
- **Input:** the `DetectedChange` from Stage 5.
- **What happens:** DIP, acting as an authenticated **RES integration client** (the same OAuth2 client-credential surface RES already built for `connector-procore` in RES-1 §10.3 — DIP is simply another integration client, not a privileged backdoor), calls RES's API to:
  1. `POST .../documents/{drawing_id}/versions` — create a new `DrawingVersion` in `DRAFT`, `revision_label="Rev B"`, with a `RevisionCloud{area: "E0.4 Panel Schedule — AHU-9C row", delta_number: N, description: "AHU-9C fed-from-panel changed from MR6 to MR7", source_evidence_ref: <pointer into DIP's evidence store>}` — **`source_evidence_ref` is a new, additive, nullable field on `RevisionCloud`**, following the exact precedent ADR-006 already set for `SubmittalRevision.fla_value`/`fla_unit` (additive, nullable, backward compatible).
  2. `PATCH .../versions/{id}/issue` — the **already-implemented** `IssueDrawingVersion` use case (RES-4B) fires: stamps `issuance_date`, supersedes the prior current version, repoints `Drawing.current_version_id`, and — because this use case already exists exactly for this purpose — emits RES's thin `documents/update` webhook.
- **Output:** a real, persisted `DrawingVersion` row inside RES, `ISSUED`, superseding Rev A. A `WebhookDelivery` row recording the dispatch attempt.
- **Owner:** RES (the record); DIP (the API caller).
- **Persistence:** RES's own Postgres (`0004`+ migrations, unchanged schema plus one additive column — see §12).
- **Provenance:** `RevisionCloud.source_evidence_ref` is the second hop back to the literal PDF page/bbox; RES's own `DrawingVersion.id` is the first hop any Downstream citation will actually use.
- **Consumption:** the next stage is not DIP's problem anymore — it's the existing, frozen webhook/connector mechanism.
- **Deterministic**, mechanical API call. No LLM. Synchronous HTTP call, made by an offline batch job (not user-request-driven).

### Stage 7 — RES webhook → Connector Layer
- **Input:** RES's `documents/update` thin webhook payload: `{resource_name: "documents", resource_id: <version_id>, project_id: <RES project id for DSH-Atascadero>, event_type: "update", timestamp}` — the exact five-key shape already built and tested for `rfis`/`submittals`/`design_changes` (RES-2/3/4).
- **What happens:** `connector-procore`'s inbound webhook receiver (`POST /connectors/procore/{project_id}`, per `docs/07` §7 — currently an empty scaffold, unbuilt) accepts it (`202 Accepted`), then makes the enrichment GET-back: `GET /rest/v1.0/projects/{id}/documents/versions/{version_id}` (an endpoint RES already added in RES-1 §10.6 for exactly this reason — "RFIs reference DrawingVersion IDs directly... but the originally-planned document endpoints only supported listing versions by drawing").
- **Output:** the full `EngineeringEventEnvelope`: `{source_system: "procore", source_id: <RES version id, standing in for Procore's opaque id>, display_number: "E0.4 Rev B", type: "DRAWING_REVISED", drawing_refs: [{item_id: <drawing id>, version_id: <version id>}], spec_section_refs: [], location_refs: [...], raw_document_ref: "res://projects/2/documents/versions/<id>", region, acting_credential_scope, occurred_at}`.
- **Owner:** Connector Layer (`connector-procore`).
- **Persistence:** none beyond the connector's own idempotency cache (`source_id` + `occurred_at`), per `docs/03` §1.
- **Provenance:** `raw_document_ref` is the pointer every later Evidence-Explorer click resolves; it points at RES's own record, which itself carries `source_evidence_ref` back to DIP's evidence — an unbroken two-hop chain from the Commercial Event all the way to the literal cited PDF page.
- **Consumption:** Ingestion & Normalization Service (Stage 2 of the frozen architecture, `docs/03` §2).
- **Deterministic** mapping (raw→envelope). No LLM. Asynchronous from here — this is the first hop onto the frozen, already-fully-specified pipeline.

**From here, nothing in this document adds anything.** `trigger.detected` → Key Resolution → Graph Layer → the five-stage Reasoning Pipeline → Commercial Event/Impact/Action → Approval → Synchronization → Ledger run exactly as `docs/03`, `docs/06`, and `docs/07` already specify, unmodified. The one place worth calling out: **Reasoning Pipeline stage 6a (Trigger Understanding)** can consume DIP's already-extracted, already-cited `ScheduleRecord` evidence directly (via `raw_document_ref` → RES → `source_evidence_ref` → DIP's structured state) rather than re-running vision-language extraction from a blank slate — a legitimate implementation optimization *within* 6a's existing contract ("structured fields... each with an extraction confidence," `docs/03` §6a), not a new stage and not a redesign of 6a's boundary.

---

## 3. Answers to the fourteen questions

**A. Where do raw PDFs live?**
`data/reference-projects/dsh-atascadero/raw/` (already exists, per the reconnaissance report — untouched, source of truth). Immutable, content-hashed. Never edited in place; a reissued sheet set is a *new* file, not an overwrite.

**B. Where do page manifests live?**
`data/reference-projects/dsh-atascadero/derived/page_manifest/<document_id>.json` — exactly the structure the reconnaissance report already proposed (§9 of that report). Owned by DIP, not RES, not Downstream.

**C. Where do OCR results live?**
`data/reference-projects/dsh-atascadero/derived/ocr_cache/<document_id>/<page>.json`. Same ownership. Never re-run silently — keyed by `extractor_version` so a pipeline upgrade doesn't invisibly invalidate prior citations still referenced by an issued RES `DrawingVersion`.

**D. Where does structured engineering evidence live?**
`data/reference-projects/dsh-atascadero/derived/structured_state/<document_id>.jsonl` while it's DIP-internal working state. Once *promoted* (Stage 6), the durable, citable copy of the fact lives in RES's own Postgres, not in DIP's cache — DIP's cache remains only as the second provenance hop, not as a second system of record.

**E. Where are previous/current document versions stored?**
Two different things, deliberately kept apart:
- **Raw PDF sets** (the whole reissued document): every version kept forever under `raw/`, one immutable file per version, never deleted.
- **The engineering record's current/previous pointer**: RES's own `Drawing.current_version_id` / `DrawingVersion.superseded_by_id` — already built, already the system of record for "which revision is current," per `docs/reference/The Reference Engineering System.md` §4/§7's issuance-date-driven supersession rule. DIP does not duplicate this pointer anywhere.

**F. Where are detected changes represented?**
Two places, by design, not one: DIP's own `detected_changes/` audit log (every diff DIP ever computed, including ones judged not event-worthy — this is DIP's own working history) **and**, only for changes DIP decides to promote, as a real `RevisionCloud` on a real, issued RES `DrawingVersion`. The frozen Downstream `Trigger` (`docs/03` §2) is *not* where a detected change is "represented" — it's where a promoted, enveloped change is normalized into a candidate for reasoning. Conflating DIP's internal diff log with the Trigger would violate the event-worthiness filter's whole reason for existing (`docs/03` §2: "a drawing revision that only fixes a typo should never become a Commercial Event").

**G. How does a detected drawing revision become an `EngineeringEventEnvelope`?**
Exactly via Stage 6→7 above: DIP promotes the change into a real, issued RES `DrawingVersion` (mechanical API call, not a new envelope-construction path); RES's existing webhook + `connector-procore`'s existing (unbuilt but fully specified) mapper does the rest, identically to how a real Procore drawing revision would.

**H. Who creates the Trigger?**
Unchanged from the frozen design: the Ingestion & Normalization Service (`apps/ingestion-service`), consuming the `EngineeringEventEnvelope` `connector-procore` publishes. DIP never creates a Trigger, never touches `apps/*`, never touches `packages/*`.

**I. How does the Trigger reach the existing event bus?**
Unchanged: Ingestion & Normalization Service persists the `Trigger` row and emits `trigger.detected` on the Event Bus, per `docs/03` §2–§3. Nothing about DSH-Atascadero changes this mechanism.

**J. How does reasoning consume the Trigger?**
Unchanged: Key Resolution consumes `trigger.detected`, resolves keys against the Graph Layer (which must be seeded for the DSH-Atascadero project exactly as Meridian Tower's graph was seeded, per `docs/06` backlog item 2 — a new, separate seeding exercise, not a new mechanism), emits `keys.resolved`; the Reasoning Pipeline consumes it from there. Zero change to this stage's contract.

**K. How does reasoning retrieve the underlying evidence?**
Two-hop, both real, both already-typed fields: `Trigger.raw_document_ref` / `EngineeringEventEnvelope.raw_document_ref` → resolves to RES's own `DrawingVersion` record (`res://projects/2/documents/versions/<id>`) → RES's `RevisionCloud.source_evidence_ref` (new field, §6 above) → resolves to DIP's evidence store, which can render the literal PDF page. Reasoning Pipeline stage 6a can either re-run vision-language extraction fresh from `raw_document_ref`, or — as an implementation optimization inside 6a's existing contract — read DIP's already-extracted, already-cited `ScheduleRecord` directly, attaching DIP's own confidence score as 6a's "extraction confidence."

**L. How is evidence/provenance preserved all the way to the final Action?**
The chain never breaks because every stage's existing, frozen contract already has a place for it: `Impact.evidence_refs[]` (frozen, `docs/03` §7) carries forward whatever `raw_document_ref` the Trigger carried; 6e's Grounded Drafting is contractually forbidden from writing a sentence it can't cite back to that same evidence (`docs/03` §6e). This document adds nothing to that mechanism — it only makes sure DIP's evidence *is* something worth citing, by construction (every `ScheduleRecord` carries `evidence_ref`; every promoted `RevisionCloud` carries `source_evidence_ref`).

**M. How does this work for PDFs today but Procore/ACC tomorrow?**
This is the central architectural payoff. RES already exists specifically to "play the role of the external system (Procore/ACC-shaped) that a future `connector-procore` will connect into" (`IMPLEMENTATION_STATUS.md` §10.1). DIP's entire job is to populate RES the way a real GC's document-control team would populate real Procore. **The day a real Procore tenant exists for a real customer, DIP is deleted or repointed at nothing, `connector-procore` is repointed at the real Procore API instead of RES's, and *zero lines change* anywhere from the Connector Layer downward** — the exact "swap the mock for real Procore is a configuration change, not a rewrite" guarantee `docs/04` and RES's own §10.1 are built around. This is precisely why DIP must never be allowed to construct an `EngineeringEventEnvelope` directly (a temptation to "save a step") — doing so would create a second, competing envelope-construction path that the real-Procore swap would then have to unwind.

**N. How can the exact same downstream pipeline run against a synthetic/demo source?**
Trivially — it already does, today, via `meridian_tower.py`. DIP and the hand-written seed script are **two interchangeable producers into the same RES API surface**. Nothing downstream of RES can tell which one populated a given project. This is also the answer to "is a real evidence-backed Scenario B feasible" from the reconnaissance report's own closing question — DSH-Atascadero becomes RES project #2, Meridian Tower stays project #1, both isolated by RES's already-built, already-tested project-isolation guards (RES-4F).

---

## 4. Constraint checklist — how this design honors every stated constraint

| Constraint | How satisfied |
|---|---|
| Preserve existing service boundaries | DIP is not a Downstream service; the Connector Layer boundary is untouched; RES's own layering is untouched |
| Do not couple RES directly to Downstream | DIP→RES is the only new coupling, and it mirrors the existing seed-script relationship exactly; RES still has zero dependency on `packages/*` |
| Do not couple Downstream to `packages/*`... to `packages/*` | N/A — reworded: Downstream's `apps/*`/`packages/*` are untouched by this entire design |
| No vector database (unless justified) | Not introduced. Table reconstruction is heuristic column-clustering, not embedding search; 6a's narrow, targeted retrieval (already scoped as deferred-general/built-narrow in `docs/06` item 7) needs no vector index for this scope |
| No bulk LLM summarization | Not introduced. Every DIP stage (1–6) is deterministic. LLM involvement is unchanged from frozen scope: only 6e (drafting), optionally 6a (extraction confidence) |
| OCR is not an LLM task | Stage 3 is Tesseract-class deterministic OCR, explicitly, per the reconnaissance report's own recommendation |
| Deterministic extraction stays deterministic | Stages 1–6 are 100% deterministic; Stage 5's diff is a field comparison, not an inference |
| Every extracted fact preserves provenance | `evidence_ref` on every `ScheduleRecord`; `source_evidence_ref` on every promoted `RevisionCloud`; `raw_document_ref` on every envelope/Trigger — an unbroken chain |
| Every event traceable to evidence | Same chain, terminating at `Impact.evidence_refs[]`, unchanged frozen mechanism |
| Every reasoning result traceable to evidence | 6e's existing retrieval-grounded constraint, unchanged |
| Raw source documents immutable | `raw/` is write-once, content-hashed, never edited in place |
| Duplicate ingestion is idempotent | See §7 (Idempotency strategy) below |
| Document revisions distinguishable | RES's `revision_label`/`issuance_date`/`superseded_by_id`, unchanged frozen mechanism, reused not reinvented |
| Project isolation enforced | DSH-Atascadero is RES project #2, under RES's already-built, already-tested (RES-4F) isolation guards |

---

## 5. ASCII architecture diagram

```
 ┌─────────────────────────────────────────────────────────────────────────┐
 │  DOCUMENT INGESTION PIPELINE (DIP) — new, offline, batch, deterministic  │
 │  reference-systems/document-ingestion-pipeline/  (proposed location)    │
 │                                                                           │
 │   raw PDFs            page manifest         OCR cache                   │
 │   data/.../raw/  ──►  derived/page_    ──►  derived/ocr_cache/          │
 │   (immutable,         manifest/             (per document,page,        │
 │    content-hashed)    (classification,       extractor_version)         │
 │                        needs_ocr)                  │                    │
 │                                                     ▼                    │
 │                                          structured_state/               │
 │                                          (ScheduleRecord + evidence_ref) │
 │                                                     │                    │
 │                                                     ▼                    │
 │                                          detected_changes/               │
 │                                          (deterministic field diff       │
 │                                           between two ingestion runs)    │
 │                                                     │                    │
 │                                    Stage 6: promotion (OAuth2 client)    │
 └─────────────────────────────────────────────────────┼────────────────────┘
                                                         │ POST/PATCH
                                                         ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │  REFERENCE ENGINEERING SYSTEM (RES) — existing, frozen, already built    │
 │  reference-systems/reference-engineering-system/                        │
 │                                                                           │
 │   Project #1: Meridian Tower  (existing, untouched)                     │
 │   Project #2: DSH-Atascadero  (new project row, same schema)            │
 │      Drawing "E0.4" → DrawingVersion Rev A ─SUPERSEDED─► Rev B (ISSUED)  │
 │                          RevisionCloud{..., source_evidence_ref} ◄───────┼── new, additive field
 │                                                     │                    │
 │                                        thin webhook (documents/update)  │
 └─────────────────────────────────────────────────────┼────────────────────┘
                                                         │ POST /connectors/procore/{project_id}
                                                         ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │  CONNECTOR LAYER — existing, frozen, currently an empty scaffold         │
 │  apps/connector-procore/                                                 │
 │   inbound webhook receiver → enrichment GET-back → EngineeringEventEnvelope │
 └─────────────────────────────────────────────────────┼────────────────────┘
                                                         │ trigger.detected candidate
                                                         ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │  EVERYTHING BELOW THIS LINE IS ALREADY FULLY SPECIFIED — SEE docs/03,06,07│
 │                                                                           │
 │  Ingestion&Normalization → Event Bus → Key Resolution → Graph Layer     │
 │  → Reasoning Pipeline (5a-5e) → Commercial Event Service → Ledger       │
 │  → Realtime Gateway / Approval Service → Synchronization Service        │
 └───────────────────────────────────────────────────────────────────────┘
```

---

## 6. Concrete end-to-end data-flow example

See §2 above (full stage-by-stage walkthrough using `E0.4`, `AHU-9C`, `MR6`→`MR7`). Not repeated here to avoid two disagreeing copies of the same example in one document.

---

## 7. Object ownership table

See §1 above.

---

## 8. Data-contract table

| Contract | Shape | Owner | Status |
|---|---|---|---|
| `Document` | `{document_id (sha256), filename, page_count, producer, project_ref}` | DIP | New |
| `PageManifestEntry` | `{page_index, char_len, image_coverage_pct, path_object_count, classification, needs_ocr, bookmark_title}` | DIP | New |
| `OcrCacheEntry` | `{words: [{text, bbox, confidence}], extractor, extractor_version, run_at}` | DIP | New |
| `ScheduleRecord` | `{sheet, new_designation, existing_designation, fed_from_panel, circuit_number, breaker_rating, volts, hp, fla, mca, evidence_ref}` | DIP | New (sheet-family-specific; each schedule family — AHU, panel, one-line — gets its own typed record, not one generic blob) |
| `DetectedChange` | `{sheet, prior_document_id, new_document_id, changed_rows[], summary}` | DIP | New |
| `RevisionCloud.source_evidence_ref` | `str \| None` — pointer into DIP's evidence store | RES (additive field) | New, additive |
| `DrawingVersion`, `Drawing`, `DesignChange` | unchanged | RES | Frozen, existing |
| `EngineeringEventEnvelope`, `DrawingRef` | unchanged | `packages/envelope-schemas` | Frozen, existing |
| `Trigger`, `CommercialEvent`, `Impact`, `Action` | unchanged | `packages/domain-models` | Frozen, existing |
| Ten Event Bus topics | unchanged | `packages/event-contracts` | Frozen, existing |

---

## 9. Storage strategy

| Store | Location | Shape | Mutability |
|---|---|---|---|
| Raw PDFs | `data/reference-projects/dsh-atascadero/raw/` | file blobs | immutable, content-hashed |
| Page manifest | `.../derived/page_manifest/` | JSON, one file per document | append/overwrite whole file per re-ingestion, never partial mutation |
| OCR cache | `.../derived/ocr_cache/` | JSON, one file per (document, page) | immutable per `(document_id, page_index, extractor_version)` |
| Structured state | `.../derived/structured_state/` | JSONL | working cache, rebuildable from OCR cache at any time |
| Detected changes | `.../derived/detected_changes/` | JSON, one per diff run | append-only audit log, never deleted |
| RES's own DB | RES's existing Postgres | unchanged schema + 1 additive column | RES's own existing durability guarantees apply |
| Everything from Trigger downward | unchanged frozen stores (`docs/03`'s storage boundaries table) | unchanged | unchanged |

No vector database. No new relational database beyond RES's existing one (DIP's own state is files, not a database, at this data scale — the largest file is 294MB and the whole corpus is four files; a database is not justified yet, matching the "don't introduce infrastructure ahead of evidence" discipline `docs/06` already models).

---

## 10. Provenance strategy

A single unbroken chain, four hops, each already a real field in an already-frozen or newly-additive contract:

```
Impact.evidence_refs[]
   └── Trigger.raw_document_ref / EngineeringEventEnvelope.raw_document_ref   (frozen field, already exists)
          └── res://projects/{id}/documents/versions/{id}                      (RES's own record)
                 └── RevisionCloud.source_evidence_ref                          (new, additive field)
                        └── DIP evidence store: {document_id, page_index, bbox} (new, DIP-owned)
                               └── the literal rendered PDF page, on demand
```

Nothing in this chain is a copy of the document (per `docs/03`'s storage-boundaries table: "Evidence must open to the actual document... cached copies exist for latency, never as the source of truth"). DIP's rendered-page cache exists purely as a rendering-latency optimization for the Evidence Explorer; the `raw/` PDF remains the one source of truth, exactly matching the existing architectural rule for the Connector Layer's own document cache.

---

## 11. Idempotency strategy

- **Document-level:** `document_id = sha256(bytes)`. Re-running DIP on an unchanged file is a no-op — the manifest/OCR/structured-state stages all check for an existing, matching `extractor_version` entry before recomputing.
- **Extraction-level:** cache keyed by `(document_id, page_index, extractor_version)`. Bumping the OCR engine or the column-reconstruction heuristic bumps `extractor_version`, producing a new cache entry rather than silently overwriting a prior one an issued `RevisionCloud` may still cite.
- **Promotion-level (Stage 6):** before `POST`-ing a new `DrawingVersion`, DIP checks RES for an existing version of the same `Drawing` whose `RevisionCloud.description` + `source_evidence_ref` already match this `DetectedChange` — a duplicate promotion attempt (e.g., DIP re-run after a partial failure) is a no-op, not a duplicate `DrawingVersion`. This mirrors the Connector Layer's own idempotency cache pattern (`source_id` + `occurred_at`) one layer upstream, applied to DIP→RES instead of connector→ingestion.
- **RES→Connector-→Ingestion:** entirely unchanged, already-specified idempotency (`docs/03` §1's connector idempotency cache, keyed on `source_id`+`occurred_at`).

---

## 12. Version/revision strategy

- **Document (file) versions:** every reissued PDF set is a new immutable file under `raw/`; never overwritten. `Document.document_id` changes; the human-facing filename convention (`Bldg_3319`) stays stable, distinguishing "same drawing set, new issuance" from "different drawing set" the same way RES already distinguishes `revision_label` from `sheet_number`.
- **Engineering (drawing) revisions:** owned entirely by RES's existing `DrawingVersion`/`superseded_by_id` mechanism — unchanged, reused, not reinvented. DIP never invents its own competing revision-numbering scheme; it always resolves "what's the current version of sheet X" by asking RES, immediately before deciding whether a new `DetectedChange` represents a genuine new revision or a re-ingestion of an already-promoted one.
- **Extraction-pipeline versions:** `extractor_version` (OCR engine version + column-heuristic version, concatenated) — bumping it never silently invalidates a citation already embedded in an issued RES record; it only affects future extraction runs.

---

## 13. Error/retry strategy

| Failure mode | Handling |
|---|---|
| PDF fails to open / corrupt | Logged, that document skipped, does not block other documents in the corpus |
| A page's OCR produces low-confidence output | `ScheduleRecord` carries the OCR engine's own confidence; low-confidence records are still promoted with that confidence attached (never silently dropped) — mirrors 6c's "never round Probable up to Certain" discipline, applied one layer earlier |
| Column-reconstruction heuristic fails to parse a table | Page flagged `needs_manual_review` in the page manifest; no `ScheduleRecord` emitted for that page; a human-inspection queue (the reconnaissance report's own "pages requiring human inspection" list is the template) surfaces it — **never** silently fabricated |
| Stage 6 promotion call to RES fails (network, RES down) | Retried with backoff (DIP's own batch-job retry, not the Synchronization Service's — this is upstream of the Connector Layer and has no bearing on the frozen retry semantics defined for Stage 10) — DIP is not "in flight" in the way an approved Action's dispatch is; a failed promotion simply means that revision isn't visible to RES/Downstream yet, safely retryable from `detected_changes/`'s durable log |
| Duplicate promotion (retry lands twice) | Prevented by the idempotency check in §11 |
| RES's own webhook dispatch fails (no receiver) | Already-existing, already-tested RES behavior: `WebhookDelivery` recorded `FAILED`, the underlying state transition (`ISSUED`) is never rolled back (RES-2 §11.5's own established pattern) — unchanged |
| Everything from Connector Layer downward | Unchanged frozen retry/idempotency/failure semantics per `docs/03`'s "Consistency, idempotency, and failure" section |

---

## 14. Phase-by-phase implementation roadmap

### PHASE A — Document ingestion foundation
**Responsibility:** open PDFs, build page manifests, classify every page.
**Components:** new `reference-systems/document-ingestion-pipeline/` — `pypdfium2`-based, single Python package, no service, no API, run as a CLI/batch job.
**Data contracts:** `Document`, `PageManifestEntry` (§8).
**Storage:** `raw/`, `derived/page_manifest/`.
**Tests:** manifest correctness against the reconnaissance report's own already-confirmed findings (431 bookmarks / 425 pages for doc02, etc.) — a golden-file regression test.
**Demo value:** none standalone — foundational only.
**Dependencies:** none beyond `pypdfium2`/`Pillow` (already available, per reconnaissance §9).
**Must NOT implement yet:** OCR, table reconstruction, any RES write.

### PHASE B — Evidence extraction
**Responsibility:** render flagged pages, run OCR, produce word-box evidence.
**Components:** same DIP package, `extract/` module.
**Data contracts:** `OcrCacheEntry`.
**Storage:** `derived/ocr_cache/`.
**Tests:** OCR accuracy prototype on the 2–3 pages the reconnaissance report already named (E0.4, E0.6, EE5.1) — this is the "biggest unresolved technical risk" the reconnaissance flagged and must be validated before committing further.
**Demo value:** a human can visually confirm OCR text against the rendered page — low, but de-risks everything after it.
**Dependencies:** Phase A; a chosen OCR engine (Tesseract vs. a pure-pip alternative — open decision, §16).
**Must NOT implement yet:** column reconstruction, promotion to RES.

### PHASE C — Engineering state/versioning
**Responsibility:** reconstruct typed schedule rows from OCR output.
**Components:** DIP `structure/` module — one typed reconstructor per schedule family (AHU schedule, panel schedule, one-line-diagram equipment list).
**Data contracts:** `ScheduleRecord` (per-family variants).
**Storage:** `derived/structured_state/`.
**Tests:** row-count/field-accuracy assertions against the 13-of-60 rows already hand-verified in the reconnaissance report (a real, existing ground truth).
**Demo value:** a human can read a real, structured JSON table where before there was only a raster image — meaningful, standalone demo value.
**Dependencies:** Phase B.
**Must NOT implement yet:** diffing across revisions, any RES contact.

### PHASE D — Change detection
**Responsibility:** deterministic diff between two ingestion runs of the same sheet.
**Components:** DIP `diff/` module.
**Data contracts:** `DetectedChange`.
**Storage:** `derived/detected_changes/`.
**Tests:** synthetic two-revision fixture (hand-authored Rev A/Rev B JSON, not requiring a second real PDF set yet) proving the diff logic in isolation.
**Demo value:** "here is the exact field that changed, with both citations side by side" — high demo value, still fully offline.
**Dependencies:** Phase C.
**Must NOT implement yet:** any write to RES.

### PHASE E — EngineeringEventEnvelope adapter (the promotion seam + RES extension)
**Responsibility:** (1) add RES's missing creation endpoints (`POST .../documents`, `POST .../documents/{id}/versions`, `POST .../design_changes`, and a way to create a second RES project) — these do not exist yet; RES currently only *creates* records via its own seed script, never via API; (2) add the additive `RevisionCloud.source_evidence_ref` field (ADR-006-style migration); (3) build DIP's Stage 6 promotion client.
**Components:** RES backend (`application/use_cases/`, one new migration, new API routes, new OAuth2 integration-client scope for DIP); DIP `promote/` module.
**Data contracts:** the new RES creation-endpoint request/response shapes; `RevisionCloud.source_evidence_ref`.
**Database changes:** one RES migration (additive column on `design_change_drawing_versions`/wherever `RevisionCloud` is persisted — needs the exact ORM location confirmed during implementation); no Downstream DB changes.
**Tests:** RES contract tests for the new creation endpoints (mirroring the existing `tests/contract/test_design_changes_api.py` pattern exactly); DIP promotion idempotency tests (§11).
**Demo value:** a real second project inside RES's own frontend, showing a real DSH-Atascadero drawing register — meaningful, fully within already-proven RES UI.
**Dependencies:** Phases A–D; requires an explicit ADR (a genuinely new RES capability — "creation via API," not just "another field") before implementation, per RES's own ADR discipline.
**Must NOT implement yet:** `connector-procore` itself; anything in `apps/*`.

### PHASE F — Downstream Milestone 1 (unchanged scope, now unblocked)
**Responsibility:** build `apps/connector-procore` and `apps/ingestion-service` exactly as `docs/06` backlog items 4–5 and `docs/07` §9 Milestone 1 already specify — **zero DSH-specific logic inside either service.**
**Components:** `apps/connector-procore/src/{inbound,client,mapper,idempotency,config}`, `apps/ingestion-service/src/{domain,consumers,publishers,repository,config}`.
**Data contracts:** unchanged — `EngineeringEventEnvelope`, `Trigger`.
**Database changes:** `triggers` table (per `docs/07` §6), connector idempotency cache.
**Tests:** contract tests run against RES directly (RES already plays the mock's role, per `IMPLEMENTATION_STATUS.md` §10.1) — no separate mock needed for this connector.
**Demo value:** first real, persisted `Trigger` row sourced from a real construction PDF, on the bus.
**Dependencies:** Phase E; Milestone 0 (artifact identity map, event bus topics — per `docs/07` §9, not yet started for Downstream's own `apps/*`).
**Must NOT implement yet:** anything past `trigger.detected`.

### PHASE G — Reasoning integration
**Responsibility:** Key Resolution + Graph Layer seeded for the DSH-Atascadero project (new seed data — the E0.4/E0.6/E0.7/EE5.1 corridor already evidence-traced in the reconnaissance report §8 is the literal graph to seed); Reasoning Pipeline's five sub-stages.
**Components:** `apps/key-resolution-service`, `apps/reasoning-pipeline`.
**Data contracts:** unchanged (`keys.resolved`, `event.created`, etc.).
**Database changes:** Graph DB seed for the new project.
**Tests:** unchanged pipeline contract, new fixture data.
**Demo value:** high — first tiered/severity-scored, evidence-cited output on real construction documents.
**Dependencies:** Phase F; Milestone 2 scope per `docs/07` §9.
**Must NOT implement yet:** Commercial Event persistence.

### PHASE H — Commercial impact
**Responsibility:** Commercial Event Service, exactly per `docs/06` backlog item 8 — **requires a Commercial Artifact source for DSH-Atascadero** (a PO/vendor/delivery equivalent of Meridian Tower's SAP-shaped mock) which does not yet exist for this project and is explicitly out of this document's scope (Reference Commercial System territory).
**Must NOT implement yet:** anything beyond what a stubbed/seeded artifact snapshot allows — full commercial fidelity for DSH-Atascadero depends on work this document does not cover.

### PHASE I — Approval/action
**Responsibility:** unchanged frozen scope (`docs/06` item 12) — Approval Service, three frontend surfaces.
**Must NOT implement yet:** anything beyond Milestone 4 scope.

### PHASE J — End-to-end demo
**Responsibility:** run the full loop — DIP ingests a real DSH-Atascadero revision → RES → connector-procore → Trigger → Reasoning → Commercial Event → Approval → Synchronization → Ledger — once, completely, on real evidence.
**Demo value:** this is the actual point of the whole exercise — replaces Meridian Tower's fictional trace with a real, evidence-backed one for at least one corridor.
**Dependencies:** everything above, in order.

---

## 15. First vertical-slice implementation plan

**Scope, exactly:** DSH-Atascadero, sheet `E0.4`, the AHU→panel relationship (`AHU-9C → MR6/MR7` or a real pair once a genuine second revision of E0.4 is located — see open decision in §16). Nothing else — no other sheet, no EE5.1 switchgear corridor yet, no second project graph edge beyond this one.

**Steps, strictly in order (per Phases A–E above, scoped to one sheet):**
1. Ingest `02_Main_Plans_Bldg_3319.pdf` through Phase A (manifest) and Phase B (OCR, page 373 only) — validate against the reconnaissance report's own already-read table (§6 of that report: full column list, real values).
2. Build the `ScheduleRecord` reconstructor for exactly the AHU-schedule family (Phase C), validated against the 13 already-hand-verified rows.
3. Author (not extract — no second real revision confirmed yet) a synthetic `Rev B` fixture representing one plausible real-world change (a panel reassignment), to prove the diff mechanism (Phase D) without waiting on locating a genuine second E0.4 revision in the corpus.
4. Implement the RES creation-endpoint extension (Phase E) scoped to `documents`/`documents/{id}/versions` only — defer `design_changes` creation (not needed for a bare drawing-revision demo) and defer new-project creation by adding DSH-Atascadero as project #2 via a one-time seed script extension (mirroring `meridian_tower.py`, not yet via API — API-based project creation can wait for a later phase).
5. Promote the one `DetectedChange` into a real, issued RES `DrawingVersion` for `E0.4`; confirm the webhook fires (reusing RES's already-tested webhook-delivery mechanism as-is).
6. **Stop here for this slice.** Do not build `connector-procore` yet within this slice — confirming RES correctly holds and serves a real, evidence-linked drawing revision from a real PDF is itself a complete, demonstrable milestone (a human can open RES's own Drawing Detail page, per RES-2's already-built Revision Timeline UI, §11.7, and see the real citation).

**Explicit non-goals of the vertical slice:** `connector-procore`, `apps/ingestion-service`, the Graph Layer, the Reasoning Pipeline, and Commercial Event Service are all out of scope for this slice — they are Phase F onward, already fully specified, and adding them here would be exactly the "building ahead of the milestone that calls for it" risk `docs/07`'s own recommendations warn against.

---

## 16. Exact files/services likely to change

**New, created by this work:**
- `reference-systems/document-ingestion-pipeline/` — new sibling directory (manifest, OCR, structure, diff, promote modules; own `pyproject.toml`, own tests — zero dependency on `packages/*`, matching RES's own §10.1 precedent)
- `docs/adr/ADR-008.md` (proposed number) — "RES gains creation endpoints; DSH-Atascadero is RES project #2"
- `docs/adr/ADR-009.md` (proposed number) — "`RevisionCloud.source_evidence_ref` additive field"

**Existing RES files touched:**
- `reference-systems/reference-engineering-system/backend/src/domain/value_objects/revision_cloud.py` — add `source_evidence_ref: str | None = None`
- `reference-systems/reference-engineering-system/backend/src/application/use_cases/drawing_use_cases.py` — add `CreateDrawing`, `CreateDrawingVersion` use cases
- `reference-systems/reference-engineering-system/backend/src/api/v1/documents.py` (or equivalent) — new `POST` routes
- `reference-systems/reference-engineering-system/backend/migrations/00XX_revision_cloud_evidence_ref.py` — new migration
- `reference-systems/reference-engineering-system/backend/src/seed/` — new `dsh_atascadero.py` seed module (project #2 skeleton: org, disciplines M/E, locations, spec sections `23 74 13`/`26 24 13`, matching what the reconnaissance report already confirmed exists in the real spec book)
- `reference-systems/reference-engineering-system/backend/tests/contract/` — new contract tests for the creation endpoints

**Untouched (confirmed, not by omission):**
- `packages/*` — zero changes
- `apps/*` — zero changes until Phase F
- `docs/01`–`07` — zero changes, per the mission's own "architecture is frozen" rule
- `infra/docker-compose.yml` — DIP is a batch job, not a long-running service; no new Compose entry needed unless it's later containerized for scheduling (open decision, §16 below)

---

## 17. Risks and unresolved decisions

1. **OCR accuracy on dense, small-font schedule tables is genuinely unvalidated.** The reconnaissance report calls this "the biggest unresolved technical risk before committing to a pipeline design." Phase B's 2–3-page prototype must run and be measured before Phase C is built for real, not assumed.
2. **No genuine second revision of `E0.4` has been located yet.** Addendum 1 does not touch it (reconnaissance §6). The vertical slice therefore either (a) uses a synthetic Rev B fixture to prove the mechanism, deferring "real revision" to whenever one is found in a fuller document set, or (b) the corpus needs to be expanded/re-reconnoitered for a genuine E0.4 revision before the demo can be evidence-backed end-to-end rather than partially synthetic. **This is a decision for you, not this document.**
3. **Tesseract vs. a pure-pip OCR engine** — a real, flagged tradeoff (system-level binary dependency and Windows friction vs. a heavier, less battle-tested pip package) that the reconnaissance report explicitly left open pending a prototype comparison.
4. **RES's creation-endpoint extension is a genuinely new RES capability**, not a pure translation of an existing frozen document — RES has never had a public "create" surface before (only seed-script creation). This needs its own ADR and explicit sign-off before Phase E starts, following RES's own established discipline (ADR-001 through ADR-007).
5. **Whether DIP should be containerized/scheduled** (a Compose entry, a cron-style batch job, or simply a manually-invoked CLI for now) is not decided — given the corpus is four static files today, a manual CLI is almost certainly sufficient until a real, continuously-updating document source exists, but this is worth confirming rather than assuming.
6. **Column-reconstruction heuristics are schedule-family-specific** (AHU schedule ≠ panel schedule ≠ one-line diagram equipment list) — Phase C's scope is larger than one reconstructor; the roadmap above only commits to the AHU-schedule family for the vertical slice, and each additional family is real, additional work, not free generalization.
7. **DSH-Atascadero's Graph Layer seed (Phase G)** requires deciding how much of the reconnaissance report's already-traced evidence corridor (E0.4 → E0.6/E0.7 → EE5.1, "LIKELY — needs manual sheet review" for the MRDP identity link) gets manually confirmed vs. left as a lower-confidence graph edge — this is a real data-quality decision, not an architecture one, but it gates Phase G's start.
8. **Whether `design_changes` creation (vs. only `documents`) is needed for the vertical slice** — deferred in §15 step 4 above; revisit once a real DSH-Atascadero authorization instrument (an ASI/CCD/addendum) is identified as the trigger for a specific promoted revision, rather than assuming every drawing revision needs one (RES-4's own ADR-007 already establishes that not every `DrawingVersion` issuance requires a `DesignChange`).

---

## ARCHITECTURE READY: NO

Not because anything above is unresolved architecturally — the fit into the frozen 14-stage pipeline is clean, minimal, and requires no redesign anywhere in `/docs`. It is "NO" because five concrete decisions in §17 are yours to make, not this document's, before a single line of implementation code should be written:

1. Confirm the **DIP → RES-as-second-project design** itself (§0, §2 Stage 6) — the core architectural choice this document is proposing — is the one you want, versus any alternative you may be holding that this document doesn't know about.
2. Pick an **OCR engine** (Tesseract vs. pure-pip) after the Phase B prototype, not before.
3. Decide the **vertical slice's revision source**: synthetic Rev B fixture now, or wait for a real second revision to be located in the corpus (§17.2).
4. Approve the **new RES capability** (creation-via-API) as worth its own ADR before Phase E starts.
5. Confirm **scope of the vertical slice** in §15 (one sheet, one family, no connector yet) matches what you want demoed first — versus, for example, wanting the switchgear/EE5.1 corridor instead, which the reconnaissance report flagged as needing more manual sheet review before it's as evidence-solid as E0.4/E0.6/E0.7 already are.
