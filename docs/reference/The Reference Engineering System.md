# The Reference Engineering System: A Vendor-Neutral Domain Model for Construction Engineering, Grounded in Real Practice

## TL;DR
- A realistic Reference Engineering System should model roughly fifteen core entity types (Drawing/DrawingVersion, SpecSection, RFI, Submittal, DesignChange with subtypes ASI/CCD/PCO/ChangeOrder, FieldIssue, ClashItem, Discipline, Location, ScheduleActivity, Vendor/Commitment, and a Transmittal distribution record) connected by a small set of typed relationships (REFERENCES, REQUIRED_BY, SUPERSEDES, RESPONDS_TO, TRIGGERS, PROCURED_UNDER, LOCATED_AT, SCHEDULED_WITH), each artifact carrying an explicit **state machine** — because that combination of typed relationships plus lifecycle state is exactly what lets Downstream trace an engineering trigger to a purchase order, vendor, and delivery.
- The highest-value commercial-impact triggers are, in order: **MEP coordination clashes** (Helonic's 2025 "MEP Coordination Best Practices" attributes 40% of all construction RFIs to MEP conflicts and names them the leading cause of rework in commercial and institutional buildings), **spec substitutions/product changes**, **late structural revisions affecting already-fabricated material (rebar, embeds, structural steel)**, and **RFI responses that escalate into ASIs, CCDs, or change orders** — the fields that most reliably predict PO/vendor/delivery impact are a submittal's `spec_section` + `required_on_site_date` + `lead_time`, a drawing version's revision-cloud/delta scope + discipline, and any artifact's `cost_impact` flag and linked `cost_code`/`commitment`.
- The model must faithfully reproduce **real lifecycle mechanics**: drawing versioning by issuance date with clouds/deltas and explicit supersession; RFI ball-in-court routing that can spawn an ASI/CCD; submittal review statuses ("No Exceptions Taken," "Revise and Resubmit," etc.) that **gate fabrication and procurement**; spec-driven submittal registers; and multi-tier location and discipline dimensions — all common patterns across Procore, Autodesk Construction Cloud/Forma, Bentley SYNCHRO, Oracle Primavera, and Trimble ProjectSight rather than any one vendor's schema.

## Key Findings

**1. The engineering workflow is a continuous office-to-field feedback loop, not a linear handoff.** Design coordination, RFI cycles, drawing issuance, submittal review, and field feedback run concurrently during construction administration. A field engineer's daily rhythm centers on punch lists, safety inspections, and drawing markups; a project coordinator's on daily logs, RFI management, submittal tracking, and meeting minutes. Field observations flow up into RFIs; RFI responses flow back down as ASIs or revised drawings; revised drawings drive submittal resubmittals; submittal approvals release procurement and fabrication. This loop is the engine Downstream must instrument.

**2. Artifacts have distinct producers and consumers, and each is a first-class node.** Drawings (produced by A/E, consumed by everyone), specifications (A/E → contractor/estimators/reviewers), RFIs (contractor → A/E), submittals/shop drawings (subcontractor → GC → A/E), ASIs/bulletins (A/E → contractor), field reports (A/E site visits), punch lists (GC/architect at substantial completion), BIM models and clash reports (VDC/BIM coordinators), meeting minutes, and transmittals (document-control record of who received which sheet at which revision).

**3. Relationships form a graph, not a list.** An RFI references one or more drawing sheets and spec sections; a submittal is required by a spec section; an ASI supersedes/modifies a drawing revision; a field issue generates an RFI; a clash generates an RFI; an RFI response triggers an ASI, which triggers a drawing revision, which triggers a submittal resubmittal, which affects a purchase order. The memory aid practitioners use — **"RFIs ask, ASIs tell, Change Orders modify, and CCDs direct"** — captures the directional semantics the model must encode.

**4. MEP coordination and late design changes are the dominant commercial-risk categories,** consistently identified across multiple independent industry sources, making them the highest-priority trigger patterns for downstream reasoning.

## Details

### 1. How engineering teams actually work day-to-day
Modern construction engineering is organized around **construction administration (CA)** — the phase after Issued-for-Construction (IFC) drawings are released. The rhythm:
- **Design coordination** happens continuously; BIM/VDC coordinators federate discipline models (architectural, structural, MEP-FP) into a single coordination model and run clash detection at defined milestones (commonly at 30% / 60% / 90% construction-document phases, and weekly/biweekly on design-build jobs).
- **RFI cycles** are the "heartbeat of construction communication." Per the Navigant Construction Forum's 2013 study *Impact and Control of RFIs on Construction Projects* (1,362 projects, over one million RFIs): median RFI closure was 9.7 days, first reply averaged 6.4 days, projects averaged 796 RFIs each at roughly $1,080 review-and-response cost apiece (~9.9 RFIs per $1M of construction value, or about $859,000 per project in aggregate review cost).
- **Drawing issuance** follows formal sets: Design Development → Construction Documents → Issued for Permit → Issued for Construction, then bulletins/revisions during construction.
- **Field-to-office feedback**: superintendents and field engineers capture observations, punch items, and progress on location-tagged mobile tools; these feed the PM/architect the same day and can escalate to RFIs or change events.

Role division observed in practice: **Project Manager** oversees the submittal process and protects long-lead/critical-path items; **Project Engineer** does day-to-day submittal-log tracking, numbering, and resubmission coordination; **Subcontractors** prepare shop drawings/product data/samples; **Architect/Engineer of Record** reviews for conformance with contract documents.

### 2. Engineering artifacts (what / who-creates / who-consumes)
- **Drawings / Sheets** — graphic contract documents; created by A/E; consumed by all trades. Organized by discipline sheet number (e.g., A-101).
- **Specifications** — written contract requirements; created by A/E/spec writer; consumed by estimators, reviewers, subs. "Drawings and specifications are complementary and carry equal weight."
- **RFI (Request for Information)** — contractor→A/E clarification request; AIA Document G716 is the standard form.
- **Submittal** (shop drawings, product data, samples) — subcontractor→GC→A/E; proves conformance before fabrication/procurement.
- **ASI (Architect's Supplemental Instruction)** — A/E→contractor minor-change directive; AIA G710.
- **Bulletin / Proposal Request (PR)** — A/E-issued packages of drawing changes for pricing (firm-specific naming; "bulletin" or "field order" often used in lieu of ASI).
- **CCD (Construction Change Directive)** — A/E+owner directive to proceed before price agreement; AIA G714.
- **Change Order** — executed three-party contract modification; AIA G701.
- **Field reports / observations (SOR)** — A/E site-visit records; may lead to RFIs.
- **Punch list / deficiency items** — GC/architect near substantial completion; location- and photo-tagged.
- **BIM models & clash detection reports** — VDC/BIM coordinators; hard/soft/workflow(4D) clashes.
- **Meeting minutes** (OAC meetings), **Transmittals** (document-control distribution records).

### 3. The relationship graph
Core edges (vendor-neutral):
- `RFI —REFERENCES→ DrawingVersion` and `RFI —REFERENCES→ SpecSection`
- `Submittal —REQUIRED_BY→ SpecSection`
- `ASI —SUPERSEDES/MODIFIES→ DrawingVersion` (issues a new revision)
- `FieldIssue —GENERATES→ RFI`; `ClashItem —GENERATES→ RFI`
- `RFI —RESPONSE_TRIGGERS→ ASI | CCD | ChangeOrder`
- `DrawingVersion —SUPERSEDES→ DrawingVersion` (prior revision)
- `Submittal —GATES→ FabricationRelease/PurchaseOrder`
- `DesignChange —AFFECTS→ Commitment/PurchaseOrder —SUPPLIED_BY→ Vendor`
- `Artifact —LOCATED_AT→ Location`; `Artifact —IN_DISCIPLINE→ Discipline`
- `ScheduleActivity —DELIVERS→ Material`; `Submittal —SCHEDULED_WITH→ ScheduleActivity`

### 4. Drawing lifecycle
Real practice (from engineering CAD standards and Autodesk/Revit revision tooling):
- **Creation** in authoring tools (Revit/AutoCAD/Civil 3D); assigned a discipline sheet number.
- **Issuance** as formal sets; lettered revisions (Rev A, B…) during design, numbered revisions (Rev 0, 1, 2…) starting at IFC.
- **Revision** marked with **revision clouds** (enclosing the changed area) and a **delta** (numbered triangle keyed to the title-block revision schedule). Rule of thumb: "If the change, in any way, affects what or how something is constructed then that constitutes a revision and therefore a cloud." A typo alone should not be clouded. Only the most-recent revision's clouds are shown; prior clouds are turned off while deltas remain in the revision history.
- **Supersession & "current version"**: modern platforms determine the current sheet by **issuance date of the version set** (Autodesk Forma/ACC: "Issuance date of a version set will drive what is considered current… this aligns to the logic of the Sheets tool"). The dominant document-control failure is "allowing multiple versions of a document to circulate at the same time without a clear record of which one is current."
- **Distribution** is recorded with a **transmittal** listing every sheet and revision distributed.

### 5. RFI lifecycle
- **Trigger conditions**: unclear/conflicting/missing information in contract documents; field conditions; coordination clashes; cost/VE questions.
- **Drafting**: sequential RFI number, references to specific sheets and spec sections, suggested resolution, required response date, cost-impact flag, cost code.
- **Ball-in-court routing**: the "backbone of workflow management." Creating an RFI "as Open" shifts ball-in-court to assignees; forwarding transfers it; on response it returns to the RFI Manager (typically GC). This is a true state machine: Draft → Open (BIC = assignee) → Responded (BIC = manager) → Closed.
- **Response → downstream trigger**: an RFI "may result in an Architect's Supplemental Instruction (ASI) or Proposal Request (PR)." If the RFI reveals a true drawing deficiency, it schedules a bulletin/ASI and a drawing revision; if it reveals added scope/cost, it feeds a PCO/change event.

### 6. Specification management
- Organized by **CSI MasterFormat** — 50 divisions (00–49) since the 2004 expansion from 16; six-digit section numbers (Division–Level 2–Level 3, e.g., 03 11 00). Older/federal projects still use the 16-division format (Div 15 Mechanical, Div 16 Electrical).
- Each section uses **CSI SectionFormat**: Part 1 – General (contains the **Submittals article**), Part 2 – Products, Part 3 – Execution.
- **Spec↔drawing↔submittal linkage**: specs define requirements with no graphic form; Part 2 product listings are "exactly what the contractor must prove they're providing during the submittal review process." Division 01 33 00 sets project-wide submittal rules; each technical section enumerates its required submittals.
- **Propagation**: spec revisions issue through addenda (pre-bid) or ASI/CCD/CO (post-award), and can generate new required submittals or substitution reviews.

### 7. Drawing revision management in detail
Version numbering conventions (per engineering CAD standards): lettered pre-IFC, sequential numbered post-IFC, restarting at Rev 0 at IFC. The title-block revision schedule records each delta with date and description. **Superseded vs current** is distinguished by version-set issuance date in platforms, and physically by removing superseded sheets from circulation and issuing a transmittal for the current set. US National CAD Standard sheet numbers = discipline designator (1–2 letters) + sheet-type digit + 2-digit sequence (A-101).

### 8. Submittals — review cycle and procurement gate
- **Cycle**: subcontractor prepares package → GC reviews for completeness/coordination → A/E reviews against contract documents → returns with a stamp.
- **Statuses** (liability-calibrated language): **No Exceptions Taken** (work may proceed), **Furnish/Approved as Noted** (minor comments, no resubmission), **Revise and Resubmit** (significant issues; must not release for fabrication), **Rejected** (redo). Per BuildSync (2026), roughly 35% of submittals are rejected on first review, at about $805 per rejection and adding 2–4 weeks to timelines; at that rate a 2,000-submittal project absorbs roughly 700 revise-and-resubmit cycles.
- **Procurement gate**: "Only after approval should materials be ordered or fabrication begin." "Once approved, submittals define exactly what will be fabricated, ordered, and installed. If something changes, it requires formal resubmittal or a change order." This gate is the single clearest engineering→procurement causal link.
- **Required-by-spec logic & register**: a submittal register is the master list pulled from the spec book before construction — Division 01 33 00 sets rules, each technical section's Part 1 Submittals article enumerates **Action Submittals** (require A/E response) vs **Informational Submittals** (retained for record, no action). Federal UFGS 01 33 00 defines a formally columned Submittal Register with an Activity Number tying each item to the schedule and classification codes "G" (Government approval) or "S." CSI provides standard forms (12.1A Transmittal, 12.1B/C Logs). Register row fields, consolidated across Procore, Oracle Contract Management, and UFGS: spec section, submittal number/revision, type, category (action/informational), responsible contractor/vendor, ball-in-court (Oracle: "Contract Management automatically fills in this field based on the review cycle"), lead time, required-on-site date, status, cost code, and linked commitment. Procore's Submittal Schedule Calculations work backward from the required-on-site date, factoring lead times and review periods, to compute when each submittal must be approved.

### 9. Field issues
- **Capture**: location-tagged photos, forms, punch items dropped on floor plans; QR codes; offline mobile sync. Distinct record types: **Observation/SOR** (early low-risk), **NCR** (confirmed non-compliance — failed test, rejected inspection), **Snag/Punch** (closeout), **Defect/DLP** (post-handover).
- **Escalation**: field observations "may lead to RFIs but do not replace them." A field report documents; an RFI formally requests clarification. Field issues carry location (site→building→level→zone→room) and discipline/trade, and can escalate to RFIs or change events.

### 10. Design-change taxonomy (real contract practice)
- **ASI (AIA G710)** — minor change; "cannot change contract sum or time" (per A201 §7.4); no owner signature.
- **PR / Bulletin** — request for pricing of a proposed change; flows into a CO.
- **CCD (AIA G714)** — directs work to proceed before price agreement; owner + architect signatures, not contractor's; must later be incorporated into a change order.
- **PCO / COR / Change Event** — the contractor-side early-warning and pricing chain: a **PCO** is the internal flag that a cost-impacting issue exists; a **COR** is the formal priced proposal to the owner; the **Change Order (AIA G701)** is the executed three-party amendment. Change reasons in real systems: Client Request, Design Development, Allowance, Existing Condition, Back Charge.
- **Addenda** modify procurement/bid documents pre-bid; CO/CCD/ASI modify contract documents post-award.

### 11. Approval workflows
- **Submittal/RFI**: ball-in-court chains model multi-step routing; permission levels (Admin/Standard/Read-Only + granular "Act as RFI Manager") govern who may act.
- **Change authority ladder**: ASI (architect alone) → CCD (owner + architect) → Change Order (owner + architect + contractor, three-way binding). Owner reserves right to reject substitutions even if the architect accepts.
- **Multi-tier financial configuration**: real systems support 1-, 2-, or 3-tier change configurations (Change Event → PCO → COR → PCCO), with a Designated Reviewer per step.

### 12. Location hierarchy
Modern platforms model an **unlimited-tier location tree** (typical 3–5 tiers): Site/Campus → Building → Level/Floor → Zone/Area → Room/Grid-line. Locations can be manually created, imported, or auto-generated from drawings or Revit levels/rooms. Any item (RFI, submittal, punch item, change order) can be scoped to a multi-tier location, enabling heat-maps of where issues concentrate. This location dimension is what lets Downstream localize a change's physical scope and correlate it with location-scoped procurement.

### 13. Disciplines as a first-class dimension
Disciplines (Architectural A, Structural S, Mechanical M, Electrical E, Plumbing P, Civil C, Fire Protection F, plus Landscape, Interiors, Telecom, Equipment) are encoded in **US National CAD Standard discipline designators** on every sheet and carry through to specs (MasterFormat divisions), RFIs, and submittals. Cross-discipline coordination is represented by **clash items** in the federated BIM model: **hard clashes** (physical overlap, e.g., duct through beam), **soft/clearance clashes** (maintenance access), and **workflow/4D clashes** (sequencing conflicts). MEP-FP disciplines occupy the contested ceiling plenum, making cross-discipline clash the primary coordination-failure locus.

### 14. Which changes most cause downstream commercial problems
Ranked by frequency/severity in the sources:
- **MEP coordination clashes** — Helonic's 2025 "MEP Coordination Best Practices" states MEP conflicts "account for 40% of all construction RFIs and are the leading cause of rework in commercial and institutional buildings," with an average field-resolved MEP clash costing $4,200 "not including the schedule impact of stopping work, issuing an RFI, and waiting for a redesign." MEP systems represent roughly 20–40% of total commercial construction cost (higher in hospitals and data centers).
- **Design/coordination errors generally** — the Construction Industry Institute's field-rework research puts direct field rework at about 5% of project cost (2–20% range, 90th percentile ~12.4%); CII's 1989 study of nine industrial projects found design-error rework contributed an average of 79% of total rework cost, and its field-rework studies rank owner/client changes (~33%) and design errors/omissions (~28%) as the top cost shares. A separate 2024 study of one Indonesian contractor (127 practitioners) attributed 56.5% of cost overruns and 40% of delays to design changes.
- **Late design changes after fabrication** — "Changes issued after fabrication has begun are among the costliest sources of rebar waste. Pre-fabricated cages or cut bars must be discarded or reworked." Per Strand & Co, rebar wastage typically runs 5–15% of material ordered (reducible to 3–5% with disciplined detailing); structural revisions affecting embeds force epoxy-anchor rework or embed replacement.
- **Spec substitutions** — governed by Section 01 25 00; a substitution changes the product, vendor, warranty, and lead time and must be evaluated for schedule and compatibility impact.
- **RFI responses that escalate** into ASI/CCD/CO, especially when a trade is already mobilized or material already ordered.

### 15. Highest-value inputs for commercial reasoning
The fields that most reliably predict PO/vendor/delivery impact:
- **Submittal**: `spec_section` (ties to procured scope), `submittal_type` (shop drawing/product data/sample), `status` (the fabrication gate), `required_on_site_date`, `lead_time`, `linked cost_code`/`commitment`, ball-in-court. A status flip to "Revise and Resubmit" on a long-lead item is the strongest single predictor of delivery risk.
- **DrawingVersion**: revision-cloud/delta scope (what changed), `discipline`, `location_refs`, issuance date, supersession link. A structural or MEP revision touching a location with mobilized trades or fabricated material is high-risk.
- **RFI**: `cost_impact` flag (Yes / Yes-unknown / No), `cost_code`, referenced spec sections and drawings, and whether the response spawned an ASI/CCD.
- **DesignChange**: change_reason, affected cost codes, linked commitments/vendors, schedule-impact days.
- **Cross-cutting**: `spec_section` + `lead_time` + `required_on_site_date` together let the engine compute whether an approval/revision slip breaches a delivery window; `location` + `discipline` scope which POs/vendors are implicated.

### 16. The ideal Reference Engineering System (synthesized design)

**Entities and key fields:**
- **Project** {id, name, location_tree_root, disciplines[], spec_format(MF2020/MF16)}
- **Discipline** {code (A/S/M/E/P/C/F/…), name}
- **Location** {id, tier_level, parent_id, name, type(site/building/level/zone/room/gridline)} — recursive tree, unlimited tiers.
- **SpecDivision / SpecSection** {number (e.g., 23 05 00), title, division, part1_submittals[], required_submittal_defs[], substitution_policy}
- **Drawing (Sheet)** {sheet_number (A-101), title, discipline, current_version_id, location_refs[]}
- **DrawingVersion** {version_id, revision_label (Rev A/0/1), issuance_date, status, revision_clouds[](area+delta+description), superseded_by_id, discipline, location_refs[]}
- **RFI** {number, question, references(drawing_versions[], spec_sections[]), location_refs[], discipline, ball_in_court, status, cost_impact_flag, cost_code, response, spawned_change_id}
- **Submittal** {number, rev, spec_section, type(shop_drawing/product_data/sample), category(action/informational), status, ball_in_court, required_on_site_date, lead_time, cost_code, linked_commitment, submitter/vendor}
- **DesignChange** (supertype) with subtypes **ASI, Bulletin/PR, CCD, ChangeOrder** {number, type, change_reason, affects(drawing_versions[], spec_sections[]), cost_impact, schedule_impact_days, approvals[], authority_level}
- **ChangeEvent / PCO / COR** {id, source(rfi/field_issue/clash/directive), cost_code, rom_cost, linked_commitment, status}
- **FieldIssue / Observation** {id, type(SOR/NCR/punch/defect), photos[], location_refs[], discipline, escalated_to_rfi_id, status}
- **ClashItem** {id, type(hard/soft/workflow), disciplines_involved[], location, model_refs[], generated_rfi_id, status}
- **Transmittal** {id, issued_date, recipients[], sheet_versions[], purpose}
- **ScheduleActivity** {id, wbs, activity_code, type(task/milestone/procurement), predecessors[], successors[], linked_submittals[], delivery_milestone} — mirroring Primavera's WBS + activity-code structure and the procurement activity chain (Submittal → Approval → PO → Fabrication → Delivery); Oracle Contract Management links submittal-review activities to schedule activities via a Successor Activity + Lead Time field.
- **ModelObject** {id, discipline, location, appearance_profile, resource_link} — mirroring the SYNCHRO pattern where a 3D object links to a schedule task through a **Resource** intermediary carrying an **appearance profile** (Install / Maintain / Neutral / Remove / Temporary).
- **Commitment / PurchaseOrder** {id, vendor, spec_scope, cost_code, line_items[], delivery_date} and **Vendor** {id, name, supplied_scope[]}.

**Relationships (typed edges):** REFERENCES, REQUIRED_BY, SUPERSEDES, RESPONDS_TO, TRIGGERS/GENERATES, GATES, AFFECTS, PROCURED_UNDER, SUPPLIED_BY, LOCATED_AT, IN_DISCIPLINE, SCHEDULED_WITH, DELIVERS.

**State machines:**
- **DrawingVersion**: Draft → Issued (IFC) → Revised(clouded) → Superseded.
- **RFI**: Draft → Open(BIC=assignee) → Responded(BIC=manager) → Closed [→ spawns ASI/CCD/CE].
- **Submittal**: Required(from register) → Prepared → GC-Review → A/E-Review → {No Exceptions Taken → FabricationReleased | Furnish as Noted | Revise&Resubmit → (loop) | Rejected} → Closed.
- **DesignChange**: Proposed → Priced(PCO/COR) → Directed(CCD)/Instructed(ASI) → Executed(CO) → Incorporated(drawing/spec revised).
- **FieldIssue**: Open → Escalated(RFI/CE) or Corrected → Verified → Closed.
- **ScheduleActivity (procurement)**: Submittal → Approval → PO → Fabrication → Delivery.

This model is deliberately synthesized from common patterns — Procore's ball-in-court, change-event/PCO/COR chain, and multi-tier locations; ACC/Forma's issuance-date-driven current-version logic and sheet/version model; SYNCHRO's object→resource→task appearance-profile linkage; Primavera's WBS/activity-code and procurement-activity structure; and CSI/AIA/ConsensusDocs contract practice for spec sections, submittal registers, and the ASI/CCD/CO change taxonomy — so it is faithful to how enterprise engineering platforms work without cloning any one proprietary schema.

## Recommendations
1. **Build the trigger layer first around the four highest-yield events** — RFI responses, drawing revisions (with cloud/delta scope), submittal status changes, and spec substitutions — because these carry the clearest, best-documented causal paths to procurement. Wire each to `spec_section`, `location_refs`, `discipline`, and `cost_code` from day one.
2. **Treat the submittal-status transition as the primary procurement gate.** Model the full status set and make "Revise and Resubmit" / "Rejected" on any submittal whose `lead_time` exceeds the days remaining to its `required_on_site_date` an automatic high-severity Commercial Event. This is the single most defensible engineering→delivery inference.
3. **Encode supersession and current-version-by-issuance-date explicitly**, so the engine never reasons off a stale sheet — reproduce the ACC/Forma rule and always keep the superseded-by pointer.
4. **Model the location tree and discipline as first-class, queryable dimensions** to scope which POs/vendors a change touches; auto-generate locations from drawings as Procore does.
5. **Represent the change chain (ChangeEvent→PCO→COR→CO) and the ASI/CCD/CO authority ladder** so Downstream can distinguish a no-cost ASI from a cost-and-schedule CCD/CO and set impact severity accordingly.
6. **Link ScheduleActivity procurement chains (Submittal→Approval→PO→Fabrication→Delivery)** using the Primavera/Oracle Contract Management pattern (Successor Activity + Lead Time), so a delayed approval visibly consumes float against a delivery milestone.

**Benchmarks that would change the design:** if validation shows structural/embed revisions (not MEP) dominate a target customer's rework, elevate DrawingVersion + fabrication-status modeling over clash modeling; if a customer runs pure design-build with model-based coordination, prioritize the ClashItem→RFI path and SYNCHRO-style model-object linkage over 2D sheet supersession.

## Caveats
- Several quantitative figures come from industry/vendor and single-study sources rather than an authoritative census; they are directionally consistent across independent sources but should be treated as indicative. Specifically: the "40% of RFIs are MEP" and "$4,200 average MEP clash" figures trace to a single vendor guide (Helonic, 2025); the CII rework percentages come from field-rework research of varying vintage (including a 1989 industrial-project study) and describe cost *shares* of rework, not project cost; and the "56.5% of cost overruns from design changes" figure derives from one 2024 study of a single Indonesian contractor (127 practitioners) and may not generalize. The earlier-circulated "52% of rework from design coordination errors" and "MEP is 40–60% of construction cost" claims appear overstated relative to primary sources and have been corrected here (MEP ≈ 20–40% of cost).
- Terminology varies by vendor and region: "bulletin," "field order," and "PR" are used interchangeably with or in lieu of ASI/proposal-request depending on the firm; change-tier configurations (1/2/3-tier) and status labels differ across Procore, ACC, and others. The model uses the most common vendor-neutral terms.
- SYNCHRO's native task/appearance behaviors are Install / Maintain / Neutral / Remove / Temporary (five profiles); the "Construct/Demolish" phrasing reflects Navisworks TimeLiner conventions — the model abstracts both into a generic `appearance_profile` field. In SYNCHRO the 3D object is not linked directly to a task but through a Resource intermediary (equipment/human/location/material), a nuance the ModelObject entity preserves via `resource_link`.
- This is a domain/state model only; per scope, it deliberately excludes API, integration, authentication, and UI concerns.