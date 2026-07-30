# The Downstream Intelligence Specification
### Chief AI Architect brief · the reasoning model, not the software

This document specifies **how Downstream thinks** — nothing about services, APIs, databases, or libraries. It draws exclusively on the three frozen documents (the Reference Engineering System, the Reference Commercial System, and the Demo Strategy) and adds no new domain entities. Where it introduces a new *reasoning* concept not present in those documents — the `INSUFFICIENT_EVIDENCE` confidence tier, the orthogonality of confidence and severity — it is a refinement of how the existing entities are reasoned about, never a change to what they are.

---

## Section 1 — Product Mission

**What Downstream actually does:** it watches for an approved engineering design change, computes exactly which already-existing commercial commitments that change invalidates, and presents an evidence-backed, human-approvable action for each one — before the next irreversible commercial or fabrication event makes the mistake expensive.

**The problem it solves:** the gap between two systems of record that were never designed to talk to each other. The Reference Engineering System knows what changed. The Reference Commercial System knows what was bought. Neither has ever had to know about the other. The causal link — *this RFI, once answered, makes that purchase order wrong* — exists nowhere but in a human's head, and only for as long as that human happens to be looking at both systems at once. Downstream is that missing link, made durable and automatic.

**What it does NOT solve, explicitly:**
- It does not make engineering decisions. Structural adequacy, means-and-methods, and the technical correctness of a design change remain the responsibility of licensed engineers. Downstream reasons about the *commercial consequence* of a change already approved by the people whose job is to approve it.
- It does not adjudicate legal entitlement or quantum. Whether a change is compensable, whose fault it is, and what it is ultimately worth in a dispute is the claims/legal domain — a genuinely different, harder problem this system does not attempt.
- It does not replace either system of record. It is the synchronization layer between them, not a new place to author drawings or a new ledger of financial truth.
- It does not execute a financial or contractual transaction autonomously, under any confidence or severity condition. Ever.
- It does not forecast changes that have not yet happened. Downstream is reactive to changes that are already approved — a prospective "what might change" product is a different system.

**Why existing systems cannot solve this alone:** an engineering platform's data model has no field for "purchase order," and a commercial/ERP platform's data model has no field for "spec section." Each system faithfully represents its own half of reality. The moment a project runs more than a handful of concurrent changes against hundreds of live commitments, manual cross-referencing between the two halves stops scaling — not because either system is deficient at its own job, but because reconciling the two was never anyone's job to automate until now.

---

## Section 2 — Intelligence Philosophy

**Triggers, not documents.** A drawing sitting untouched on a server means nothing to Downstream. A drawing whose *state just changed* — revised, superseded, newly cross-referenced by an approved RFI — is the only thing that can possibly invalidate an existing commercial commitment. The document is inert; the **state transition** is the causal event. This is why the intelligence model listens for transitions, never indexes documents for their own sake.

**Relationships over files.** A purchase order in isolation and a drawing in isolation are both commercially meaningless. Impact is a property of the *relationship* between an engineering trigger and a commercial commitment — a shared cost code, a shared spec section, a shared physical location. The substrate the intelligence model reasons over is therefore the graph of typed relationships established by the two reference systems, not a document index or a similarity search.

**Why graph reasoning is required.** The question Downstream must answer — *does this RFI, which touches this spec section, which is the cost code for this PO line, supplied by this vendor, scheduled for this delivery window, currently sitting at this fabrication stage, matter?* — is inherently multi-hop. No single keyword match or document lookup answers it. Only a traversal that can walk the causal chain, hop by typed hop, and stop at a principled boundary, can.

**Why confidence must be evidence-based, never asserted.** The two systems being reconciled were never built to agree with each other, so exact certainty is often genuinely unavailable. The intelligence model must never manufacture false precision — a single invented percentage — in place of that honest uncertainty. Confidence is always a function of how much real, checkable graph support exists for a conclusion, never a model's self-reported plausibility.

**Why severity depends on lifecycle position.** The cost of correcting a mistake is not a function of how big the mistake is — it is a function of how far the affected commitment has *already traveled* through fabrication, shipping, and installation. A small change that reaches an already-shipped custom part is a bigger emergency than a large change that reaches a still-draft requisition. This is the construction-industry expression of the general principle that defects become exponentially more expensive the further downstream they are caught — which is also, not coincidentally, the source of the product's name.

**Why commercial reasoning must happen before financial loss, not after.** Downstream's only reason to exist is to compute impact *before* the next irreversible commercial event — a fabrication release, a shipment, an invoice — rather than to audit what already went wrong. Every part of this intelligence model is oriented around racing the commercial system's own next state transition, not reconciling against its history.

---

## Section 3 — Trigger Taxonomy

Ranked by business value, per the Demo Strategy's own findings on which changes most frequently and severely create commercial risk.

| Trigger | Source artifact | Trigger condition | Priority | Expected downstream impact | Always reason? |
|---|---|---|---|---|---|
| **Submittal Status Change** | Submittal | Status transitions to *Revise & Resubmit*, *Rejected*, or (inversely) *No Exceptions Taken* on a submittal whose scope has changed since the prior revision | Highest | This is literally the fabrication/procurement gate — a status flip here is the most direct, best-evidenced signal that a commercial commitment's basis has changed | Yes, always — this is the trigger the whole product is built around |
| **Drawing Revision** | DrawingVersion | A new version is issued (revision cloud/delta present) on a sheet referencing a discipline/location already tied to a live commitment | Very high | Direct physical scope change; the most common root cause behind the other triggers | Yes, but gated by an event-worthiness check (see below) |
| **Design Change (CCD / Change Order)** | DesignChange (CCD/ChangeOrder subtype) | A change carrying explicit cost/time authority is issued | Very high | Guaranteed commercial consequence by definition — a CCD/CO exists specifically because cost or schedule is affected | Yes, always |
| **Design Change (ASI)** | DesignChange (ASI subtype) | A minor instruction is issued with no stated cost/time change | Medium | Usually none, occasionally conceals a real impact if work has already proceeded on the old basis | No — reason only if the ASI's referenced scope matches an already-in-fabrication or shipped commitment |
| **RFI Response** | RFI | Status moves to Closed, especially where the response spawns an ASI/CCD | High | The most frequent upstream cause of the above two triggers; also independently informative (a response can reveal a scope conflict even without a formal change vehicle yet) | Yes, but only once Closed with a substantive response — not on every ball-in-court routing step |
| **Clash Resolution** | ClashItem | A hard/soft/workflow clash is resolved via rerouting, especially post-prefabrication | High | Concentrated, high-value MEP impact; frequently hits already-fabricated prefab spools/racks | Yes, always |
| **Specification Change** | SpecSection (revision) | A spec section is revised, especially a substitution changing product/vendor/lead time | High | Directly changes the cost-code join key's meaning — everything procured under that section is now suspect | Yes, always |
| **Field Issue Escalation** | FieldIssue/Observation | An observation escalates to an RFI or a design change | Medium | Indirect — value lies in early awareness, not a direct commercial hit | No — reason only once/if it escalates into one of the above; the raw field issue itself is too early to act on |
| **Location Change** | Location reassignment on a Drawing/RFI/Submittal | An artifact's location scope changes | Low-medium | Mostly relevant for re-scoping which commitments are physically adjacent | No — treat as a modifier to an already-firing trigger, not a trigger in its own right |
| **Schedule Change** | ScheduleActivity date shift | An activity date affecting a linked ProcurementScheduleItem moves | Medium | Can flip a delivery from "has float" to "critical," changing severity of an *existing* impact without any new engineering scope change | Yes, but as a severity re-evaluation trigger on already-open Impacts, not a new-Impact-creation trigger |

**The event-worthiness gate:** every trigger above passes through a lightweight relevance check before the expensive reasoning sequence runs — does it carry a spec/cost-code/location reference at all, and does that reference intersect anything already known to the graph? A typo-fix drawing revision with no clouded scope, for instance, never reaches full reasoning. This gate exists to protect the expensive stages below from being run on noise, not to second-guess the taxonomy above.

---

## Section 4 — Reasoning Pipeline

The sequence below describes the *reasoning content* of each stage, independent of which service executes it. Two stages — **Severity Calculation** and **Confidence Calculation** — are listed in this order because it mirrors how a human explains the result, but they are computed from **independent evidence** and neither is an input to the other's arithmetic; this orthogonality is explained fully at the start of Section 8 and is the single most important structural idea in this specification.

```
Trigger arrives
      ↓
Normalize
      ↓
Entity Resolution
      ↓
Graph Expansion
      ↓
Evidence Collection
      ↓
Commercial Mapping
      ↓
Impact Analysis
      ↓
Severity Calculation
      ↓
Confidence Calculation
      ↓
Recommendation Generation
      ↓
Human Approval Decision
      ↓
Synchronization
```

**Trigger arrives.** One of the taxonomy entries in Section 3 fires. Downstream knows only that a named artifact changed state — nothing about consequence yet.

**Normalize.** The raw artifact — a paragraph of RFI response text, a resubmitted equipment schedule, a revision cloud on a sheet — is reduced to the specific fields that matter: which spec section, which drawing/location, which discipline, what actually changed within it. This is where document intelligence operates: deciding what part of a messy real artifact *is* the semantically meaningful delta, as opposed to the surrounding boilerplate.

**Entity Resolution.** The normalized references are matched against known nodes in both reference systems — this specific SpecSection, this specific CostCode, this specific DrawingVersion — with an explicit match-quality score per candidate. Naming inconsistency (a spec section cited slightly differently than it's recorded) is absorbed here, honestly, by scoring the match rather than silently assuming it.

**Graph Expansion.** From the resolved entities, the graph is traversed outward (Section 5) to surface every candidate commercial artifact that could plausibly be affected — first-order (direct key matches) and second-order (structural/temporal/location dependencies).

**Evidence Collection.** For every candidate surfaced, the actual supporting artifacts are gathered — never synthesized, always a pointer to a real document or field (Section 6).

**Commercial Mapping.** Each engineering-side entity is joined to its Reference Commercial System counterpart — CostCode to Commitment/POLine, POLine to Vendor, POLine to its ProcurementScheduleItem — using the two frozen domain models' own defined join keys. This is the exact moment the two reference systems actually meet.

**Impact Analysis.** Each mapped commercial artifact is classified by *what kind* of impact this is — scope superseded, quantity conflict, delivery-date conflict, budget/commitment delta — not merely flagged as "affected." This classification is what later drives which recommendation category applies.

**Severity Calculation.** Section 8's business-reasoning model: how bad would this be, *if the link is real*, driven by lifecycle position, commercial exposure, and schedule criticality.

**Confidence Calculation.** Section 7's four-tier model: how sure are we the link *is* real, driven purely by evidence quality and graph support.

**Recommendation Generation.** Section 9: severity and confidence are combined — for the first time — to decide what category of action, if any, to draft.

**Human Approval Decision.** Section 10: a human reviews, edits, approves, or dismisses each recommendation individually.

**Synchronization.** Section 11: only an approved recommendation is ever dispatched outward, and only to the exact scope approved.

---

## Section 5 — Graph Traversal Strategy

**Starting node.** Always the entity the trigger most directly touches — a DrawingVersion for a drawing revision, an RFI for an RFI response, a Submittal for a submittal status change. Never a generic "search everything relevant" starting point; the traversal always has one precise origin.

**First hop — establish identity, not consequence.** From the starting node, traverse `REFERENCES`/`REQUIRED_BY` to SpecSection, `LOCATED_AT` to Location, `IN_DISCIPLINE` to Discipline. This hop answers *what is this change actually about* before any search for consequence begins. Reasoning about impact before establishing identity is how false positives get manufactured.

**Second hop — the engineering-to-commercial join.** From SpecSection, traverse `PROCURED_UNDER` to CostCode, then `LINE_ITEM_OF` to the specific Commitment/POLine. This is the single most important hop in the entire model — it is the literal moment the graph crosses from the Reference Engineering System into the Reference Commercial System.

**Third hop — first-order commercial blast radius.** From the matched POLine/Commitment, traverse `SUPPLIED_BY` to Vendor and `SCHEDULED_WITH` to ProcurementScheduleItem/Delivery. Everything reached here is a direct, key-matched consequence — the highest-confidence tier the traversal can produce.

**Fourth hop — second-order, lower-confidence candidates.** From the first-order POLine, traverse `STRUCTURALLY_DEPENDS_ON` or `TEMPORALLY_SCHEDULED_WITH` to other POLines that share physical or temporal adjacency without a direct key match. This is where PROBABLE- and POSSIBLE-tier candidates originate.

**Depth limit.** A hard stop five hops from the trigger (identity: 2 hops; engineering-to-commercial join: +1; first-order blast radius: +1; second-order dependents: +1). Beyond this, match quality decays into noise — an unbounded traversal becomes indistinguishable from "everything on the project might be related," which asserts nothing useful. The limit is not a technical convenience; it is a reasoning discipline.

**Fan-out rule — never compound weak signals.** At every hop, an edge below a minimum relevance floor is not traversed further. Chaining two "maybe" links together and presenting the combined result as a single conclusion is exactly how false positives get manufactured across multiple systems that were never meant to agree. A multi-hop path's eventual confidence is bounded by its **weakest** edge, never its strongest, and never an average of the two.

**Termination conditions.** A branch stops expanding when: (a) the current node has no further high-relevance untraversed edges, (b) one more hop would push the accumulated evidence below the POSSIBLE floor into INSUFFICIENT_EVIDENCE, or (c) the depth/fan-out budget above is exhausted. Every termination is explicit and explainable — "the traversal stopped here, and here is why" — never a silent truncation.

**Why this shape, and not a similarity search.** The whole product's credibility rests on every hop being explainable to a human as "X is connected to Y because Z, a real shared identifier or a real dependency edge" — never "X and Y seemed related in embedding space." A typed, narrow, explainable graph is slower to build and less impressive-sounding than semantic search, and it is the only version of this system a procurement lead should ever be asked to trust with a live purchase order.

---

## Section 6 — Evidence Model

Each evidence type, and what it specifically proves:

- **Drawing reference / revision cloud** — proves *what changed physically, and where*.
- **Spec section** — proves the causal reason a commercial artifact could be affected at all; the primary join key.
- **Submittal approval status** — proves whether a commitment has *already* been authorized to proceed toward fabrication — the single most decisive lifecycle signal available.
- **PO line** — the commercial commitment itself: what was ordered, at what value, under which cost code.
- **Vendor** — proves who bears or must execute the consequence.
- **Location** — proves physical scope overlap between the change and the commitment.
- **Cost Code** — the primary structural link between the two reference systems.
- **Lifecycle Position** — proves how far the commitment has already traveled — the dominant severity input.
- **Schedule Activity** — proves the timing dependency between a delivery and the project's own critical path.
- **Commitment** — proves the financial exposure, independent of and prior to any invoice.

**How evidence is collected.** Only from artifacts already surfaced by Entity Resolution and Graph Expansion — never synthesized, never inferred from general world knowledge, and always a pointer to an actual location within an actual document or field, never a paraphrase of it.

**When evidence is insufficient.** Three conditions, any one of which is disqualifying: (1) a candidate's *only* support is a single weak signal with no corroborating second signal (location adjacency alone, with no spec or cost-code overlap); (2) the underlying data itself is stale or was fetched under a partial credential scope, meaning the fact being relied on may already be wrong or incomplete; (3) a field the confidence calculation structurally requires is simply absent (no cost code on a PO line, no spec-section reference on the trigger). In any of these cases the correct outcome is the fourth confidence tier below — never a default assignment to POSSIBLE, which would falsely imply *some* real signal exists.

---

## Section 7 — Confidence Model

Four tiers. The fourth, `INSUFFICIENT_EVIDENCE`, is a reasoning-stage gate, not a value ever shown to a human — a candidate that reaches it is discarded before an Impact is ever created, because surfacing "we found something but have no evidence for it" would itself violate the principle that Downstream never asserts past what it knows.

**CERTAIN**
- *Required evidence:* an exact key match — the trigger's spec section is the literal cost code of the affected PO line, or an explicit direct cross-reference exists — reached in a single engineering-to-commercial hop.
- *Minimum graph support:* one direct edge, no ambiguity in Entity Resolution (the match score sits at its ceiling).
- *Example:* an RFI cites Spec 23 31 13 verbatim; the affected PO's cost code is the section's own MasterFormat-derived code.
- *When it should decrease:* if the underlying commercial snapshot is discovered to be stale rather than real-time — a stale fact cannot support certainty about the present, no matter how clean the match.

**PROBABLE**
- *Required evidence:* an inferred second-order graph edge (a structural or temporal dependency) or a high-but-imperfect fuzzy key match, or a direct match where Entity Resolution itself had to choose between two plausible candidates.
- *Minimum graph support:* one direct edge plus one inferred edge, or a single fuzzy-matched direct edge above the relevance floor.
- *Example:* a hanger-steel PO is linked to a directly-matched duct-fabrication PO via a structural-dependency edge, with no direct spec citation of its own.
- *When it should decrease:* if a second independent check (e.g., the artifact's own data freshness) contradicts or cannot corroborate the signal.

**POSSIBLE**
- *Required evidence:* a single weak signal only — location adjacency, discipline overlap, or temporal proximity — with no corroborating spec or cost-code support.
- *Minimum graph support:* one weak edge, unsupported by any stronger signal.
- *Example:* a schedule activity sharing a grid location with the change, with no scope reference of its own.
- *When it should decrease:* it cannot decrease further without becoming INSUFFICIENT_EVIDENCE — this is the honesty floor.

**INSUFFICIENT_EVIDENCE**
- *Required evidence:* none clears the POSSIBLE floor, or required source data is missing, stale beyond use, or was fetched under a credential scope that could not have seen it.
- *System behavior:* the candidate is dropped before Impact creation. It is logged internally for future graph-tuning, never surfaced to a human as an unresolved claim.

**When the system must stop reasoning entirely.** The moment a traversal branch's accumulated evidence would fall to this fourth tier, per the termination rule in Section 5 — the system stops extending that branch rather than continuing to guess.

---

## Section 8 — Severity Model

**The foundational design decision: confidence and severity are independent axes, computed from different evidence, and neither is an input to the other.** Confidence answers *how sure are we this link is real*; severity answers *how bad would this be if it is*. A PROBABLE-tier impact on an already-shipped, high-value commitment can and should outrank a CERTAIN-tier impact on a still-draft requisition — the tier of certainty says nothing about the size of the consequence. This is not a simplification; it is the correct shape of the problem, and collapsing the two into a single number is exactly the kind of false precision this specification exists to prevent.

**Per-impact severity is a business-reasoning decision table, not a weighted formula with invented coefficients**, built from three factors:

1. **Lifecycle position (the dominant factor).** An ordinal progression by how expensive and how possible correction still is: *draft* (free — simply edit it) < *issued* (cheap — cancel or amend) < *in_fabrication* (expensive — work-in-progress is scrapped or reworked) < *shipped* (very expensive and schedule-breaking — redirect in transit or receive-and-rework) < *installed* (worst — physical demolition and rework in place).
2. **Commercial exposure.** The committed or actual value at risk on the specific artifact, bucketed (not falsely precise) into low/medium/high/critical bands. A large lifecycle penalty on a trivial-value line is still less severe than a moderate lifecycle penalty on a seven-figure, non-cancellable commitment.
3. **Schedule criticality.** Whether the affected delivery or activity sits on the project's critical path or carries float. A delayed delivery with slack is materially less severe than an identical delay with none.

**How these combine.** Lifecycle position sets the baseline severity band. Commercial exposure and schedule criticality then adjust that baseline upward when either is high/critical — never downward past what lifecycle position alone would indicate, because a cheap-to-fix mistake is never made *more* dangerous by a low price tag, only a costly one made worse by a high one.

**Blast radius (breadth) is reported separately from peak severity, deliberately.** The number of affected vendors and commitments is never averaged into the per-impact severity score — doing so would let one catastrophic impact be diluted by counting several trivial ones alongside it. Instead, an **Event's overall severity is the maximum severity across its Impacts** (the single worst consequence), while breadth is reported as its own dimension that separately informs which recommendation category applies (Section 9) — because many simultaneous moderate impacts across many vendors is a *coordination* difficulty even when no single one is individually catastrophic.

**Worked example — the HVAC demo scenario:**

| Affected commitment | Lifecycle position | Commercial exposure | Schedule criticality | Resulting severity |
|---|---|---|---|---|
| Switchgear PO | in_fabrication | Critical (multi-million, non-cancellable once released) | On critical path (lead time measured in months) | **Severity 1** — the worst combination: expensive to unwind, expensive in absolute terms, and no schedule slack |
| Feeder/busway delivery | shipped (in transit) | Medium (a more standard, lower-value component) | Some criticality, less acute than switchgear | **Severity 2** — a higher lifecycle position than the switchgear alone would suggest, but tempered by materially lower exposure |
| Branch conduit requisition | draft | Low (nothing committed yet) | Not yet schedule-critical | **Severity 4** — cheapest and most fully preventable; simply correct the requisition before it converts to a PO |

Note that the feeder does **not** automatically outrank the switchgear despite a "later" lifecycle position — this is the model correctly refusing to apply lifecycle position as a strict, exposure-blind ordering, exactly as the general rule above specifies.

---

## Section 9 — Recommendation Engine

Recommendations are generated from the **combination** of confidence and severity — the first point in the pipeline where the two independent axes are actually used together.

- **PO Amendment** — generated when confidence is CERTAIN or PROBABLE and severity is high (1–2). A concrete, drafted revision to the specific commercial commitment, ready for approval.
- **Vendor Notification** — generated alongside a PO Amendment whenever the affected party is external to the buying organization and needs to be informed or asked to act (a hold, a revised spec, a rescheduled delivery).
- **Procurement Review** — generated when severity is high but confidence is only PROBABLE — the consequence would be serious *if real*, but the causal link itself still needs a human's confirmation before a vendor-facing action is drafted with full confidence.
- **Engineering Review** — generated when the ambiguity is on the *technical* side, not the commercial side — e.g., it is unclear whether an artifact represents a genuine scope change or merely a clarification. This routes to a discipline lead, because procurement cannot resolve a technical question.
- **Monitor** — generated for POSSIBLE-tier candidates regardless of severity, and for low-severity candidates at any confidence tier. No action is drafted; the item is flagged for awareness and automatically re-evaluated if the artifact's lifecycle position later advances.
- **Review** — the baseline "a human should look at this" recommendation when nothing more specific applies.
- **Executive Escalation** — generated independent of any single impact's severity, triggered instead by *breadth* (a high number of simultaneously affected vendors/commitments crossing an organizational-attention threshold), by aggregate commercial exposure across the whole Event crossing a materiality threshold, or by a Severity-1 recommendation's approved action subsequently failing or being rejected. Escalation is about organizational attention, never a substitute for the per-impact recommendation already generated.

**What must never be generated automatically, under any confidence or severity condition:**
- Any recommendation that assigns fault or asserts legal/contractual entitlement — that is the claims domain, explicitly out of scope (Section 1).
- Any recommendation that originates a *new* sourcing or vendor decision Downstream was never asked to make — the system reacts to what already exists; it does not decide who should be hired.
- Any recommendation that would execute a financial or contractual transaction without prior human approval.
- Any recommendation drafted from a candidate that reached INSUFFICIENT_EVIDENCE — such a candidate never reaches this stage at all, by design (Section 7).

---

## Section 10 — Human-in-the-Loop

**Approval gates.** Every drafted Action is approved, edited, or rejected individually — never in bulk, for anything above the lowest-severity acknowledgment. This holds regardless of confidence or severity; there is no shortcut for a CERTAIN, Severity-1 finding.

**Override capability.** A human may edit a drafted Action's content before approving it, or reject it outright with a stated reason. Both are captured as an immutable Approval record, distinct from the Action's own (editable-until-approved) content.

**Manual dismissal.** A human may acknowledge an Impact without taking its drafted action at all. This is always a recorded, attributed decision — never a silent timeout, and never indistinguishable from an Impact that was simply never reviewed.

**Manual evidence.** A human should be able to attach additional context to an Impact — confirming or refuting the system's inference from outside knowledge Downstream could not have had. This is not a courtesy feature; it is the mechanism by which the system's own future matching improves.

**Manual confirmation as training signal.** When a human approves a PROBABLE-tier recommendation, that approval does more than authorize the action — it validates the underlying inferred relationship for the first time. Every human decision, across all of the above, is signal that should inform how confidently the same class of inference is drawn next time.

**Auditability.** Every trigger, inference, tier assignment, recommendation, and human decision is appended, immutably, to the permanent record — attributable to a specific person and moment, never editable after the fact.

**Why autonomous execution is dangerous in construction, specifically.** A wrong commercial action taken without review has consequences that are physical and often irreversible — fabricating the wrong part, damaging a vendor relationship with an incorrect notice, committing budget against a need that was misread. The cost of undoing a physical mistake dwarfs the cost of pausing for a human's confirmation the first time — the same 1-10-100 logic that justifies the whole product's existence applies with equal force to the product's own actions. And responsibility in construction is a matter of professional licensure and contractual authority that cannot be delegated to software. Downstream's credibility depends entirely on never crossing this line — not on how rarely it would technically need to.

---

## Section 11 — Synchronization Policy

**What is written back.** Only the specific field or scope an approved Action was drafted to change — a PO hold flag, a revised delivery date, a vendor notice — dispatched through whichever tier (a drafted external communication, or a proposed write into the commercial system of record) the Action's type calls for. Never a broader write than the one a human explicitly approved.

**What is never written back.** Anything not explicitly approved. Any write to the *engineering* system of record — Downstream is commercial-side only in its write scope; it never edits a drawing, an RFI, or a spec section, one-directionally, always. Any write that bypasses the target commercial system's own governance — a proposed PO hold still passes through that system's own release/approval workflow; Downstream proposes into it, never around it. Any write outside the specific scope the connecting credential was actually granted.

**When synchronization occurs.** Only after a human Approval is recorded — never speculatively, never pre-emptively, regardless of how certain or severe the finding is. The most urgent, most certain finding still waits for the click.

**What requires approval.** Every synchronization dispatch, without exception. There is no confidence or severity threshold above which a shortcut exists, because the day such a shortcut is introduced is the day the product's entire premise — evidence-backed recommendation *for* human approval — stops being true.

---

## Section 12 — Failure Modes

- **Missing drawing/document.** Normalization cannot complete. The pipeline halts for that trigger and surfaces "extraction failed, needs review" — it never guesses at a change's scope from a partial artifact.
- **Missing vendor / incomplete commercial record.** Commercial Mapping cannot complete for that specific candidate. That one link is capped at INSUFFICIENT_EVIDENCE; other, independently-resolved links within the same Event proceed unaffected.
- **Conflicting revisions** (two drawing versions both claiming currency, or two RFIs answering the same question differently). The system never silently picks one. The conflict itself becomes the finding — routed as an Engineering Review, because resolving which source is authoritative is a technical judgment, not a commercial one.
- **Stale commercial data.** Any lifecycle-position or value read that did not arrive through a genuinely current path caps the achievable confidence tier for everything depending on it at PROBABLE, regardless of how clean the key match otherwise is — a clean match against a possibly-outdated fact is not a certain conclusion.
- **Connector/data-source failure.** The affected reasoning branch halts rather than proceeding on a value known to predate the failure. A dimension that cannot currently be checked is marked unknown, never silently assumed unchanged.
- **Partial graph coverage** (a new project, or an artifact type the key-index has never encountered). The system degrades to narrower-hop, lower-tier reasoning rather than either refusing to reason at all or overreaching past what the graph can actually support.
- **Low confidence across an entire Event.** The trigger and its best candidates are still surfaced — as a Monitor recommendation — rather than suppressed. Low confidence is not the same condition as nothing having happened, and a human should still know a change occurred even when Downstream cannot yet say with confidence what it broke.

**The unifying rule across every failure mode:** degrade the *scope or confidence* of the claim, never the *honesty* of it. Always surface what is genuinely known, clearly labeled as partial where it is partial — never go silent on a real signal, and never overstate certainty to produce a cleaner-looking answer from broken inputs.

---

## Section 13 — Walkthrough: The HVAC Demo Scenario

**Step 1 — Trigger arrives.** A mechanical equipment Submittal for a rooftop unit is approved (status: *No Exceptions Taken*) on its second revision. Downstream knows only that a Submittal tied to a Mechanical spec section has changed status.

**Step 2 — Normalize.** Document intelligence diffs the current submittal's equipment schedule against the prior revision and finds the unit's MCA and FLA (minimum circuit ampacity, full-load amps) have increased. The trigger normalizes to: type = Submittal Revised, discipline = Mechanical, delta = electrical demand increase.

**Step 3 — Entity Resolution.** The mechanical spec section is resolved in the graph. A cross-discipline reference edge, captured during initial project calibration, links this equipment's electrical characteristics to a specific Electrical spec section governing the serving switchgear.

**Step 4 — Graph Expansion.** From the Electrical spec section: `PROCURED_UNDER` → CostCode → `LINE_ITEM_OF` → the switchgear PO line (first-order). From that PO line, `SCHEDULED_WITH` surfaces the feeder/busway delivery (first-order); a `STRUCTURALLY_DEPENDS_ON`-type edge surfaces a not-yet-ordered branch-conduit requisition (second-order). Downstream now holds three candidate commercial artifacts at three different fabrication stages.

**Step 5 — Evidence Collection.** Switchgear: the submittal's revised equipment-schedule row, plus the explicit cross-discipline reference note, plus the switchgear PO's own cost code matching that spec section — three corroborating signals. Feeder: the same submittal delta, reached one hop further, with no direct citation of its own. Branch conduit: only a location/discipline adjacency, with no spec or cost-code support at all.

**Step 6 — Commercial Mapping.** Each engineering-side entity now has a real Reference Commercial System counterpart: a Vendor, a lifecycle_position, and a value, for all three artifacts.

**Step 7 — Impact Analysis.** Switchgear and feeder are both classified as "electrical rating now insufficient for the specified equipment" — a genuine technical/commercial conflict. The branch conduit is classified as "a possible future sizing conflict on an item not yet committed" — a softer, still fully preventable finding.

**Step 8 — Severity Calculation.** Switchgear: in_fabrication + critical exposure + on the critical path (a lead time measured in months) → **Severity 1**. Feeder: shipped, but materially lower value than the switchgear lineup → **Severity 2**. Branch conduit: draft, low exposure, nothing yet committed → **Severity 4**.

**Step 9 — Confidence Calculation.** Switchgear: two independent corroborating signals, a direct key match → **CERTAIN**. Feeder: the same delta, reached via one further graph hop with no independent citation → **PROBABLE**. Branch conduit: adjacency only → **POSSIBLE**.

**Step 10 — Recommendation Generation.** Switchgear (CERTAIN + Severity 1) → **PO Amendment** and **Vendor Notification**, both drafted and flagged urgent given the lead-time-restart risk. Feeder (PROBABLE + Severity 2) → **Procurement Review**, with a drafted vendor notification pending human confirmation of the link. Branch conduit (POSSIBLE + Severity 4) → **Monitor**, no action drafted, flagged for re-evaluation if the requisition later converts to a PO.

**Step 11 — Human Approval Decision.** The procurement lead reviews all three in severity order. She approves the switchgear PO Amendment and Vendor Notification after clicking through the evidence to confirm the submittal delta and the cross-discipline reference note herself. She reviews and approves the feeder's Procurement Review, and in doing so personally confirms the previously-inferred structural dependency — feeding that confirmation back as future confidence signal. She acknowledges the conduit Monitor flag with no action, noting to revisit it before that requisition is ever released as a PO.

**Step 12 — Synchronization.** The approved switchgear PO Amendment and Vendor Notification dispatch — the amendment as a proposed write into the commercial system of record (still subject to that system's own release-strategy re-approval), the notification as a drafted external communication. The feeder's approved notification dispatches the same way. Nothing synchronizes for the branch conduit — no action was approved, so nothing is sent; only its Monitor status is recorded to the permanent record.

---

## Section 14 — Design Principles

The principles every future implementation of this reasoning model must preserve, regardless of how the surrounding software evolves:

1. **Never infer without evidence.** A conclusion Downstream cannot point at a real document or field is a conclusion Downstream does not draw.
2. **Confidence and severity are independent axes.** Certainty is never conflated with consequence; a less-certain finding about a catastrophic outcome still outranks a certain finding about a trivial one.
3. **Graph before language model.** Every conclusion is traceable through typed, named relationships — never through embedding-space similarity a human cannot audit.
4. **Relationships matter more than documents.** No artifact has commercial meaning in isolation; meaning lives in the edge, not the node.
5. **Lifecycle position is the primary driver of severity**, because it is the primary driver of what correction actually costs in the physical world.
6. **Never synchronize without an explicit human approval** — regardless of confidence, regardless of severity, without exception.
7. **Engineering truth is upstream of commercial truth.** Downstream always reasons from design reality toward its commercial consequence, never the reverse.
8. **Downstream proposes; the systems of record still govern.** Every write-back still passes through the target system's own approval workflow — it is never bypassed.
9. **Silence is honest when evidence is honest.** An INSUFFICIENT_EVIDENCE candidate is discarded, not guessed at, and not quietly rounded up to something more confident-sounding.
10. **Every human decision is training signal.** Approvals, edits, and dismissals feed back into how confidently the same class of inference is drawn next time.
11. **The human owns the final decision, always.** This is not a limitation to be engineered around as the system matures — it is the permanent foundation of why the system can be trusted at all.
12. **The domain models are vendor-neutral, and so is the reasoning that runs on them.** The intelligence layer reasons exclusively in terms of the Reference Engineering and Reference Commercial Systems' own entities — never in terms of any single vendor's proprietary schema, now or in any future implementation.