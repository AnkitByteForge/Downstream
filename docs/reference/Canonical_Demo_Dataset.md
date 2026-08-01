# Canonical Demo Dataset

### Specification, not a research report · the single project every subsystem seeds from

---

## 0. Purpose, authority, and how to read this document

This document freezes **one** commercial construction project — every seed script, integration test, and demo scenario across Downstream (Reference Engineering System, Reference Commercial System, Graph Layer, Reasoning Pipeline, and the frontend) is generated **from** this document, not invented independently by each subsystem. It is a specification of data, not of architecture: nothing here redesigns an entity, a state machine, or a service boundary — every field, transition, and relationship named below already exists in the frozen documents or the reference documents. Where this document assigns a concrete value (an ID, a date, a dollar figure), it is choosing one instance of an already-frozen shape, the same way RES-1's `meridian_tower.py` seed script already did for the RFI-214 trace.

**Authority order, if anything here ever conflicts:** the seven frozen documents (`01`–`07`) → `The Reference Engineering System.md` / `The Reference Commercial System.md` (this phase's own frozen functional specs) → `05_Downstream_Reference_Execution_Trace.md` (the literal, already-implemented scenario) → this document → the other reference documents (`The Enterprise Fidelity Review.md`, `Downstream Demo Strategy.md`, `Downstream_Intelligence_Specification.md`), which this document synthesizes into concrete data but does not outrank.

**What already exists vs. what this document adds.** `IMPLEMENTATION_STATUS.md` §10–§11 records that RES-1/RES-2 already built and seeded a real, tested slice of this dataset — the project, its location tree, Discipline M, SpecSection `23 31 13`, Drawing `M-2.1` (Rev B → Rev C), RFI-214, five users, two OAuth2 integration clients, and one webhook subscription. **That slice is frozen by virtue of already being live, tested code — this document does not change one field of it.** Everything else below is new: it extends the same project with the entities RES-3 onward will build (Submittals, Vendors, Commitments) and with the full commercial/graph/reasoning picture that doesn't exist as code anywhere yet, but must already be internally consistent on paper before RES-3 writes a single seed row.

**Two scenarios, one project.** Per the RES-3 plan's own finding (§5 of that plan): docs/05's RFI-214 trace and the Enterprise Fidelity Review's HVAC-upsizing scenario are not the same story, and neither replaces the other. Both live inside Meridian Tower, sharing its location tree, its disciplines, and (where realistic) its vendors:
- **Scenario A — "The Duct Reroute"** (§7 below): the frozen docs/05 trace, verbatim. Fully built since RES-1.
- **Scenario B — "The HVAC Upsize"** (§8 below): the Fidelity Review / Demo Strategy / Intelligence Specification's recommended scenario. Not yet built. RES-3 makes its engineering half (the Submittal) producible; its commercial half waits on the Reference Commercial System.

---

## 1. Project metadata

| Field | Value | Source |
|---|---|---|
| Project name | **Meridian Tower** | docs/05 (frozen), already seeded |
| Downstream-internal `project_id` | `proj_8841` | docs/05 §Scenario header (frozen literal value) |
| RES-internal surrogate key | integer, assigned on insert (currently `1` in a fresh seed) | RES-1 architecture — surrogate PKs are not the cross-system identifier, see §19 |
| Spec format | `MF2020` (CSI MasterFormat 2020, 50-division) | `The Reference Engineering System.md` §6; already seeded |
| Delivery method / type | Design-Bid-Build, vertical commercial office tower | Consistent with docs/05's cast (GC, procurement manager, subcontractors) and Fidelity Review Area 6 ("vertical government/commercial building" framing) |
| Project stage at scenario time | Construction administration, structure topped out, MEP rough-in and equipment procurement underway | Implied by docs/05 (duct fabrication, hanger steel shipped) and Scenario B (RTU submittal in review, switchgear already on order) |

---

## 2. Location hierarchy (Buildings / Floors / Zones / Locations)

Extends the four-tier tree already seeded in RES-1 (`Site → Building → Level → Gridline`) with the tiers Scenario B needs. All rows share `project_id = proj_8841` / RES `project.id`.

| id (business key) | Name | Type | Parent | Tier | New in this doc? |
|---|---|---|---|---|---|
| `LOC-SITE` | Meridian Tower Site | site | — | 0 | No — RES-1 |
| `LOC-BLDG-MAIN` | Main Building | building | `LOC-SITE` | 1 | No — RES-1 |
| `LOC-L01` | Level 1 | level | `LOC-BLDG-MAIN` | 2 | **Yes** |
| `LOC-L01-ELEC` | Level 1 Electrical Room | zone | `LOC-L01` | 3 | **Yes** — switchgear location |
| `LOC-L04` | Level 4 | level | `LOC-BLDG-MAIN` | 2 | No — RES-1 (was "Level 4") |
| `LOC-L04-GRIDB4` | Grid B-4 | gridline | `LOC-L04` | 3 | No — RES-1 |
| `LOC-ROOF` | Roof | level | `LOC-BLDG-MAIN` | 2 | **Yes** — RTU location |

`LOC-SITE`/`LOC-BLDG-MAIN`/`LOC-L04`/`LOC-L04-GRIDB4` names above are the exact `name` values already in the RES-1 seed script (`"Meridian Tower Site"`, `"Main Building"`, `"Level 4"`, `"Grid B-4"`) — the `LOC-*` codes here are this document's own stable reference labels for cross-document citation, **not** a new field to add to the schema; RES identifies a location by its `(project_id, name, parent)` path, exactly as already implemented.

---

## 3. Disciplines

| Code | Name | New? | Source |
|---|---|---|---|
| `M` | Mechanical | No — RES-1 | docs/05, `The Reference Engineering System.md` §13 |
| `E` | Electrical | **Yes** | `The Reference Engineering System.md` §13 (US National CAD Standard designator); required by Scenario B |
| `S` | Structural | **Yes, reserved not used** | Named for completeness (Fidelity Review's structural-steel alternate scenario, §102 of that doc) — no seeded artifact uses it yet; do not seed unused rows, listed here only so a future RES-4/5 structural scenario doesn't collide with an undocumented code choice |

---

## 4. CSI Specification hierarchy

| Division | Section | Title | New? | Used by |
|---|---|---|---|---|
| `23` (HVAC) | `23 31 13` | HVAC Ducts | No — RES-1 | Scenario A (RFI-214) |
| `23` (HVAC) | `23 74 13` | Packaged, Outdoor, Central-Station Air-Handling Units | **Yes** | Scenario B (RTU-1 submittal) — real CSI MasterFormat number |
| `26` (Electrical) | `26 24 13` | Switchboards | **Yes** | Scenario B (switchgear Commitment) — real CSI MasterFormat number |

**Deterministic cross-discipline edge** (per Intelligence Spec §13 Step 3 — "a cross-discipline reference edge, captured during initial project calibration"): `23 74 13 —[cross_discipline_reference, confidence 0.9]→ 26 24 13`. This is **Graph Layer seed data**, per docs/06 backlog item 2 ("the graph is seeded directly from known project data — the general-purpose... pipeline is real future work"), not an RES artifact — see §13.

---

## 5. Drawings & Drawing Revisions

| Drawing | Sheet # | Title | Discipline | Revisions |
|---|---|---|---|---|
| `DWG-M-2.1` | M-2.1 | Mechanical Plan – Level 4 | M | Rev B (2026-06-02, superseded) → **Rev C** (2026-07-28, current, revision cloud "Duct DN200 rerouted 0.6m south of Beam B-14") — No new content, RES-1 |

Scenario B does **not** introduce a new drawing revision at RES-3 — per the RES-3 plan's §5 finding, Intelligence Spec §13's canonical walkthrough triggers off the Submittal alone, with no drawing supersession required. A future RES-4 extension (once Design Change exists) may add `DWG-E-1.1` (Electrical Plan – Level 1, showing the switchgear lineup) revised by an ASI — flagged here as a **documented future extension**, not seeded now (see §8, "Stage B2").

---

## 6. RFIs

| RFI | Number | Subject | Status | New? |
|---|---|---|---|---|
| `RFI-214` | 214 | Duct routing conflict at Grid B-4 vs. structural beam | CLOSED | No — RES-1, frozen per docs/05 |

No new RFI is added for Scenario B — see §4's note on the cross-discipline edge being graph-seed data, not an RFI.

---

## 7. Submittals & Submittal Revisions

No submittal exists in the repository yet (RES-3 scope). This is what RES-3's seed script must produce, field for field.

| Submittal | Number | Spec section | Vendor | Package |
|---|---|---|---|---|
| `SUB-118` | 118 | `23 74 13` | Coastal Aire Equipment | (none — single-item submittal, Package left unused here; see §21) |

**Revisions:**

| Rev | Equipment tag | Manufacturer | Model | MCA | FLA | Status | `gates_procurement`? | Issued |
|---|---|---|---|---|---|---|---|---|
| Rev 0 | RTU-1 | Coastal Aire Equipment | CA-RTU-40 | 180 A | 150 A | Revise and Resubmit (coordination clearance issue, unrelated to load) | No | 2026-06-10 |
| **Rev 1** | RTU-1 | Coastal Aire Equipment | CA-RTU-55 | **240 A** | **200 A** | **No Exceptions Taken** | **Yes** | 2026-07-30 |

This is the literal artifact Intelligence Spec §13 Step 1–2 describes: *"a mechanical equipment Submittal for a rooftop unit is approved (status: No Exceptions Taken) on its second revision... the unit's MCA and FLA have increased."* Equipment tag/manufacturer/model/capacity fields live **on `SubmittalRevision`**, not a separate `Equipment` entity — per the Fidelity Review's own framing (Area 2: "fields that specifically matter for a PO... equipment tag/mark, model/manufacturer, capacity/size"), these are fields, not a new entity type any source names.

**Submittal register entry (spec-driven, per `The Reference Engineering System.md` §8):**

| SpecSection | Submittal type | Category | Required? |
|---|---|---|---|
| `23 74 13` | shop_drawing + product_data | Action | Yes — Division 01 33 00 governs |

**Long-lead flag:** `SUB-118`'s own lead time (RTU fabrication, ~10–14 weeks per standard packaged-equipment lead times) is **not** itself long-lead by the Fidelity Review's definition (that term is reserved for the *electrical* gear downstream of it — see §9). `required_on_site_date`: 2026-11-02. `lead_time_days`: 84. This does not trip the gate on its own; it is the trigger, not the long-lead exposure.

---

## 8. Design Changes — explicitly deferred, noted for continuity only

No `ASI`/`CCD`/`ChangeOrder` row is defined in this document. Per the approved RES-3 plan, the Design Change family is RES-4 scope. **Stage B2** (future, non-binding sketch, so RES-4's seed work has continuity to extend rather than invent from scratch): an ASI `ASI-07` citing `SUB-118` Rev 1's load increase, superseding `DWG-E-1.1` Rev 0 → Rev 1 on the electrical plan. Not to be seeded before RES-4.

---

## 9. Vendors

| Vendor | Role | Scenario | New? |
|---|---|---|---|
| VendorCo Metals | Duct fabricator, PO-4471 | A | No — named in docs/05 |
| Arjun Steelworks | Hanger steel, PO-4488 | A | No — named in docs/05; **already the employer of seeded user Vikram Suresh** (RES-1), a continuity detail worth preserving |
| ThermaWrap | Insulation, PO-4512 | A | No — named in docs/05 |
| Coastal Aire Equipment | RTU-1 manufacturer/submittal vendor | B | **Yes** |
| Voltrex Switchgear Inc. | Switchgear manufacturer, PO-5201 | B | **Yes** |
| Ferro Electrical Supply | Feeder/busway supplier, PO-5202 | B | **Yes** |

All new vendor names are fictitious, generic, and deliberately non-referential to any real manufacturer — consistent with the existing seed's own naming convention (VendorCo, ThermaWrap).

---

## 10. Commitments / Purchase Orders / Delivery schedule

**Scenario A — frozen, verbatim from docs/05:**

| Artifact ref | Type | SAP-style number | Vendor | Cost code | Lifecycle position | Value (INR) |
|---|---|---|---|---|---|---|
| `po_4471` | PO | `4500018823` | VendorCo Metals | `23-100` | IN_FABRICATION | 820,000 |
| `po_4488` | PO | *(not stated in trace)* | Arjun Steelworks | *(inherited via structural dependency)* | SHIPPED | 610,000 |
| `po_4512` | PO | `4500019104` | ThermaWrap | *(inherited via temporal dependency)* | SCHEDULED | 410,000 |
| `sched_3410` | Schedule Activity | — | — | — | N/A | 0 |

**Scenario B — new, this document:**

| Artifact ref | Type | SAP-style number | Vendor | Cost code | Lifecycle position | Value (INR) | Long-lead? |
|---|---|---|---|---|---|---|---|
| `po_5201` | PO (switchgear lineup) | `4500020045` | Voltrex Switchgear Inc. | `26-200` | **IN_FABRICATION** | 42,000,000 | **Yes — 44 weeks, non-cancellable once released** (Fidelity Review §Area 7, cited Wood Mackenzie Q2 2025) |
| `po_5202` | PO (feeder/busway) | `4500020091` | Ferro Electrical Supply | `26-200` | **SHIPPED** (in transit) | 6,500,000 | No — standard lead time |
| `req_5203` | Delivery/requisition (branch conduit) | *(not yet a PO)* | *(not yet committed)* | `26-200` | **DRAFT** | 180,000 | No |

Cost code `26-200` deliberately mirrors the `23-100` convention already implied by Scenario A (`{division}-{sequence}`), per `The Reference Engineering System.md` §6's cost-code-format guidance and docs/04's `cost_code_format` field (tagged `CSI MasterFormat`-derived here, not SAP WBS, since this is the engineering-side cost code before SAP's own WBS mapping is applied).

**These are Reference Commercial System artifacts — no code exists yet to hold them.** They are specified here so that when the Reference Commercial System is built, its own seed script has one already-consistent source, not an independently invented one.

---

## 11. Equipment & Equipment Tags

Per §7's note: modeled as fields on `SubmittalRevision`, not a standalone entity. Consolidated list for traceability:

| Tag | Discipline | Submittal | Manufacturer | Model | Capacity |
|---|---|---|---|---|---|
| `RTU-1` | M | `SUB-118` Rev 1 | Coastal Aire Equipment | CA-RTU-55 | 240 A MCA / 200 A FLA |
| `SWGR-1` | E | *(no submittal in RES scope — commercial-side only)* | Voltrex Switchgear Inc. | VSI-4000MV | 4000 A, 15 kV class |

`SWGR-1` has no corresponding `Submittal` row because, per Intelligence Spec §13, the switchgear side is reached entirely through the graph/commercial join (`PROCURED_UNDER` → `LINE_ITEM_OF`), never through an RES-owned document — this is the seam between the two reference systems, not a gap in this dataset.

---

## 12. Users & Ball-in-court assignments

| User | Role | Scenario A role | Scenario B role |
|---|---|---|---|
| Ananya Rao (`ananya.rao@meridiangc.example`) | PROJECT_MANAGER | RFI-214 ball-in-court (manager, on close); approves all four Actions (docs/05 `user_2209`) | Would approve the switchgear PO Amendment / Vendor Notification (Intelligence Spec §13 Step 11) |
| Kabir Mehta (`kabir.mehta@meridiangc.example`) | PROJECT_ENGINEER | RFI-214 ball-in-court (assignee, on open) | Submittal `SUB-118` reviewer (GC-side) |
| Rhea Fernandes (`rhea.fernandes@archstudio.example`) | ARCHITECT_ENGINEER_OF_RECORD | — | `SUB-118` A/E-side reviewer of record (issues the "No Exceptions Taken" disposition on Rev 1) |
| Vikram Suresh (`vikram.suresh@arjunsteelworks.example`) | SUBCONTRACTOR | Employed by PO-4488's vendor (Arjun Steelworks) — a pre-existing continuity detail | — |
| System Admin (`admin@downstream.example`) | ADMIN | — | — |

No new users are required for Scenario B — its ball-in-court assignments reuse Ananya and Kabir's existing seeded roles, and add Rhea (already seeded, previously unused by Scenario A) as the A/E reviewer. This is deliberate: it proves the same five-user cast is sufficient for both scenarios, rather than growing the user list per scenario.

---

## 13. Relationships between every entity (the graph)

**Scenario A** (verbatim from docs/05 Phase 4.1 — already the literal seeded/tested subgraph):

```
(RFI-214)-[references]->(Spec 23 31 13)-[procured_under]->(Cost Code 23-100)-[line_item_of]->(PO-4471)-[supplied_by]->(VendorCo Metals)
(PO-4471)-[structurally_depends_on, confidence:0.71]->(PO-4488)-[supplied_by]->(Arjun Steelworks)
(Spec 23 31 13)-[temporally_scheduled_with, confidence:0.68]->(PO-4512)-[supplied_by]->(ThermaWrap)
(Grid B-4)-[location_adjacent, confidence:0.44]->(Schedule Activity 3410)
```

**Scenario B** (new, this document, same edge-type vocabulary per `03_Downstream_Systems_Architecture.md` §6 Graph DB edge types):

```
(Submittal SUB-118 Rev 1)-[references]->(Spec 23 74 13)
(Spec 23 74 13)-[cross_discipline_reference, confidence:0.90]->(Spec 26 24 13)
(Spec 26 24 13)-[procured_under]->(Cost Code 26-200)-[line_item_of]->(PO-5201)-[supplied_by]->(Voltrex Switchgear Inc.)
(PO-5201)-[scheduled_with]->(Delivery: Switchgear Lineup, on-site 2027-05-15)
(PO-5201)-[structurally_depends_on, confidence:0.75]->(PO-5202)-[supplied_by]->(Ferro Electrical Supply)
(Cost Code 26-200)-[temporally_scheduled_with, confidence:0.40]->(REQ-5203, branch conduit, draft)
```

Both subgraphs share nothing except being in the same project — by design, they are two independent trigger chains, proving the graph and reasoning layers generalize rather than being hard-coded to one trade (Fidelity Review Recommendation #7: "do not over-build... prove the engine is not hard-coded to one trade").

---

## 14. Expected engineering events (what the RES must actually emit)

These are the **RES-owned, already-verifiable** events — the ones RES-3's contract tests assert.

| Trigger | Thin webhook payload (exact 5 keys, per docs/04) | Scenario |
|---|---|---|
| RFI-214 closed | `{resource_name: "rfis", resource_id: <id>, project_id: <id>, event_type: "update", timestamp: "2026-07-28T09:14:03Z"}` | A — already built, RES-2 |
| Drawing M-2.1 Rev C issued | `{resource_name: "documents", resource_id: <version id>, project_id: <id>, event_type: "update", timestamp: "2026-07-28T..."}` | A — extension confirmed in scope by RES-3 plan §2 item 6, not yet built |
| Submittal SUB-118 → Rev 1 "No Exceptions Taken" | `{resource_name: "submittals", resource_id: <id>, project_id: <id>, event_type: "update", timestamp: "2026-07-30T..."}` | B — RES-3 to build |

---

## 15. Expected commercial artifacts (what the Reference Commercial System must eventually hold)

Restates §10 in the exact `CommercialArtifactSnapshot` shape from `packages/envelope-schemas` (already implemented, Downstream Milestone 0), so a future Reference Commercial System build has a literal target to match:

```json
{
  "envelope_type": "CommercialArtifactSnapshot",
  "source_system": "sap",
  "source_id": "4500020045",
  "artifact_type": "PO",
  "cost_code": "26-200",
  "cost_code_format": "CSI_MASTERFORMAT",
  "spec_section_refs": ["26 24 13"],
  "lifecycle_position": "IN_FABRICATION",
  "value": 42000000,
  "vendor_ref": "Voltrex Switchgear Inc.",
  "project_ref": "proj_8841",
  "data_freshness_path": "polled",
  "fetched_at": "2026-07-30T00:00:00Z"
}
```
(shown for `po_5201`; `po_5202` and `req_5203` follow the same shape with their own §10 values.)

---

## 16. Expected Downstream reasoning output

**Scenario A** — restates docs/05 Phase 5c/5d/5e and Phase 6 verbatim (already the literal, tested target once Downstream's own Reasoning Pipeline exists): four Impacts (`po_4488` CERTAIN Sev 1 → wait, verbatim correction below), Event `evt_7731`, four Actions, value-at-risk ₹18.4L, savings ₹17.2L, 42 days. Reproduced exactly as docs/05 states it — **not re-derived here**, to avoid two documents disagreeing on the same frozen numbers:

| Artifact | Confidence | Severity | Action |
|---|---|---|---|
| `po_4488` | PROBABLE | 1 | VENDOR_HOLD_NOTICE |
| `po_4471` | CERTAIN | 2 | ERP_HOLD_FLAG |
| `po_4512` | PROBABLE | 3 | ERP_RESCHEDULE |
| `sched_3410` | POSSIBLE | 4 | FLAG_FOR_REVIEW |

**Scenario B** — restates Intelligence Spec §13 Steps 8–10 verbatim, mapped onto this document's own artifact refs:

| Artifact | Confidence | Severity | Recommendation |
|---|---|---|---|
| `po_5201` (switchgear) | **CERTAIN** — direct cost-code match + explicit cross-discipline reference note, two corroborating signals | **1** — in_fabrication, critical exposure, on critical path (44-week lead time) | **PO Amendment** + **Vendor Notification**, flagged urgent (lead-time-restart risk) |
| `po_5202` (feeder) | **PROBABLE** — reached one further hop, no independent citation of its own | **2** — shipped, materially lower value than switchgear | **Procurement Review** |
| `req_5203` (branch conduit) | **POSSIBLE** — location/discipline adjacency only | **4** — draft, low exposure, nothing committed | **Monitor**, re-evaluate if it converts to a PO |

Neither table above is invented by this document — both are the literal frozen/reference-document outputs, restated here only so the same artifact refs used in §10/§13 line up with them for whoever builds the Reasoning Pipeline's own tests later.

---

## 17. Scenario A — "The Duct Reroute" (full trace pointer)

Fully specified in docs/05, fully built (RES-1/RES-2), fully covered by §§2–3, 5–6, 10, 13, 14, 16 above. This document does not restate its narrative prose — see docs/05 directly. Listed here only as the second half of "two scenarios, one project" (§0).

---

## 18. Scenario B — "The HVAC Upsize" (narrative, for continuity)

1. RTU-1's submittal is prepared (Rev 0), sent back Revise-and-Resubmit for an unrelated coordination clearance issue — a realistic false start, not itself the trigger.
2. RTU-1's submittal is resubmitted (Rev 1) with a larger unit (CA-RTU-55 replacing CA-RTU-40) to meet a revised cooling load — MCA/FLA both increase. A/E (Rhea Fernandes) marks it **No Exceptions Taken**. *(RES-3 produces exactly this event — see §14.)*
3. Downstream's Reasoning Pipeline (not yet built) would: normalize the MCA/FLA delta, resolve `23 74 13`, traverse the pre-seeded cross-discipline edge to `26 24 13`, reach the switchgear PO, feeder delivery, and branch-conduit requisition in confidence/severity order, and draft the three recommendations in §16.
4. A human (Ananya) reviews switchgear first (Severity 1), approves the PO Amendment and Vendor Notification; reviews the feeder's Procurement Review and confirms the inferred dependency; acknowledges the conduit Monitor flag with no action.

This is Intelligence Spec §13's walkthrough, retold with this document's own concrete IDs substituted in — nothing added, nothing renamed.

---

## 19. ID stability contract

**The word "stable" does not mean "the same literal value in every subsystem's database."** Three different ID spaces coexist by design, and conflating them is exactly the display-vs-key confusion docs/04 warns against:

1. **RES-internal surrogate keys** (`SERIAL`/`BIGINT` PKs in the Reference Engineering System's own Postgres) — assigned on insert, never referenced outside that one service, never appear in this document as the identifier of record.
2. **Business/natural keys** — `RFI.display_number` ("RFI-214"), `Drawing.sheet_number` + `DrawingVersion.revision_label` ("M-2.1 Rev C"), `SpecSection.number` ("23 31 13"), `Submittal.number` + revision index ("SUB-118 Rev 1"), `Vendor.name`, `User.email`, and the `LOC-*` labels in §2. **These are what this document fixes, and what every seed script across every subsystem must reproduce identically.**
3. **Downstream-internal IDs** (`proj_8841`, `trg_2f9a1c`, `evt_7731`, `po_4471`, etc.) — assigned by Downstream's own Ingestion/Reasoning services per `packages/shared-config`'s prefix scheme. For Scenario A these are **frozen literal values already fixed by docs/05** and reproduced verbatim throughout this document. For Scenario B, this document deliberately does **not** invent Downstream-side IDs (`evt_...`, `imp_...`) beyond the artifact refs already listed in §10/§13/§16 (`po_5201`, `po_5202`, `req_5203`) — those three are stable business-key-style refs this document is coining now, precisely so they can be typed once and reused everywhere; the fully-Downstream-generated IDs (a specific `evt_...`/`trg_...` value) don't exist until Downstream's own Reasoning Pipeline runs and are out of this document's authority to pre-assign.
4. **Cross-system mapping** — the `artifact_identity_map` table already specified in `07_Downstream_Implementation_Blueprint.md` §6 is the literal mechanism that ties (2) and (3) together once both sides exist (`po_5201` ↔ SAP `4500020045`). This document's job ends at making sure (2) is identical everywhere; wiring (4) is that table's job, not this document's.

---

## 20. Traceability matrix — every section's authority

| §§ | Content | Primary source |
|---|---|---|
| 1–2, 5–6, 10 (Scenario A rows), 13 (Scenario A), 16 (Scenario A) | Project/location/drawing/RFI/graph/reasoning for Scenario A | `05_Downstream_Reference_Execution_Trace.md` (frozen), already built per `IMPLEMENTATION_STATUS.md` §10 |
| 3 (`E` discipline), 4, 7, 9 (new vendors), 10 (Scenario B), 11 | Submittal/vendor/PO/equipment data for Scenario B | `The Enterprise Fidelity Review.md` §Area 7, `Downstream Demo Strategy.md` Scenario #1, `Downstream_Intelligence_Specification.md` §13 |
| 7 (state machine shape, register mechanism) | Submittal lifecycle and register | `The Reference Engineering System.md` §8, §16 |
| 13 (edge types), 15 | Graph edge vocabulary, envelope shape | `03_Downstream_Systems_Architecture.md` §6; `packages/envelope-schemas` (already implemented) |
| 16 (confidence/severity model) | Reasoning output | `Downstream_Intelligence_Specification.md` §7–§9, §13 |
| 19 | ID scheme | `04_Downstream_Connector_Layer_Validation.md`; `07_Downstream_Implementation_Blueprint.md` §6; `packages/shared-config` (already implemented) |

---

## 21. What this document does not do

It does not write a migration, a seed script, a test, or a line of application code — those are RES-3's (and later milestones') job, using this document as their single input instead of each inventing its own fixture. It does not decide Submittal Packages' schema shape (ADR-005, still pending your approval from the RES-3 plan) — `SUB-118` is deliberately a single-item submittal with no package, so this dataset doesn't silently presuppose that decision either way. It does not seed Design Changes, Field Issues, ClashItems, or ScheduleActivities beyond `sched_3410` (already frozen) — those remain RES-4/RES-5 scope per the approved plan, and this document's §8 sketch is explicitly non-binding.

---

## 22. Open items requiring your confirmation before this feeds RES-3's seed script

1. **CSI section numbers** (`23 74 13`, `26 24 13`) are real MasterFormat numbers I selected as realistic fits for "packaged rooftop unit" and "switchboards" respectively — confirm they're acceptable, or specify different sections if you have ones in mind.
2. **Dollar/lead-time figures** in §10 (₹42,000,000 switchgear PO, 44-week lead time, etc.) are illustrative, scaled to be internally consistent with docs/05's own INR figures and the Fidelity Review's cited lead times — confirm the currency/scale convention (docs/05 uses INR; the Fidelity Review's cited figures are USD-denominated industry averages) is fine to keep as INR throughout, or should Scenario B switch currency to match the Fidelity Review's sourcing more literally.
3. **Vendor names** (Coastal Aire Equipment, Voltrex Switchgear Inc., Ferro Electrical Supply) are fictitious placeholders in the existing seed's style — confirm, or provide preferred names.
4. **`E` discipline and Level 1/Roof locations** are additions beyond RES-1's seeded set — confirm these are fine to add in RES-3's migration/seed, not held back for a later milestone.

No code, migration, or seed script has been written. Waiting for your approval before RES-3 implementation begins.
