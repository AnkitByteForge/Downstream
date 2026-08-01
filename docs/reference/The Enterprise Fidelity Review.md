# Building a Credible Reference Engineering System: How Modern Construction Engineering Platforms Actually Work

## TL;DR
- **Build Submittals next, and build them as a procurement-gating state machine, not a document tracker** — the submittal review status ("No Exceptions Taken" → fabrication/procurement may proceed; "Revise and Resubmit"/"Rejected" → it may not) is the single most authentic, best-documented mechanism by which an engineering event controls a purchase order, making it the highest-value addition to the RES and the natural anchor of the Downstream demo.
- **The most believable procurement-impact scenario is a design change (ASI/PCO) that supersedes a drawing revision and invalidates an already-"No Exceptions Taken" equipment submittal on a long-lead item** — the prior research's HVAC-upsizing-drives-electrical-switchgear scenario is validated and is strong precisely because switchgear and transformers have documented lead times measured in *many months to years* (medium-voltage switchgear averaging roughly 44 weeks, power transformers roughly 128 weeks) and large committed costs; it should be refined to route through the submittal + design-change entities the RES is about to build.
- **Entities link through explicit, deterministic identifiers** — spec section (CSI MasterFormat, e.g., "23 31 13"), drawing sheet number + revision, and location codes are the real join keys; the RES should model these as first-class reference fields, and Downstream's impact inference should treat spec-section and drawing-number citations as the deterministic edges and discipline/location adjacency as the fuzzy edges.

## Key Findings

**1. The submittal is the procurement chokepoint, and its vocabulary is contractual.** Across vendor docs and industry practice, the review-status words are chosen for liability reasons and directly gate money. Per Procore Support's default-responses page, "REJECTED indicates that the submittal is not in compliance with the contract documents and work may NOT proceed on the submittal," and "REVISE AND RESUBMIT… work may NOT proceed until a revision of the submittal is resubmitted"; conversely "No Exceptions Taken" means fabrication/procurement may proceed. This is DOCUMENTED BEHAVIOR (Law Insider, LA City Bureau of Engineering, Procore, CSI-aligned sources). Procore provides **nine (9) default submittal responses** and lets customers **create up to twelve (12) custom responses for six (6) of the eight (8)** configurable defaults (PENDING and SUBMITTED are limited to one custom response each) — meaning the status vocabulary must be configurable, not hard-coded.

**2. Ball-in-court is the universal routing primitive.** RFIs, Submittals, and multi-tier approvals in Procore, Trimble Viewpoint/ProjectSight, and Primavera Unifier all express "who holds this now" as ball-in-court. RFI states reduce to Open → Answered → Closed, with only the GC able to close in Procore. This is DOCUMENTED BEHAVIOR.

**3. Field issues form a severity ladder that escalates upward into design/procurement.** Observation → NCR (Non-Conformance Report) → Punch/Snag → Defect, distinguished by timing and contractual weight. An NCR can escalate to an RFI (needs engineering judgment) which can trigger an ASI/PCO which can supersede a drawing and invalidate a submittal. This is DOCUMENTED BEHAVIOR for the definitions; the full escalation chain is INFERENCE built from consistent multi-source patterns.

**4. Design changes follow a documented authority ladder.** RFI → ASI (architect only, no cost/time change) → PR/PCO (pricing a proposed change) → CCD (owner+architect, work proceeds before price agreement) → Change Order (all three parties sign). AIA Document G701™–2017 is the standard change-order form; per aiacontracts.com it is executed "when the Owner and Contractor, in concurrence with the Architect, have reached agreement on the change… including any adjustments in the Contract Sum" (i.e., it requires owner, contractor, and architect signatures). G701 also states verbatim that it "does not include adjustments to the Contract Sum… or Contract Time, that have been authorized by Construction Change Directive until the cost and time have been agreed upon by both the Owner and Contractor, in which case a Change Order is executed to supersede the Construction Change Directive." This authority ladder is exactly what determines whether an engineering change has procurement teeth. DOCUMENTED BEHAVIOR (AIA Contract Documents, Procore, Minnesota State CO.40).

**5. Links are deterministic via spec section, drawing number, and location.** CSI MasterFormat gives every requirement a fixed six-digit address used across RFIs, submittals, POs, and change orders. Primavera Unifier's RFI business process explicitly carries "Reference Contract Documents, Area, or Spec Section" fields. This is DOCUMENTED BEHAVIOR and is the backbone of the RELATIONSHIPS model.

**6. Enterprise UX converges on a small set of patterns** — persistent left-nav tool list, dense filterable logs with a "ball-in-court/assigned-to" column, a "current set" drawing view that hides superseded revisions, side-by-side revision compare, and a per-record activity feed. Each satisfies a specific workflow need (see Details).

**7. Truly complete public document sets (drawings + specs + RFIs + submittals + revisions together) essentially do not exist in the open** — RFIs and submittals live in gated PM systems. The best freely-downloadable approximation is a public-agency bid package with drawings + CSI specs + addenda (the open-web equivalent of "revision history").

## Details

### Area 1 — Core Engineering Workflows

**Who works where, all day vs. periodically** (DOCUMENTED + INFERENCE):
- The **project engineer** is the day-to-day owner of the RFI log and submittal log; they review submittals before the architect sees them, manage the RFI cycle, and distribute responses (DOCUMENTED — Virtual Construction Assistants; corroborated by Procore training guidance that a PE walks an RFI "from creation to closeout").
- **Document control** handles drawing revisions, filing, and transmittals on larger projects; the **superintendent/field engineer** is responsible for building from *current* documents (DOCUMENTED). The single most common failure is multiple versions circulating with no clear "current" marker — which is exactly why the RES's existing "current version" marker is realistic and important.
- **Stays open all day / checked constantly:** the drawing viewer/current set, the RFI log, and the submittal log — these are the "heartbeat" screens (Procore describes RFIs as "the heartbeat of construction communication"). **Checked periodically:** inspections, daily logs, the activity feed, and dashboards (reviewed at weekly project meetings, where "both the RFI log and the submittal log" are walked). This is INFERENCE from documented role descriptions.
- **BIM/VDC coordinators** live in a model-plus-issue-tracker environment (Revizto, ACC Model Coordination) rather than the RFI/submittal logs; their output (clash → coordination issue) feeds RFIs. DOCUMENTED (Revizto, ACC).

**How the entities trigger each other** (DOCUMENTED relationships, INFERENCE for the full chain):
- Submittals and RFIs intertwine: while a sub prepares a submittal, questions arise → RFI to the design team; "in a perfect world all RFIs are resolved before any submittals are produced… but in reality, submittals might reveal new questions" (DOCUMENTED — Procore).
- RFI answer that changes the work → "the change management process starts from here" (DOCUMENTED — Archdesk). RFI → ASI or PR → CCD/CO (DOCUMENTED — AIA, Minnesota State).
- Field inspection failure → observation; in Procore the best practice is to "create an observation from the non-conforming line item" (DOCUMENTED). Observation/NCR that needs engineering judgment → RFI (DOCUMENTED — multiple QA sources: "If a problem requires engineering judgment or customer approval, it's a non-conformance, not a punch list item").
- Design bulletin/ASI → new drawing revision issued → prior revision superseded → any submittal keyed to the old drawing is now suspect. This full chain is INFERENCE assembled from documented single links.

### Area 2 — Domain Model

**Essential entities (must exist for credibility):** Project, Drawing, DrawingVersion/Revision, Drawing Set / Area, Specification (Section), RFI, Submittal, Submittal Item, Field Issue/Observation, Inspection, Design Change (ASI/PCO/CCD/CO family), Company/Contact/Directory, Location (tiered), and the linking/webhook/activity infrastructure the RES already has. (DOCUMENTED — these are exactly the Procore project-level tools and the ProjectSight record-type list: "Drawings, Specifications, Submittals, RFIs, Checklists, Action items, Daily reports, Field work directives, Issues, Notices to comply, Punch items, Safety notices, Submittal packages.")

**Optional / nice-to-have:** Meeting Minutes, Transmittals, Daily Logs, Punch List as a distinct entity, Photos, Correspondence (Procore models ASI/CCD as configurable "Correspondence types"), Schedule/activities.

**Which entities + fields create downstream PROCUREMENT impact** (this is the core of the Downstream thesis; DOCUMENTED where cited, otherwise labeled):
- **Submittal.review_status** — the highest-impact field in the entire model. "No Exceptions Taken" releases procurement/fabrication; a later change to "Revise and Resubmit"/"Rejected" invalidates it (DOCUMENTED).
- **Submittal.spec_section** and **Submittal.linked_drawings** — if the referenced spec or drawing changes, the submittal (and any PO placed against it) is at risk (DOCUMENTED linkage; procurement consequence is INFERENCE).
- **DrawingVersion.status / supersession** — when a sheet is superseded by a revision that changes a dimension, equipment tag, or capacity, any commitment based on the old sheet is exposed (INFERENCE from documented supersession behavior).
- **Design Change (ASI/CCD/CO).scope** — a change that alters equipment size, material, or quantity is the direct procurement-invalidation trigger; only CO/CCD can actually modify the contract (DOCUMENTED).
- **Field Issue/NCR** on installed or on-order material → quarantine/rework, potentially re-order (DOCUMENTED containment behavior).
- Fields that specifically matter for a PO: equipment tag/mark, model/manufacturer, capacity/size (tonnage, ampacity, kVA), dimensions, quantity, and finish — these are the attributes a "Revise and Resubmit" or drawing revision most often changes (INFERENCE, strongly supported by the AHU-curb-dimension and switchgear-upsize examples in the sources).

### Area 3 — Lifecycle (documented state machines)

- **Drawing revision** (DOCUMENTED — Procore): revisions stack under a drawing number; the version with the latest Drawing Date sits at top and is the **current version**; older ones become **obsolete/superseded** but remain in "All Sets and Revisions." "Current" is determined by drawing date/order, not a manual flag, and can be reordered by drag-and-drop. The RES's supersession pointer + current-version marker already matches this.
- **RFI** (DOCUMENTED — Procore, Archdesk, Trimble): Draft → Open (ball-in-court routes among assignees) → Answered → Closed (GC/RFI-manager only closes). "Answered" ≠ "Closed": an answer nobody has actioned is still a live risk.
- **Submittal** (DOCUMENTED): Pending/Draft → Submitted → Under Review (ball-in-court) → response applied. Response vocabulary (nine Procore defaults, configurable): Approved / No Exceptions Taken, Approved as Noted / Furnish as Noted / Make Corrections Noted, Revise and Resubmit, Rejected, and non-review outcomes (Pending, Submitted, For Record Only, Void). Gate: only "No Exceptions Taken"/"Furnish as Noted"/"Make Corrections Noted" release procurement/fabrication; "Revise and Resubmit" and "Rejected" block it (verbatim Procore language above).
- **Field issue** (DOCUMENTED definitions; escalation INFERENCE): Observation (SOR) → NCR (formal, root-cause, containment, corrective action, closure) → Punch/Snag (near completion) → Defect (post-handover/DLP). Procore Observation states include "Initiated" → response → closed.
- **Design change** (DOCUMENTED — AIA authority ladder): RFI → ASI (architect only, no cost/time) → PR/PCO (pricing) → CCD (owner+architect, proceed before agreement) → CO (all three sign; G701™–2017). CCD unresolved → Claim under AIA A201 Article 15.
- **Approval chains** (DOCUMENTED — Procore, ProjectSight, Unifier): multi-step, each step has an assignee/ball-in-court, step due dates auto-set from workflow template; items lock once closed to preserve record integrity.

### Area 4 — Relationships (deterministic vs. fuzzy)

**Deterministic / explicit** (DOCUMENTED):
- **Spec section (CSI MasterFormat, six-digit, e.g., "23 31 13" HVAC Ducts / "26" Electrical)** — the fixed "address" tagged onto RFIs, submittals, POs, and change orders. Submittal registers are literally built by extracting requirements from the spec (Division 01 Section 01 33 00 Submittal Procedures + each technical section).
- **Drawing number + revision** — RFI logs cite "drawing numbers with revisions, specification sections" as linked documents.
- **Location / tiered location code** — Procore's tiered locations link Drawings, Documents, RFIs, Submittals to a jobsite location; inspections/observations carry location. Unifier RFI carries "Area."
- **Ball-in-court / assignee** — links a record to a Contact/Company.
- **Explicit parent/child** — Submittal → Submittal Package; Observation ← Inspection (Procore stores a link to the originating inspection in the observation's "Origin" field); Unifier RFI "might create… Change Request, Issue, Risk."

**Inferred / fuzzy** (INFERENCE): discipline adjacency (an HVAC change implying an electrical impact with no explicit citation), location adjacency (work in the same room/grid), and trade coordination overlaps. These carry no explicit foreign key and are exactly where Downstream's inference layer earns its value — and where it must express confidence rather than certainty.

### Area 5 — Enterprise UX (comparative, with the "why")

| Pattern | Procore | ACC (Autodesk/Forma) | Primavera P6/Unifier | ProjectSight | Revizto | Why users expect it |
|---|---|---|---|---|---|---|
| Navigation | Persistent left-nav tool list per project | Unified module switcher; design+build in one | Unifier: BP "logs" under navigator nodes (RFI Manager, Submittals) | Left-nav record-type list; project home with recent-drawings carousel | 2D/3D unified workspace, issue tracker panel | Tool-based mental model matches how the team divides labor by role |
| Info density | Dense logs, many columns, ball-in-court | Dense + Construction IQ risk flags | Very dense, enterprise/tabular | Cleaner, field-first, free tier | Issue list synced to spatial coordinate | Logs are management tools; the assigned-to + due-date columns turn a list into accountability |
| Dashboards | Pre-built dashboards, project overview line-items per tool | Construction IQ predictive analytics | Portfolio/program controls | Project home + status tiles | Charts/dashboards + BI API | Leaders need aging/overdue at a glance, not per-record |
| Drawing/doc viewer | Current-set view; OCR; compare revisions (removed items in red) | First-class sheet viewer, model-linked | Document Manager folder tree | Split-screen viewer, 360° walkthrough→drawing | Game-engine 2D/3D, reference-point align | Field must trust it's the current sheet; compare answers "what changed?" |
| Revision history | "All Sets and Revisions" report; drag-reorder; version list | Version sets | Document Manager versions | Drawing revision list | Model version | Auditability + defensible record for claims |
| Activity feed | Per-record activity feed + comments; email-to-respond | Activity + @mentions | BP workflow history | Per-record notifications/comments | Issue comment thread | Every handoff is a place work can stall; the feed is the audit trail |
| Filtering | Filter/search per log; discipline filter on drawings | Filter + saved views | Log filters | Filters per record list | Filter/group clashes→issues | Reviewers need "the 10 that matter, not all 40" |

Key UX principles the RES should honor (OPINION grounded in the above): (a) a **"current" view that hides superseded items by default** with an explicit "all revisions" escape hatch; (b) an **assigned-to/ball-in-court column** as a first-class, filterable column on every log; (c) a **compare-revisions affordance**; (d) a **per-record activity feed** (the RES already has this via the webhook log — good); (e) **overdue/aging visibility** at the log level.

### Area 6 — Real construction documents (best seed data)

The honest finding: a single, freely-downloadable package containing drawings + specs + RFIs + submittals + revision history for one building **does not exist in the open** — RFIs and submittals almost always live behind login in Procore/ACC. The realistic target is drawings + CSI specs + **addenda** (the open-web stand-in for revision history).

**Recommendation: the Missouri Office of Administration – Facilities Management, Design & Construction (FMDC) "Bid Listing / Electronic Plans" portal** (oa.mo.gov/facilities/bid-opportunities/bid-listing-electronic-plans) is the best confirmed source. It posts, together for one identifiable vertical government building, downloadable **plans + CSI-organized specifications/Project Manual + addenda + bid tabs/award** as free PDFs with no login. The portal text confirms: "downloadable plans, specifications, Invitation for Bid, bid tabulation, award, addenda." A confirmed example is a Department of Corrections MEP/structural project (portal project C2516-01) with a posted Addendum No. 1, whose scope ("addition of packaged rooftop units… modifications to electrical systems… addition of structural supports… full replacement of fire alarm systems") is ideal because it naturally contains the HVAC-plus-electrical interaction the demo needs.

**Why over alternatives:**
- *University of Alabama constructionpublicinfo.ua.edu* — drawings/specs are "EXAMINATION ONLY" at a plan room or paid print sets ("$250 PER SET"); only front-end/CSI template docs (Instructions to Bidders 002113, a Procore SOP spec, Closeout 01 78 00) are downloadable. Excellent for realistic spec/front-end *templates*, not a full set.
- *GSA* — drawings/specs gated behind SAM.gov registration ("You'll need to register on SAM.gov to obtain access to drawings and specifications"); only reference docs like P100 are open.
- *TxDOT Plans Online* — genuinely free and complete ("Download and print letting plans, proposals, addenda and contract plans… this is a free service"; plan set + proposal + addenda + bid tabs) but highway/transportation, lacking CSI specs and vertical-building architectural/MEP sheets.
- *Iowa State University FPM* (plans.print.iastate.edu) — cleanest UX, each project exposes Drawings + Project Manual + Advertisement as direct Box PDFs with no login (e.g., "Pearson Hall – Rooms 1116 and 1138 Remodel"); downside is current projects are small interior remodels.

Practical caveat: the Missouri portal is a live rotating table, so a chosen project should be downloaded and archived promptly, because specific project numbers rotate off as bidding closes.

### Area 7 — Demo realism (procurement-impact scenario)

**Validated and refined.** The prior research's late-HVAC-upsizing-drives-electrical-switchgear scenario is authentic and well-supported — and, if anything, *more* compelling than the earlier figures suggested, because equipment lead times are extreme:
- Per Wood Mackenzie's Q2 2025 T&D supply-chain survey (cited via VAWN's Electrical Equipment Lead Time Index, 2026), **medium-voltage switchgear averages roughly 44 weeks and low-voltage switchgear roughly 54 weeks**. Per the same survey (POWER Magazine, "Transformers in 2026," IndustrialSage), **standard power transformers average about 128 weeks and generator step-up transformers about 144 weeks**, with some specialized orders extending to four years and power-transformer prices up 77% since 2019. A late upsize that pushes service gear + feeder is described in industry sources as a "$40,000 to $90,000 change-order between service gear upsize and feeder upsize," with premium-freight/expediting exposure and downstream trade stacking when an order date slips.
- The mechanism is real and directly documented: the AHU example in the sources ("No Exceptions Taken"… unit dimensions don't fit the curb… "$40,000 in modifications and a four-week delay") shows exactly how an approved submittal becomes wrong when a drawing/spec detail changes.

**Recommended refined demo flow (routes through the entities the RES is about to build):**
1. HVAC equipment schedule on a mechanical drawing is revised (larger RTU/AHU) via an **ASI/PCO** (design change) → new **DrawingVersion** issued, prior revision **superseded**.
2. The larger unit's electrical load (MCA/MOCP) now exceeds the feeder/switchgear shown on the electrical sheet (deterministic link via **spec section 26 / electrical drawing number**, plus **discipline-adjacency inference** M→E).
3. An **electrical-switchgear Submittal** previously marked **"No Exceptions Taken"** (with a PO already placed on a long-lead item) is now invalidated → status must move to **Revise and Resubmit** → the PO/commitment is exposed. Because the underlying gear runs ~44+ weeks, the slip lands squarely on the critical path.
4. Downstream detects and quantifies the procurement impact (lead-time slip + restocking/expediting exposure).

This is more convincing than a pure field-issue scenario because it exercises the *design-change → drawing-supersession → submittal-invalidation → PO* chain end-to-end, which is the story the whole RES exists to tell. (OPINION, grounded in DOCUMENTED lead-time and change-order-cost sources.)

Two credible alternatives to keep in reserve (OPINION): (a) a structural-steel connection RFI answer that changes an embed/anchor-bolt layout after the steel package PO is placed; (b) a "Revise and Resubmit" on a long-lead curtainwall/glazing submittal (documented 20–36 week award-to-install timeline) driven by a spec addendum.

### Area 8 — Gap analysis (tiered feature list with reasoning)

**MUST HAVE (required for a credible reference platform and the Downstream demo):**
- **Submittals + Submittal Items + Packages** with a configurable **review-status state machine** and an explicit **procurement-release gate** on "No Exceptions Taken"/"Furnish as Noted." *Reason:* this is the single most authentic engineering→procurement control mechanism (DOCUMENTED) and the RES currently lacks it.
- **Ball-in-court / assignee** as a first-class, filterable field on RFIs, Submittals, and any approval workflow, with multi-step routing. *Reason:* universal primitive across all five platforms.
- **Design Change entity family (ASI / PCO / CCD / Change Order)** with the documented authority ladder and a link back to the triggering RFI and forward to superseded drawings. *Reason:* only CO/CCD actually modify the contract; this is where procurement impact becomes real.
- **Deterministic reference fields** everywhere: spec_section (CSI), drawing_number+revision, location code. *Reason:* these are the real join keys and the deterministic edges Downstream needs.
- **Specifications as a first-class browsable entity** organized by CSI MasterFormat. *Reason:* submittal registers and RFIs are built from specs; ProjectSight and Procore both treat Specifications as a top-level tool.
- **Field Issues / Observations** with the Observation→NCR distinction and an **escalate-to-RFI** action. *Reason:* documented field-to-design escalation path feeding the change engine.

**SHOULD HAVE:**
- **Inspections** with pass/fail/N/A line items and **create-observation-on-deficiency**. *Reason:* documented Procore behavior; closes the QA→field-issue loop.
- **Cross-entity relationship/linking UI** (the RES's biggest current gap) showing an RFI's linked drawing/spec/submittal and a record's forward/back references. *Reason:* the relationships are the product; users and Downstream both need them visible.
- **Compare-revisions view** for drawings and **overdue/aging** indicators on logs. *Reason:* documented, high-expectation UX patterns ("what changed?" and "the 10 that matter").
- **Submittal register derived from specs** and **long-lead flagging** on submittal/procurement schedule. *Reason:* documented practice tying submittals to the procurement schedule.

**NICE TO HAVE:**
- Transmittals, Meeting Minutes, Daily Logs, Punch List as a distinct entity, Photos, Correspondence as configurable types (ASI/CCD modeled this way in Procore).
- BIM/model-coordination issue tracker (Revizto/ACC style) and clash→issue→RFI conversion.
- Predictive/analytics dashboard (ACC "Construction IQ" style) and portfolio roll-ups.
- Email-to-respond on RFIs/submittals (documented Procore/ProjectSight capability) — realistic but not essential to the harness.

## Recommendations

1. **Build Submittals first, as a state machine with a procurement-release gate.** Model the configurable response vocabulary (nine defaults, up to twelve custom on six of eight configurable defaults) and treat "No Exceptions Taken"/"Furnish as Noted"/"Make Corrections Noted" as procurement-releasing and "Revise and Resubmit"/"Rejected" as procurement-blocking. Emit a webhook on status transitions (mirroring the RFI-close pattern already built). *Benchmark to proceed to the next stage:* a submittal can move Submitted → Under Review (ball-in-court) → response, and a status change fires a webhook Downstream can consume.

2. **Add the Design Change family (ASI/PCO/CCD/CO) and wire the authority ladder**, with a link from a triggering RFI and a pointer to the drawing revision it causes. *Threshold that changes the plan:* if time-boxed, ship ASI + a generic "Change Order" first and defer CCD/PCO nuance — the demo needs "a design change superseded a drawing and invalidated a submittal," which ASI+CO alone can carry.

3. **Promote Specifications to a first-class CSI-indexed entity and make spec_section / drawing_number / location first-class reference fields on RFIs, Submittals, Field Issues, and Design Changes.** *Reason/benchmark:* this is what lets Downstream distinguish deterministic edges (explicit spec/drawing citations) from fuzzy edges (discipline/location adjacency). Ship deterministic links before investing in inference UI.

4. **Build the cross-entity relationship/linking UI** so each record shows its forward/back references. This is the RES's largest current gap and the relationships are the whole point of the platform.

5. **Add Field Issues (Observation vs. NCR) with an escalate-to-RFI action, then Inspections with create-observation-on-deficiency.** These close the field→design→procurement loop and are lower-risk than the change engine.

6. **Wire the refined demo scenario end-to-end** (HVAC upsize ASI → mechanical drawing revision supersedes prior → electrical switchgear submittal flips to "Revise and Resubmit" → PO exposed) and **seed the RES from the Missouri FMDC document set** (download and archive a specific project promptly, since the portal rotates). Use Iowa State as a clean backup and TxDOT only if a transportation flavor is ever needed. Lean on the extreme documented equipment lead times (~44 weeks MV switchgear, ~128 weeks power transformers) to make the impact quantification feel authentic.

7. **Do not over-build.** Skip predictive analytics, BIM model coordination, and full CCD/PCO nuance until the core submittal-gate + design-change + linking chain is demonstrably driving Downstream impact detection.

## Caveats
- **Claim types are labeled inline** as DOCUMENTED / INFERENCE / OPINION per the methodology requirement. The status vocabularies, ball-in-court, drawing supersession, the AIA authority ladder, and CSI linking are DOCUMENTED. The *full* escalation chains (NCR→RFI→ASI→drawing→submittal→PO) are INFERENCE assembled from documented single links. Sequencing/feature-tier judgments are OPINION.
- **Vendor marketing bias:** comparative UX claims (e.g., "ACC Construction IQ flags risks before they escalate," "Procore is easier in the field") come partly from vendor and review-aggregator pages and should be read as positioning, not benchmarked fact.
- **Public document sets are time-sensitive and incomplete:** the Missouri FMDC portal is a live rotating table; RFIs and submittals are essentially never posted publicly, so any seed set will need synthetic RFIs/submittals layered onto real drawings+specs+addenda.
- **Procurement figures vary by source and reflect a stressed supply chain:** lead-time figures come from Wood Mackenzie's Q2 2025 T&D survey (as reported by POWER Magazine, IndustrialSage, and VAWN's 2026 index) and represent averages during an atypical constrained period — treat as order-of-magnitude and current-era, not permanent constants. Change-order dollar ranges come from individual contractor/industry sources, not a controlled dataset.
- **Terminology varies by contract:** submittal responses, NCR vs. defect vs. snag, and change-order naming (PCO/COR/CE) differ by owner, region, and contract form; the RES should treat these as configurable rather than canonical. Note a minor source inconsistency on Procore submittal-response counts (some Procore pages say "eight" defaults, the current default-responses page says "nine"); either way the operative design point is that the vocabulary is configurable.