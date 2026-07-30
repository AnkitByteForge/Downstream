# Downstream Demo Strategy: The Top 20 Engineering Changes That Wreck Procurement — and the Single Best One to Demo Live

## TL;DR
- **The single best live-demo scenario is a late HVAC/mechanical equipment upsizing (a larger rooftop unit or chiller with higher electrical demand) that ripples into the electrical package after switchgear/transformer POs are already released to fabrication** — because it hits multiple POs at different lifecycle stages at once (already-fabricating switchgear, in-transit feeders, still-draft branch conduit), carries a defensible seven-figure blast radius, and a non-technical judge grasps "the AC got bigger, so the electrical gear you already bought is now the wrong size" in under 15 seconds.
- The changes that most severely hurt procurement are the ones that strike **fabricated-to-order, long-lead commitments** — structural steel, rebar cages, curtain-wall units, switchgear, transformers, and MEP prefab spools — where the fabrication/shipping "lifecycle distance" is already large, exactly the axis Downstream's severity model (blast_radius × lifecycle_distance) is built to expose.
- Change orders are effectively universal (large projects >$50M average 11.29 change orders each and add ~4–5% to contract value) and rework runs ~5% of project cost, but the value Downstream creates is concentrated in catching the small subset of changes that hit already-in-flight commitments **before** the next fabrication/shipping gate closes — where the cost differential between "caught now" and "caught late" is 10–100×.

## Key Findings
1. **Change is the default, not the exception.** AIA Contract Documents' Construction Benchmark Database analysis of 892,457 change orders across 18,229 completed U.S. projects ("The Truth About Change Orders") found large projects (>$50M) average 11.29 change orders each, and change orders add roughly 4–5% to contract cost on average, rising to +15% at the upper Market Standard Range. Critically, most change orders land in the **back half** of a project — precisely when commitments are already in fabrication or shipped.
2. **RFIs are the leading indicator and they are voluminous.** The Navigant Construction Forum's 2013 "Impact & Control of RFIs on Construction Projects" (1,362 projects, 2001–2012, via ACONEX data) found 1.1M RFIs, averaging 796 per project (9.9 per $1M of construction), ~$1,080 to process each, a 6.4-day average first reply and 9.7-day median reply, and ~22% never formally answered. RFIs frequently spawn the ASI/CCD/PCO/ChangeOrder chain that Downstream keys off.
3. **Rework is 4–10% of project cost.** Per the Construction Industry Institute (CII, IR-153/Hwang et al. analysis of 359 projects), direct rework costs average 5% of total construction costs, with a range of 2–20% depending on project type (industrial projects averaging ~12%); the UK Get It Right Initiative puts total avoidable error near 21% once indirect costs and latent defects are counted. The PlanGrid/FMI 2018 "Construction Disconnected" report (survey of 599 construction leaders) found poor project data and miscommunication responsible for 48% of all rework, accounting for a total of $31.3 billion in U.S. rework in 2018 ($17B miscommunication + $14.3B poor project data).
4. **The severity axis is real and physically grounded.** The escalation of remediation cost as a defect survives further down the pipeline (the 1-10-100 rule) maps directly onto Downstream's lifecycle_distance term. In construction procurement this is not a metaphor: fabricated rebar cages, cut steel, and glass units cannot be un-fabricated, and engineered electrical gear becomes **non-cancellable once released to production**.
5. **Long-lead electrical equipment is now the critical path and the highest-severity blast radius.** Wood Mackenzie's Q2 2025 survey ("Making the Connection") put power transformers at 128 weeks (down 10 weeks in the quarter), generator step-up transformers at 143–144 weeks, and switchgear at ~44 weeks; per VAWN's Electrical Equipment Lead Time Index, Wood Mackenzie's 2026 read puts substation units above 160 weeks (roughly three years). A late load change that forces a revised submittal **restarts the entire lead-time clock from the date the revised submittal clears review**, not the original order date.

## Details

### Methodology and data basis
This analysis builds on the two reference domain models. For each candidate change I mapped: (a) the **triggering engineering artifact** (Drawing/DrawingVersion, SpecSection, RFI, Submittal, ASI/CCD/PCO/ChangeOrder, ClashItem), (b) the **commercial artifact hit** (PurchaseOrder/POLine, Commitment, Delivery, Vendor, ProcurementScheduleItem), and (c) where in the fabrication/expediting sub-lifecycle (draft→issued→in_fabrication→shipped→installed) the commitment typically sits when the change lands — the single biggest driver of severity.

Frequency, cost, schedule, detection-difficulty, and Downstream-value ratings below are on a 1–5 scale (5 = highest/worst/most valuable), grounded in the cited data where available and expert-pattern judgment where specific studies do not isolate the scenario.

### The Top 20 engineering changes that create downstream commercial risk

**1. Late HVAC/mechanical equipment upsizing driving electrical load increase after switchgear/gear is ordered.** Discipline: Mechanical→Electrical. Trigger: equipment Submittal / substitution or an ASI increasing RTU/chiller MCA/FLA. Hits: switchgear/transformer/feeder POs (Commitment, POLine in_fabrication), branch-circuit conduit (draft). Frequency 5 (MEP coordination is a top change-order driver; Eagle BIM, citing Dodge Construction Network, notes disciplined MEP coordination reduces field RFIs and change orders by 40–60% on complex commercial work — implying that fraction is coordination-driven). Cost 5 (switchgear lineups run into the millions; engineered gear becomes non-cancellable once released, with 20–50% cancellation exposure short of that). Schedule 5 (a revised submittal restarts a 44–160-week lead-time clock). Detection 5 (the load delta lives in a mechanical equipment schedule; the electrical PO lives in a different system/vendor — nobody reconciles them until startup). Downstream value 5.

**2. Structural beam/column size revision after steel is released for fabrication.** Discipline: Structural. Trigger: DrawingVersion revision cloud / structural ASI. Hits: steel-fabrication PO (in_fabrication or shipped), connection material, erection subcontract. Frequency 4. Cost 5 (recut/refab, re-detailing at 5–8% of fab cost, plus possible foundation redesign). Schedule 5 (steel is the first trade after foundations; everything behind it slips). Detection 4. Downstream value 5.

**3. Structural change after rebar cages are already fabricated/bent.** Discipline: Structural/Civil. Trigger: rebar shop-drawing revision, ASI, or clash. Hits: rebar-supply PO (in_fabrication), placement subcontract, concrete pour ScheduleActivity. Frequency 4. Cost 4 (prefabricated cages discarded/reworked — "among the costliest sources of rebar waste"). Schedule 3 (pour delayed until reinforcement matches approved drawings). Detection 4. Downstream value 4.

**4. Curtain-wall/facade glazing spec change after glazing shop drawings approved and glass fabrication started.** Discipline: Architectural. Trigger: SpecSection change / substitution / ASI. Hits: glazing subcontract Commitment, glass-fab PO (in_fabrication), unitized-panel delivery. Frequency 3. Cost 5 (specialty/impact-rated glass fabrication runs 10–16 weeks and cannot be accelerated once in fab; mockups $30–80K). Schedule 5 (facade is on critical path for dry-in). Detection 4. Downstream value 5.

**5. Anchor-bolt / embed-plate location or pattern change after slab/foundation poured.** Discipline: Structural. Trigger: structural DrawingVersion / RFI resolution. Hits: embed/anchor supply PO, steel erection sequence, possible concrete rework. Frequency 3. Cost 3. Schedule 3 (documented 2–3 day field delays awaiting redesigned anchors + refabrication; worse if concrete demolition needed). Detection 4. Downstream value 3.

**6. Electrical service/distribution redesign (voltage, phase, capacity) after switchgear/panel submittals released.** Discipline: Electrical. Trigger: load recalculation, utility coordination, ASI. Hits: switchgear/panelboard PO (in_fabrication), feeder/busway. Frequency 4. Cost 5. Schedule 5. Detection 4. Downstream value 5.

**7. Mechanical equipment substitution ("or-equal") changing dimensions/clearances/connections after coordination complete.** Discipline: Mechanical. Trigger: substitution Submittal. Hits: equipment PO, ductwork/piping prefab, housekeeping-pad/structural embeds. Frequency 4. Cost 3. Schedule 3. Detection 5 (substitution details are frequently buried in electrical data tables and slip submittal review). Downstream value 4.

**8. MEP coordination clash resolution forcing rerouting after prefab spools/multi-trade racks fabricated.** Discipline: Mechanical/Electrical/Plumbing/FP. Trigger: ClashItem / coordination DrawingVersion. Hits: prefab spool/rack POs (in_fabrication or shipped), hanger/support supply. Frequency 4. Cost 4 (prefab shifts cost to the shop; a late structural move means fabricated spools don't fit — the most frequent prefab failure mode). Schedule 3. Detection 4. Downstream value 4.

**9. Fire-protection sprinkler design change forcing hydraulic recalculation and pipe/head refabrication.** Discipline: Fire Protection. Trigger: SpecSection/occupancy change, ASI, coordination clash. Hits: sprinkler subcontract, pipe-spool PO, fire-pump equipment PO. Frequency 3. Cost 3. Schedule 3. Detection 3. Downstream value 3.

**10. Precast concrete panel design/connection change after panels cast or embeds set.** Discipline: Structural/Architectural. Trigger: DrawingVersion / connection RFI. Hits: precast-supply PO (in_fabrication/shipped), embed/hardware supply, erection crane sequence. Frequency 3. Cost 4 (field-installed connection steel costs 3–5× shop cost). Schedule 3. Detection 3. Downstream value 4.

**11. Foundation redesign from geotechnical/unforeseen soil conditions after pile/footing materials ordered.** Discipline: Civil/Geotechnical/Structural. Trigger: FieldIssue/Observation → RFI → ASI/CCD. Hits: pile-supply PO, rebar, concrete, possible re-mobilization. Frequency 3. Cost 4. Schedule 4. Detection 3. Downstream value 3.

**12. Electrical gear relocation from architectural room/space change after conduit/feeder routing set.** Discipline: Architectural→Electrical. Trigger: architectural DrawingVersion / Location change. Hits: feeder/conduit material, gear delivery staging. Frequency 3. Cost 3. Schedule 3. Detection 4. Downstream value 3.

**13. Duct/pipe main resizing after ductwork/piping fabricated.** Discipline: Mechanical. Trigger: load/flow recalculation, VE, coordination. Hits: sheet-metal/pipe-fab PO (in_fabrication). Frequency 3. Cost 3. Schedule 2. Detection 3. Downstream value 3.

**14. Elevator/vertical-transport spec change (capacity, speed, hoistway) after unit ordered.** Discipline: Architectural/Mechanical. Trigger: SpecSection/ASI. Hits: elevator equipment PO (long-lead, in_fabrication), shaft structural embeds, rail supply. Frequency 2. Cost 4. Schedule 4. Detection 3. Downstream value 4.

**15. Roofing/waterproofing assembly spec change after materials ordered/delivered.** Discipline: Architectural. Trigger: SpecSection change / substitution. Hits: roofing-material PO (shipped/delivered), roofing subcontract. Frequency 3. Cost 2. Schedule 2. Detection 3. Downstream value 2.

**16. Structural connection detail change (moment vs. shear, weld vs. bolt) after fabrication drawings approved.** Discipline: Structural. Trigger: connection-design RFI / EOR revision. Hits: steel-fab PO (in_fabrication), bolt/weld consumable supply. Frequency 3. Cost 3. Schedule 3. Detection 4. Downstream value 3.

**17. Owner-driven scope/program change (added lobby, tenant fit-out revision) mid-fabrication.** Discipline: Architectural (owner). Trigger: owner CCD/ChangeOrder. Hits: multiple trade Commitments and POs across lifecycle stages simultaneously. Frequency 4. Cost 4. Schedule 3. Detection 2 (usually explicit, but the downstream PO fan-out is not traced). Downstream value 3.

**18. Code/AHJ-driven change (egress, fire rating, accessibility) after related materials ordered.** Discipline: Architectural/Life-Safety. Trigger: building-official requirement / permit revision. Hits: door/hardware POs, rated-assembly materials, fire/life-safety equipment. Frequency 3. Cost 3. Schedule 3. Detection 3. Downstream value 3.

**19. Generator/UPS/backup-power spec change after long-lead unit ordered.** Discipline: Electrical/Mechanical. Trigger: load recalculation / resiliency requirement / ASI. Hits: generator/UPS PO (long-lead 12–20+ weeks, in_fabrication), fuel/exhaust systems, structural pad. Frequency 3. Cost 5. Schedule 4. Detection 3. Downstream value 4.

**20. Finish/fixture spec change (plumbing fixtures, lighting) after ordered/in production.** Discipline: Architectural/Plumbing/Electrical. Trigger: SpecSection change / substitution / owner selection. Hits: fixture POs (in_fabrication/shipped), attic-stock, warranty terms. Frequency 4. Cost 2. Schedule 1. Detection 3. Downstream value 2.

### Composite ranking and weighting rationale

Because Downstream's entire thesis is catching in-flight commitments before further fabrication/shipping progress, I weight the five dimensions: **Downstream Value 30%** (the product's reason to exist), **Financial Impact 25%**, **Frequency 20%** (a rare catastrophe is a worse demo/value story than a common six-figure one), **Detection Difficulty 15%** (why it slips today = why Downstream is needed), **Schedule Impact 10%** (largely correlated with and partly captured by cost).

Composite top tier (weighted score, 1–5):
1. **#1 HVAC-load-driven electrical gear change** — 4.90
2. **#6 Electrical service/distribution redesign** — 4.55
3. **#2 Beam/column steel revision after fab release** — 4.50
4. **#4 Curtain-wall glazing spec change mid-fab** — 4.25
5. **#3 Structural change after rebar fabricated** — 3.85
6. **#8 MEP clash rerouting after prefab** — 3.75
7. **#19 Generator/UPS spec change** — 3.55
8. **#7 Mechanical substitution / clearance** — 3.50

The bottom cluster (#15, #20, #13, #5) score lower primarily on financial impact and Downstream value — they either hit commodity/short-lead commitments (low lifecycle_distance) or are caught relatively easily today.

### The 3–5 strongest live-demo candidates
Filtering for **visual clarity, <30-second judge comprehension, technically impressive trace, and dramatic before/after**:
- **#1 HVAC-load-driven electrical gear change** — best all-around (see recommendation).
- **#2 Steel beam revision after fab release** — extremely visceral ("the beam already being welded is now the wrong size"), single clean trace-line, but tends to hit one dominant PO/vendor, so it under-showcases the blast-radius/severity-tiering mechanism.
- **#4 Curtain-wall glazing change** — visually gorgeous and intuitive, but narrower blast radius (one glazing sub) and slightly more jargon to set up.
- **#6 Electrical service redesign** — enormous numbers, but the trigger (a load calc) is abstract and harder for a lay judge to "see" than a physical AC unit getting bigger.

## Recommendation

**Demo Scenario #1: A late-approved change enlarges a rooftop HVAC unit (or chiller), raising its electrical demand — and Downstream instantly shows that the already-in-fabrication switchgear, the in-transit feeder/busway, and the not-yet-ordered branch conduit are now wrong, with a computed cost-of-catching-it-now vs. cost-of-catching-it-late.**

Stage it as "The Break": a calm board of green in-flight POs across three vendors. An approved ASI/equipment-submittal lands (the VLM reads the mechanical schedule showing the new unit's higher MCA/FLA). Cards flip red **in severity order** — the fabricating switchgear PO first (highest lifecycle_distance, non-cancellable), then the in-transit feeder, then the draft conduit (lowest severity, cheapest to fix). Each red card throws a trace-line back to the exact clause/line in the equipment submittal that caused it. Closing beat: **catch-now cost (a change order to a not-yet-released branch-conduit PO plus a modest gear reconfiguration) vs. catch-late cost (a non-cancellable switchgear re-order that restarts a ~44-week clock, plus delay damages).**

**Why this wins on all six criteria:**

1. **Technical sophistication.** It naturally exercises every Kaya-named technique: a **VLM** reads the equipment submittal / mechanical schedule (a real drawing/table); **Document Intelligence** extracts the load delta and the affected spec section; **knowledge-graph / entity resolution** links the mechanical equipment → electrical load → the specific switchgear POLine → vendor → ProcurementScheduleItem → dependent branch circuits across both reference models; **confidence tiering** is genuine (Certain: switchgear lineup on this feeder; Probable: feeder ampacity; Possible: downstream breaker coordination); and **severity computation** (blast_radius × lifecycle_distance) is the star of the show because the three affected POs sit at three different fabrication stages.

2. **Business value.** The numbers are large and defensible: switchgear lineups are multi-million-dollar commitments (hyperscale single orders have exceeded $400M per Eaton disclosures); engineered gear is **non-cancellable once released to production** (with 20–50% exposure short of that, per standard manufacturer terms); and a forced re-order **restarts the full 44–160-week lead-time clock** (Wood Mackenzie Q2 2025: switchgear ~44 weeks, power transformers 128 weeks), with delay costs on a large mission-critical project running into the millions per month. No other Top-20 scenario combines a seven-figure commitment with a physically un-cancellable fabrication state so cleanly.

3. **Visual demonstration quality.** Three cards, three colors, three trace-lines, one clear cost differential — it fits "The Break" perfectly, and the severity-ordered flip is the visual payoff.

4. **Realism.** MEP (HVAC/electrical) coordination is repeatedly identified as a top change-order driver — Eagle BIM, citing Dodge Construction Network, notes disciplined MEP coordination cuts field RFIs and change orders by 40–60% on complex commercial work. A project director will recognize "the mechanical guys upsized the unit and the electrical gear was already bought" instantly.

5. **Judge understanding.** The one-sentence stakes — "the air conditioner got bigger, so the electrical equipment you already paid for and can't return is now too small" — need zero construction vocabulary.

6. **Commercial impact / blast radius.** Uniquely among the candidates, it hits **multiple POs and vendors at different fabrication lifecycle stages simultaneously** (in_fabrication switchgear, shipped/in-transit feeder, draft conduit), which is exactly what makes the severity-tiering mechanism legible and convincing.

**Why it beats the close runners-up even where they score higher on a single axis:** #2 (steel) and #4 (glazing) are each *more viscerally physical* on a single axis (you can almost see the beam being cut). #6 (electrical redesign) may carry an even *larger* headline number. But #2 and #4 concentrate on essentially one dominant vendor/PO, so they cannot show blast-radius fan-out or severity-tiering across lifecycle stages — the mechanism that is Downstream's actual differentiator versus the intake-gating competitors (Foundry, PO-LICE, Meridian, Jasper). #6's trigger (a load calculation) is abstract and fails the 30-second lay-judge test. Scenario #1 is the only candidate that is simultaneously top-3 on financial impact, #1 on frequency, #1 on detection difficulty, and structurally guaranteed to hit multiple lifecycle stages — the exact combination that showcases "incident response for procurement" rather than any one dimension in isolation.

## Recommendations (staged, with thresholds)
1. **Build the demo around Scenario #1** with three vendor POs at three fabrication stages. *Threshold to switch to #2 (steel):* if judges/mentors signal they want a *simpler, more physical* single-trace story over a blast-radius story, steel is the fallback.
2. **Use real artifacts.** Feed the VLM an actual (anonymized) mechanical equipment schedule and an actual switchgear submittal so the extraction is genuine, not scripted — this is the direct counter to Kaya's "just a chatbot wrapped around a prompt" penalty.
3. **Anchor the money with cited numbers**, not invented ones: switchgear/transformer lead times (Wood Mackenzie Q2 2025: switchgear ~44 weeks, power transformers 128 weeks, GSU 143–144 weeks; 2026 read >160 weeks for substation units), the non-cancellable-once-released terms, and a delay-cost-per-week figure. Show the confidence tiers explicitly rather than a single fake percentage.
4. **Rehearse the severity-ordered flip** so the highest-lifecycle-distance card (fabricating switchgear) flips first — the ordering *is* the argument.
5. **Keep a second scenario (#4 glazing) as a 20-second "and it generalizes" coda** if time allows, to prove the engine is not hard-coded to one trade.

## Caveats
- Frequency/cost/schedule/detection scores are a structured synthesis of the cited studies plus domain-pattern judgment; the literature rarely isolates a single named scenario's full five-dimension profile, and no public case study isolates the exact "HVAC-load-change → switchgear re-order → $X and Y weeks" chain (the recommendation assembles a defensible proxy chain from Wood Mackenzie lead-time data, manufacturer non-cancellation clauses, and data-center delay-cost figures).
- Several per-unit switchgear/transformer dollar figures in circulation originate from industry/vendor blogs rather than primary filings; the most defensible anchors are Wood Mackenzie lead times, POWER Magazine, Eaton's SEC-disclosed order magnitude, and actual manufacturer cancellation terms. Large-power-transformer per-unit pricing should be confirmed with a manufacturer quote before quoting a hard number on stage.
- The 1-10-100 escalation ratio is an illustrative order-of-magnitude teaching tool, not a measured constant — use it to explain the severity gradient, not as a precise multiplier.
- Rework and change-order percentages vary widely by study, region, and delivery method (design-build reduced unforeseen change orders ~87% vs. design-bid-build in one study); cite ranges, not false precision.
- Lead-time figures are 2025–2026 snapshots of an unusually constrained market (data-center/electrification demand); they are elevated versus historical norms and will move.