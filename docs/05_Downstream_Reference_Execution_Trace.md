# Downstream — Reference Execution Trace
### CTO walkthrough · one complete scenario, every step, exactly as the running system executes it

**Scenario:** Meridian Tower (Downstream `project_id: proj_8841`). An engineer answers RFI-214 in Procore, rerouting a duct at grid B-4. Three purchase orders and one schedule activity are affected. A procurement manager, Ananya Rao (`user_2209`), reviews and approves three corrective actions individually. The event closes. Nothing below is summarized — every payload shown is the literal shape that stage produces.

---

## PHASE 0 — The trigger, in Procore

Ananya's colleague, the site engineer, submits the official response to RFI-214 inside Procore and marks it Closed. Procore's own object model updates: `rfis` resource `id: 4821356` (opaque, Procore-internal), `display_number: "RFI-214"` (the editable, human-facing label — never used as a key downstream of the connector, per the connector validation).

Procore's webhook service — deliberately thin, per its documented behavior — fires:

```
POST https://hooks.downstream.build/connectors/procore/proj_8841
Content-Type: application/json
X-Procore-Signature: sha256=7f2a9c...

{
  "resource_name": "rfis",
  "resource_id": 4821356,
  "company_id": 4471002,
  "project_id": 884199,
  "event_type": "update",
  "timestamp": "2026-07-28T09:14:03Z"
}
```

That is the entire payload. No status, no response text, no drawing reference. This is exactly the thin-event behavior validated earlier — the connector now must call back.

---

## PHASE 1 — Connector Layer: the callback and envelope construction

**1.1 — Idempotency check.** The Procore adapter first checks its short-lived cache for `(resource_id: 4821356, event_type: update, timestamp: 2026-07-28T09:14:03Z)`. Not seen before — proceeds. (Had Procore redelivered this webhook, as at-least-once delivery permits, the adapter would stop here.)

**1.2 — The enrichment GET-back**, using the stored OAuth2 bearer token for the provisioned integration user:

```
GET https://api.procore.com/rest/v1.0/projects/884199/rfis/4821356
Authorization: Bearer 9a3f...c81
```

Response (abbreviated to the fields the adapter actually reads):

```json
{
  "id": 4821356,
  "number": "214",
  "display_number": "RFI-214",
  "status": "closed",
  "subject": "Duct routing conflict at Grid B-4 vs. structural beam",
  "response": "Reroute duct per attached SK-14. Duct now runs south of beam, see revised Spec 23 31 13 clause 2.3 and Drawing M-2.1 Rev C.",
  "drawing_references": ["M-2.1"],
  "spec_section_references": ["23 31 13"],
  "location": "Level 4, Grid B-4",
  "closed_at": "2026-07-28T09:14:03Z",
  "attachments": [
    { "id": 991211, "name": "SK-14_reroute.pdf", "url": "https://api.procore.com/rest/v1.0/attachments/991211" }
  ]
}
```

The adapter also checks the **acting credential's permission scope** (recorded at connection time) — this integration user is scoped to RFIs, Submittals, and Documents on this project. It has **no Commitments/Budget scope on this Procore connection** (the customer's commercial system of record is a separate SAP tenant, connected independently — see Phase 9). This matters immediately: `acting_credential_scope` will be recorded as `partial: ["rfis","submittals","documents"]`, not `full`.

**1.3 — Envelope construction.** The adapter builds the canonical envelope — this is the only place a raw Procore payload is ever touched:

```json
{
  "envelope_type": "EngineeringEventEnvelope",
  "source_system": "procore",
  "source_id": "4821356",
  "display_number": "RFI-214",
  "type": "RFI_APPROVED",
  "spec_section_refs": ["23 31 13"],
  "drawing_refs": [{ "item_id": "doc_M-2.1", "version_id": "rev_C" }],
  "location_refs": ["Level 4, Grid B-4"],
  "raw_document_ref": "procore://attachments/991211",
  "region": "us-east",
  "acting_credential_scope": "partial:[rfis,submittals,documents]",
  "occurred_at": "2026-07-28T09:14:03Z"
}
```

Note the `drawing_refs` shape — `item_id` and `version_id` kept distinct, per the connector validation, so the Reasoning Pipeline can later diff Rev B against Rev C rather than treating "M-2.1" as one opaque blob.

---

## PHASE 2 — Ingestion & Normalization Service

**2.1 — Dedup/validate.** The envelope's `(source_system, source_id, occurred_at)` triple is checked against the ingestion idempotency store — new. Shape-validated against the envelope schema — passes.

**2.2 — Event-worthiness filter.** A lightweight rule pass checks: does this envelope carry spec/drawing references at all? Yes (`23 31 13`, `M-2.1`). Proceeds to the expensive pipeline. (Had this been a typo-fix ASI with no spec/drawing reference, it would stop here, logged but never becoming a Trigger.)

**2.3 — Trigger object persisted** (first durable write in the system):

```sql
INSERT INTO triggers (
  trigger_id, project_id, type, source_envelope_ref,
  spec_section_refs, drawing_refs, location_refs,
  raw_document_ref, occurred_at, status
) VALUES (
  'trg_2f9a1c', 'proj_8841', 'RFI_APPROVED', 'env_9a41bb',
  '["23 31 13"]', '[{"item_id":"doc_M-2.1","version_id":"rev_C"}]', '["Level 4, Grid B-4"]',
  'procore://attachments/991211', '2026-07-28T09:14:03Z', 'PENDING_RESOLUTION'
);
```

**2.4 — Emit onto the event bus:**

```json
Topic: trigger.detected
Partition key: proj_8841
{
  "trigger_id": "trg_2f9a1c",
  "project_id": "proj_8841",
  "occurred_at": "2026-07-28T09:14:03Z"
}
```

---

## PHASE 3 — Key Resolution Service

Consumes `trigger.detected`. Fetches the Trigger, resolves its raw references against the Graph Layer's key-index.

```
GET graph://proj_8841/keys?spec_section=23+31+13
GET graph://proj_8841/keys?drawing=doc_M-2.1
```

Returns three candidate key matches:

```json
[
  { "artifact_ref": "po_4471", "match_basis": "cost_code_exact", "match_score": 0.98 },
  { "artifact_ref": "po_4488", "match_basis": "graph_edge:structural_dependency", "match_score": 0.71 },
  { "artifact_ref": "po_4512", "match_basis": "graph_edge:temporal_dependency", "match_score": 0.68 },
  { "artifact_ref": "sched_3410", "match_basis": "graph_edge:location_adjacency", "match_score": 0.44 }
]
```

Emitted:

```json
Topic: keys.resolved
{ "trigger_id": "trg_2f9a1c", "candidates": [ ...as above... ] }
```

---

## PHASE 4 — Graph Layer

**4.1 — Read path** (already exercised above by Key Resolution's traversal). The graph, for this project, holds — among thousands of nodes — this locally relevant subgraph:

```
(RFI-214)-[references]->(Spec 23 31 13)-[procured_under]->(Cost Code 23-100)-[line_item_of]->(PO-4471)-[supplied_by]->(VendorCo Metals)
(PO-4471)-[structurally_depends_on, confidence:0.71]->(PO-4488)-[supplied_by]->(Arjun Steelworks)
(Spec 23 31 13)-[temporally_scheduled_with, confidence:0.68]->(PO-4512)-[supplied_by]->(ThermaWrap)
(Grid B-4)-[location_adjacent, confidence:0.44]->(Schedule Activity 3410)
```

**4.2 — Write path.** This Trigger doesn't add new nodes (the artifacts already existed from onboarding calibration) — but it does append a new, versioned edge: `(RFI-214)-[triggered_event:evt_7731]->(Spec 23 31 13)`, timestamped, non-destructive. The graph's history now shows this exact traversal was available *at this moment* — relevant if a dispute later asks "what did the system know, and when."

---

## PHASE 5 — Reasoning Pipeline

**5a — Trigger Understanding.** The document-intelligence stage opens `procore://attachments/991211` (SK-14_reroute.pdf) and the cited Drawing M-2.1 Rev C, extracting structured fields:

```json
{
  "trigger_id": "trg_2f9a1c",
  "extracted_scope_change": "Duct DN200 rerouted 0.6m south of Beam B-14",
  "affected_quantity": "duct run: 4.2 linear meters; hanger points: 3",
  "extraction_confidence": 0.93
}
```

**5b — Candidate Resolution.** Walks the graph outward from `Spec 23 31 13` and `Grid B-4`, confirming the four candidates already surfaced by Key Resolution, now enriched with each artifact's live lifecycle snapshot (fetched via each artifact's own Commercial Connector — see Phase 9 for how PO-4471's snapshot arrives from SAP):

```json
[
  { "artifact_ref": "po_4471", "lifecycle_position": "IN_FABRICATION", "value_inr": 820000 },
  { "artifact_ref": "po_4488", "lifecycle_position": "SHIPPED",       "value_inr": 610000 },
  { "artifact_ref": "po_4512", "lifecycle_position": "SCHEDULED",     "value_inr": 410000 },
  { "artifact_ref": "sched_3410", "lifecycle_position": "N/A", "value_inr": 0 }
]
```

**5c — Confidence Tiering.** Combines match_score + extraction_confidence + graph edge confidence into the three honest tiers, each with a stated reason:

```json
[
  { "artifact_ref": "po_4471", "tier": "CERTAIN",
    "reason": "RFI-214 §2 cites Spec 23 31 13, exact match to PO-4471's cost code 23-100" },
  { "artifact_ref": "po_4488", "tier": "PROBABLE",
    "reason": "Hanger steel structurally dependent on rerouted duct; inferred graph edge, not a direct key match" },
  { "artifact_ref": "po_4512", "tier": "PROBABLE",
    "reason": "Insulation delivery scheduled around this duct run; temporal dependency, not a direct key match" },
  { "artifact_ref": "sched_3410", "tier": "POSSIBLE",
    "reason": "Same location, no direct scope reference — worth a human glance, not asserted as fact" }
]
```

**5d — Severity Computation** (deterministic, inspectable — `severity = f(value, lifecycle_weight, confidence_tier)`):

```json
[
  { "artifact_ref": "po_4488", "severity": 1, "why": "SHIPPED — highest lifecycle distance, most expensive to unwind" },
  { "artifact_ref": "po_4471", "severity": 2, "why": "IN_FABRICATION — costly but not yet physically committed" },
  { "artifact_ref": "po_4512", "severity": 3, "why": "SCHEDULED, not yet fabricated — cheapest to redirect" },
  { "artifact_ref": "sched_3410", "severity": 4, "why": "POSSIBLE tier only — informational" }
]
```

Note the ordering: PO-4488 outranks PO-4471 in severity despite lower confidence, because it is already shipped — the lifecycle-distance law overriding naive "the one the RFI literally mentions must be worst" intuition. This is the system doing exactly what it's for.

**5e — Grounded Drafting.** For each candidate above `POSSIBLE`, drafts an Action, citing only what 5a–5d already established:

```json
{ "artifact_ref": "po_4488", "action_type": "VENDOR_HOLD_NOTICE",
  "drafted_content": "Arjun Steelworks — hanger steel shipped against PO-4488 references duct geometry superseded by RFI-214 (Spec 23 31 13, Rev C). Requesting immediate hold on installation pending revised hanger spec. See attached: RFI-214 response, Drawing M-2.1 Rev C." }
{ "artifact_ref": "po_4471", "action_type": "ERP_HOLD_FLAG",
  "drafted_content": "Hold release-to-fabrication on PO-4471 pending revised duct geometry per RFI-214." }
{ "artifact_ref": "po_4512", "action_type": "ERP_RESCHEDULE",
  "drafted_content": "Reschedule ThermaWrap delivery on PO-4512 from Aug 22 to Sep 08 window, aligned to revised install sequence." }
{ "artifact_ref": "sched_3410", "action_type": "FLAG_FOR_REVIEW",
  "drafted_content": "Framing sequence at Grid B-4 shares this location — no scope match found. Flagged for scheduler awareness only." }
```

---

## PHASE 6 — Commercial Event Service: the domain writes

```sql
INSERT INTO commercial_events (event_id, project_id, trigger_id, severity, status, created_at)
VALUES ('evt_7731', 'proj_8841', 'trg_2f9a1c', 1, 'DETECTED', '2026-07-28T09:14:07Z');

INSERT INTO impacts (impact_id, event_id, artifact_ref, confidence_tier, confidence_reason, lifecycle_position_at_detection, severity, status)
VALUES
 ('imp_001','evt_7731','po_4488','PROBABLE','Structurally dependent...','SHIPPED',      1,'TRIAGED'),
 ('imp_002','evt_7731','po_4471','CERTAIN', 'Exact cost-code match...', 'IN_FABRICATION',2,'TRIAGED'),
 ('imp_003','evt_7731','po_4512','PROBABLE','Temporally scheduled...',  'SCHEDULED',     3,'TRIAGED'),
 ('imp_004','evt_7731','sched_3410','POSSIBLE','Location adjacency only...','N/A',       4,'TRIAGED');

INSERT INTO actions (action_id, impact_id, type, drafted_content, status)
VALUES
 ('act_001','imp_001','VENDOR_HOLD_NOTICE', '...', 'DRAFTED'),
 ('act_002','imp_002','ERP_HOLD_FLAG',      '...', 'DRAFTED'),
 ('act_003','imp_003','ERP_RESCHEDULE',     '...', 'DRAFTED'),
 ('act_004','imp_004','FLAG_FOR_REVIEW',    '...', 'DRAFTED');

UPDATE commercial_events SET status = 'TRIAGED' WHERE event_id = 'evt_7731';
```

Event bus emissions, in order:

```
event.created      { event_id: evt_7731, severity: 1 }
impact.tiered       { impact_id: imp_001, tier: PROBABLE, severity: 1 }
impact.tiered       { impact_id: imp_002, tier: CERTAIN,  severity: 2 }
impact.tiered       { impact_id: imp_003, tier: PROBABLE, severity: 3 }
impact.tiered       { impact_id: imp_004, tier: POSSIBLE, severity: 4 }
severity.computed    { event_id: evt_7731, severity: 1 }
action.drafted      { action_id: act_001 } action.drafted { action_id: act_002 }
action.drafted      { action_id: act_003 } action.drafted { action_id: act_004 }
```

---

## PHASE 7 — Ledger

Every message above is also appended, verbatim, to the append-only Ledger — nine rows, sequence-numbered, immutable:

```
seq 40021  trg_2f9a1c   TRIGGER_DETECTED     2026-07-28T09:14:03Z
seq 40022  evt_7731     EVENT_CREATED        2026-07-28T09:14:07Z  severity=1
seq 40023  imp_001      IMPACT_TIERED        PROBABLE  sev=1
seq 40024  imp_002      IMPACT_TIERED        CERTAIN   sev=2
seq 40025  imp_003      IMPACT_TIERED        PROBABLE  sev=3
seq 40026  imp_004      IMPACT_TIERED        POSSIBLE  sev=4
seq 40027  act_001..004 ACTION_DRAFTED       (4 rows)
```

`Commercial State` for `proj_8841` is not written anywhere — it is computed, live, from a query over this Ledger: `SELECT status, severity FROM ledger WHERE project_id='proj_8841' AND entity_type='commercial_event' AND status != 'CLOSED'`. Right now that query returns one row: `evt_7731, severity 1`.

---

## PHASE 8 — Realtime Gateway → WebSocket → Frontend (first paint)

The Realtime Gateway, already subscribed to the bus, filters every message above by `project_id: proj_8841` and forwards to every connected client entitled to that project. Ananya's browser tab (open on Commercial State) is one such client.

```
WS ← { "topic": "event.created", "project_id": "proj_8841", "event_id": "evt_7731", "severity": 1 }
WS ← { "topic": "impact.tiered", "impact_id": "imp_001", "severity": 1 }
WS ← { "topic": "impact.tiered", "impact_id": "imp_002", "severity": 2 }
WS ← { "topic": "impact.tiered", "impact_id": "imp_003", "severity": 3 }
WS ← { "topic": "impact.tiered", "impact_id": "imp_004", "severity": 4 }
```

**Frontend state change 1 — Commercial State page.** The hero line, which was reading "Synchronized," re-renders on the `event.created` message alone (it does not need the Impact detail to update the summary): **"1 open event · 1 critical."** The event appears atop the severity-sorted list beneath it.

**Frontend state change 2 — Event Inbox** (if open): a new row appears at the top — severity governs position, not recency — labeled with the Trigger's `display_number`, "RFI-214," and the computed severity badge.

---

## PHASE 9 — Notification Service

Consumes `severity.computed` for `evt_7731` (severity 1). Org policy: Severity 1–2 push immediately; 3–4 digest. This is a 1 → immediate push, routed per Ananya's configured channel:

```
POST https://hooks.slack.com/services/T00/B00/XYZ
{ "text": "🔴 Downstream: Sev-1 commercial event on Meridian Tower — RFI-214. Open: https://app.downstream.build/events/evt_7731" }
```

(Severity 3–4 impacts on this same event do not generate separate notifications — they will simply be visible when Ananya opens the event, per the digest policy; the event-level notification already fired on its worst-case severity.)

---

## PHASE 10 — Ananya opens the event

```
GET /events/evt_7731
Authorization: Bearer <session_token>
```

The Human Review & Approval Service (thin, synchronous) returns the full aggregate:

```json
{
  "event_id": "evt_7731", "severity": 1, "status": "TRIAGED",
  "trigger": { "display_number": "RFI-214", "occurred_at": "2026-07-28T09:14:03Z" },
  "impacts": [
    { "impact_id": "imp_001", "artifact": "PO-4488 · Hanger steel · Arjun Steelworks", "tier": "PROBABLE", "severity": 1, "action": { "id": "act_001", "type": "VENDOR_HOLD_NOTICE", "status": "DRAFTED" } },
    { "impact_id": "imp_002", "artifact": "PO-4471 · Duct fabrication · VendorCo Metals", "tier": "CERTAIN", "severity": 2, "action": { "id": "act_002", "type": "ERP_HOLD_FLAG", "status": "DRAFTED" } },
    { "impact_id": "imp_003", "artifact": "PO-4512 · Insulation · ThermaWrap", "tier": "PROBABLE", "severity": 3, "action": { "id": "act_003", "type": "ERP_RESCHEDULE", "status": "DRAFTED" } },
    { "impact_id": "imp_004", "artifact": "Schedule Activity 3410", "tier": "POSSIBLE", "severity": 4, "action": { "id": "act_004", "type": "FLAG_FOR_REVIEW", "status": "DRAFTED" } }
  ],
  "containment": "0 of 4 contained"
}
```

**Frontend state change 3 — Event Detail renders**, severity-first: PO-4488 (Sev-1) at top, down to the Possible-tier flag at bottom. Every Impact's evidence is collapsed by default; clicking one opens the actual cited passage from `procore://attachments/991211`, at the highlighted location — a real fetch through the Evidence Explorer, not a cached paraphrase.

---

## PHASE 11 — Approval cycle 1: PO-4488 (Severity 1)

**11.1 — Ananya reviews, edits nothing, clicks Approve** on `act_001`.

```
POST /actions/act_001/approve
{ "user_id": "user_2209", "edited_content": null }
```

**11.2 — Approval Service writes the immutable record:**

```sql
INSERT INTO approvals (approval_id, action_id, user_id, decision, edited_content, decided_at)
VALUES ('apr_001', 'act_001', 'user_2209', 'APPROVED', NULL, '2026-07-28T09:21:44Z');

UPDATE actions SET status = 'APPROVED' WHERE action_id = 'act_001';
```

Emitted: `action.approved { action_id: act_001 }`. Ledger appends both rows.

**11.3 — Synchronization Service** consumes `action.approved`. `act_001` is `VENDOR_HOLD_NOTICE` — the lower-trust, drafted-communication tier (no write-scope granted or needed on Arjun Steelworks' own systems). Dispatches via the Connector Layer's generic email adapter, carrying an idempotency key:

```
POST connector://email/dispatch
Idempotency-Key: act_001-dispatch-1
{
  "to": "procurement@arjunsteelworks.in",
  "subject": "Hold notice — PO-4488 hanger steel — RFI-214",
  "body": "...drafted_content from 5e, plus attached evidence links...",
  "cc": ["ananya.rao@meridiangc.example"]
}
```

Receipt returns synchronously: `{ "dispatch_id": "disp_5510", "status": "SENT" }`. Emitted: `action.dispatched { action_id: act_001 }`.

**11.4 — Confirmation.** The email adapter's delivery webhook fires minutes later:

```
POST /connectors/email/callback
{ "dispatch_id": "disp_5510", "status": "DELIVERED", "at": "2026-07-28T09:21:52Z" }
```

Synchronization Service consumes it, emits `action.confirmed { action_id: act_001 }`. Commercial Event Service advances:

```sql
UPDATE actions SET status = 'COMPLETED' WHERE action_id = 'act_001';
UPDATE impacts SET status = 'CONTAINED' WHERE impact_id = 'imp_001';
```

Containment check: 1 of 4 contained. Event stays `TRIAGED` (not all impacts closed). Ledger appends. Realtime Gateway pushes `impact.status { imp_001: CONTAINED }` — **Frontend state change 4:** the PO-4488 row's status pill flips from pending to a contained state, and the Event Detail's containment counter updates to **"1 of 4 contained."**

---

## PHASE 12 — Approval cycle 2: PO-4471 (Severity 2) — the ERP write-back

**12.1 — Approve** `act_002` (`POST /actions/act_002/approve`) → Approval `apr_002` written, `action.approved` emitted, Ledger appends — identical shape to 11.1–11.2.

**12.2 — Synchronization Service**, this time dispatching an **ERP write-back** — the deeper-trust tier, since this customer has granted write scope on their SAP tenant for PO hold flags specifically. The SAP connector must perform the real ceremony validated earlier:

```
GET https://s4.meridiangc.example/sap/opu/odata/sap/API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrder('4500018823')
X-CSRF-Token: fetch
Authorization: Bearer <sap_oauth_token>
```

Response header returns the session-scoped token: `X-CSRF-Token: 8Kf2-1Qz`. (`4500018823` is SAP's real 10-digit PO number — the system Downstream displays as the friendly label "PO-4471" internally maps to this identifier; this mapping is stored on the artifact record, exactly the display-vs-key duality the connector validation flagged.)

```
PATCH https://s4.meridiangc.example/sap/opu/odata/sap/API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrder('4500018823')
X-CSRF-Token: 8Kf2-1Qz
Idempotency-Key: act_002-dispatch-1
Content-Type: application/json

{ "PurchasingProcessingStatus": "HOLD", "CompanyCode": "1000", "Plant": "P100" }
```

Response: `204 No Content` (accepted). Emitted: `action.dispatched { action_id: act_002 }`.

**12.3 — Confirmation.** SAP's own Change Documents (CDHDR/CDPOS) record the field-level change natively; the connector polls (or, if the customer's landscape has Event Mesh configured, receives) confirmation and emits `action.confirmed { action_id: act_002 }`.

```sql
UPDATE actions SET status = 'COMPLETED' WHERE action_id = 'act_002';
UPDATE impacts SET status = 'CONTAINED' WHERE impact_id = 'imp_002';
```

2 of 4 contained. **Frontend state change 5:** PO-4471's row flips; counter reads **"2 of 4 contained."**

---

## PHASE 13 — Approval cycle 3: PO-4512 (Severity 3)

Same shape as Phase 12 — approve `act_003`, `apr_003` written, `action.approved` emitted — and a second SAP write-back, this time against the delivery-schedule field rather than the hold-status field:

```
PATCH .../A_PurchaseOrder('4500019104')/to_PurchaseOrderItem('00010')
X-CSRF-Token: 9Tn4-3Ab
Idempotency-Key: act_003-dispatch-1
{ "ScheduleLineDeliveryDate": "2026-09-08" }
```

Confirmed, `act_003` → `COMPLETED`, `imp_003` → `CONTAINED`. **3 of 4 contained.**

---

## PHASE 14 — Impact 4: the Possible-tier flag

Ananya reviews the Sched-3410 flag, confirms it's a non-issue, and acknowledges rather than "approves" a corrective transaction — there is nothing to synchronize, because a `POSSIBLE` tier never carries a forced action:

```
POST /actions/act_004/approve
{ "user_id": "user_2209", "decision": "ACKNOWLEDGED_NO_ACTION" }
```

```sql
INSERT INTO approvals (approval_id, action_id, user_id, decision, decided_at)
VALUES ('apr_004', 'act_004', 'user_2209', 'ACKNOWLEDGED_NO_ACTION', '2026-07-28T09:34:10Z');
UPDATE actions SET status = 'COMPLETED' WHERE action_id = 'act_004';
UPDATE impacts SET status = 'CONTAINED' WHERE impact_id = 'imp_004';
```

**4 of 4 contained.**

---

## PHASE 15 — Event closure and Commercial State resynchronization

Commercial Event Service's state machine, enforced centrally: all four Impacts are now `CONTAINED` — the Event advances:

```sql
UPDATE commercial_events SET status = 'CLOSED', closed_at = '2026-07-28T09:34:11Z' WHERE event_id = 'evt_7731';
```

Emitted: `event.closed { event_id: evt_7731 }`. Ledger appends the final row (`seq 40041`).

**The cost figure**, computed deterministically from data already on hand — sum of at-risk PO values against the containment actions actually taken, versus the counterfactual of discovery at delivery:

```json
{
  "event_id": "evt_7731",
  "value_at_risk_inr": 1840000,
  "cost_to_contain_now_inr": 120000,
  "estimated_cost_if_found_at_dock_inr": 1840000,
  "savings_inr": 1720000,
  "schedule_days_saved": 42
}
```

**Frontend state change 6 — final.** Realtime Gateway pushes `event.closed`. Commercial State's hero line recomputes, live, from the Ledger: **"Synchronized"** — the open-event count drops from 1 to 0. The Event Detail page shows **"4 of 4 contained · Closed"** and, as its closing line, the same cost figure above: *"Downstream's value on this event: ₹17.2 lakh and 42 days."*

Nothing here was scripted. Every one of the six frontend state changes was driven by a real message that had already been written to the Ledger before the Realtime Gateway ever forwarded it — which is the entire architectural guarantee this trace exists to demonstrate.

---

## What this trace is the reference for

Every stage boundary named in the systems architecture appears here exactly once, in the order it actually executes: Connector → Ingestion → Event Bus → Key Resolution → Graph → five-stage Reasoning → Commercial Event/Impact/Action → Ledger → Realtime Gateway → Approval → Synchronization (both tiers) → confirmation → closure → recomputed state. A backend engineer implementing any single stage can find, above, the exact shape of what it consumes and what it must emit — this is the contract every stage's tests should be written against.

## Caveats

- Field names, endpoint paths, and specific payload shapes (SAP OData fields, Procore response fields) are illustrative and modeled closely on the real contracts validated earlier in this project, but should be checked against live API versions before being treated as literal implementation targets — vendors revise these continuously.
- The severity/value/cost figures are computed here from seeded demo data chosen for narrative continuity with earlier design documents, not from a real historical dataset — the *mechanism* (deterministic function over value, lifecycle position, and confidence tier) is the reference; the specific numbers are illustrative.
- This trace shows the single-event, happy-path case. Failure-mode traces (a dispatch that exhausts retries, a Trigger that fails extraction mid-pipeline, a rejected Action) follow the same stage boundaries but were deliberately out of scope here to keep one complete scenario traceable end to end without interruption.