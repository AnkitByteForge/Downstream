# The Reference Commercial System: A Vendor-Neutral Domain Model for Engineering-to-Commercial Impact Tracing

## TL;DR
- A credible Reference Commercial System should be built as a small set of core entities — **PurchaseRequisition, PurchaseOrder (with PO Lines and Schedule Lines), Commitment/Contract, Vendor, GoodsReceipt/Delivery, Invoice, CostCode/WBS, ProcurementScheduleItem, ChangeOrder, and OrgScope** — each with an explicit lifecycle state machine, because every real ERP (SAP S/4HANA, Oracle Fusion, ERPNext, Dynamics 365, IFS) converges on these same objects even though it names them differently.
- The single most important design decision is to model the **commitment** as a first-class object distinct from both the PO and the actual cost: an approved engineering change propagates into the commercial system as a *commitment/budget adjustment* first (committed cost changes long before any invoice), and it is exactly this committed-cost delta on a shared **cost code / WBS element** that lets Downstream trace an engineering trigger to specifically affected POs, vendors, and deliveries.
- Faithfulness to reality requires three things most naive models omit: (1) **line-item and schedule-line granularity** (a PO line splits into multiple dated delivery schedule lines, each independently received); (2) **org-scoping dimensions** (SAP Company Code / Plant / Purchasing Organization; Oracle Business Unit) that constrain visibility; and (3) a **fabrication/expediting sub-lifecycle** (PO issued → drawings approved → released for fabrication → in fabrication → FAT/inspection → shipped → delivered → installed) for long-lead engineered equipment, which is where engineering changes do the most commercial damage.

## Key Findings

**1. All five ERPs share the same procure-to-pay backbone, differing mainly in naming and org-structure.** The universal chain is: Requisition → (approval) → Purchase Order → (release/approval) → Goods Receipt/Delivery → Invoice → Payment, with a three-way match (PO/receipt/invoice) as the control gate. SAP calls the requester document a Purchase Requisition (PR) and converts it via ME21N; Oracle Fusion calls it a Requisition converted through the Document Builder; ERPNext uses a Material Request converted to a Purchase Order; Dynamics and IFS use purchase requisitions/orders. This convergence is what makes a vendor-neutral model viable.

**2. The purchase requisition is an internal request, not a commitment; the PO is the legal commitment.** A PR "is not an order. It is a signal that a department or a planning run needs something procured" and "has to be approved before it can be converted" (SAP MM guidance). In project-based procurement, PRs are frequently generated automatically — in SAP PS, network activities and Easy Cost Planning "Execution Services" auto-generate PRs tied to a WBS element; ERPNext auto-creates Material Requests at reorder level.

**3. Site/field material requests are modeled as a lighter-weight, inventory-oriented document distinct from a formal PR.** ERPNext's Material Request supports purposes of **Purchase, Material Transfer, Material Issue, Manufacture, and Customer Provided**, and can be satisfied either by a new purchase (→ PO) or an internal warehouse transfer (→ Stock Entry) — capturing the real distinction between "buy this" (procurement) and "send this from another location/stores" (fulfillment from existing stock).

**4. The PO lifecycle is a multi-state machine with clearly named states in each ERP.** Oracle Fusion Cloud documents 15 PO header statuses verbatim (Oracle "Using Procurement" 25D): **Canceled, Closed, Closed for Invoicing, Closed for Receiving, Finally Closed, Incomplete, On Hold, Open, Pending Acknowledgment, Pending Approval, Pending Change Approval, Pending Signature, Rejected, Sent for Signature, Withdrawn** — where, e.g., "Finally Closed" means "all receiving and invoicing activity on the order has completed, and it can now be archived and purged." SAP uses a **release indicator** (Blocked → Released) plus separate fulfillment flags — the **Delivery Completed Indicator (EKPO-ELIKZ)** for materials and the **Final Entry Sheet indicator** (services), and an informational **Final Invoice Indicator**.

**5. Commitments are a first-class concept, separate from PO and actuals.** A PO creates a *commitment* — a future obligation — long before the invoice lands. In SAP S/4HANA, per the SAP Help Portal "Predictive Commitments Management," "the commitment for the predicted expense is created in a prediction ledger 0E" and is reduced when the follow-on valuated goods receipt is posted; construction ERPs (JD Edwards, Trimble Vista, Foundation, Sage Intacct) maintain a commitment/PA ledger where a subcontract or PO posts "total committed" cost against a job + cost code, relieved as invoices/progress payments post. Approved change orders raise committed cost immediately.

**6. Cost codes are structured differently per system and must be normalized.** Construction practice uses CSI MasterFormat: 50 divisions numbered 00–49 (with divisions 15–20, 24, 29, 30, 36–39, 47 and 49 reserved for future use), with six-digit section codes in the format XX YY ZZ — e.g., 03 30 00 = Division 03 (Concrete) → Section 30 (Cast-in-Place) → General. SAP uses WBS elements (hierarchical, in SAP PS). Oracle Projects uses a task-based WBS plus a separate Cost Breakdown Structure (CBS). Contractors often use custom cost-code structures. A normalized model needs a generic `CostCode` node that can carry a standard reference (MasterFormat) plus a system-native identifier.

**7. Deliveries are tracked at schedule-line granularity with partial-receipt states.** A SAP PO line can carry multiple delivery schedule lines with distinct dates; goods receipts are posted against them (MIGO), producing partial-delivery status (e.g., production-order analog PDLV = partially delivered, DLV = fully delivered) governed by over/under-delivery tolerances. A confirmation control key can require an inbound delivery / advance shipping notification before goods receipt, giving visibility of expected GR dates for long-lead materials.

**8. Procurement schedules link to project schedules via required-on-site (ROS/ROJ) dates and lead times.** Construction practice computes the latest "order-by" date by working backward from the required-on-site date, subtracting fabrication + transit + submittal-approval lead time. This is the crucial link that lets a commercial object (a PO/delivery) be tied to a schedule activity: "this material must arrive by this date to support this activity."

**9. Invoices go through three-way match with construction-specific retention.** The three-way match compares PO, goods receipt, and invoice; construction extends this to job/phase/cost-code matching and applies **retainage/retention** — a 5-to-10-percent holdback on each construction progress payment, released once work is substantially or fully complete (federal projects are capped at 10% under FAR 52.232-5; a typical private rate is 5%, "of which half is released at completion and half at the end of the defects liability period"). Retention is tracked via a schedule of values and AIA-style pay applications.

**10. Commercial approvals are value-threshold, multi-level release strategies — structurally different from engineering approvals.** SAP release strategies use classification characteristics (net value via CEKKO-GNETW, plant, purchasing org) to assign approval sequences (e.g., <$500 manager only; >$10,000 adds department head). This is fundamentally a *financial-authority* hierarchy keyed on money and org unit, whereas engineering approvals (RFI/submittal/ASI) are *technical-authority* workflows keyed on discipline and design correctness.

**11. Engineering changes propagate into procurement as an ordered causal chain.** The realistic sequence: engineering trigger (approved RFI / drawing revision / ASI) → affected spec section / cost code identified → change order raised → committed cost / budget adjustment on the WBS → affected PO lines identified (re-scope, cancel, or amend) → PO amendment (new release/approval cycle) → delivery schedule impact → invoice/three-way-match implications. Committed cost changes first; actuals follow later.

**12. Org-structure dimensions constrain visibility and must be modeled generically.** SAP scopes procurement through Client → Company Code (legal entity) → Purchasing Organization → Plant → Storage Location, with vendor master data maintained at general/company-code/purchasing-org levels; Oracle uses Business Units. A vendor-neutral model needs a generic `OrgScope` composite (company_code / plant / business_unit / purchasing_org) attached to POs, vendors (per-scope views), and deliveries.

**13. A sufficient Reference Commercial System is ~11 core entities plus their state machines and the explicit join to the Reference Engineering System.** See Details for the full schema.

## Details

### A. Purchase Requisitions (Topic 1)
A purchase requisition (PR) is an internal request that signals a need to procure; it is not a commitment to a vendor. In SAP MM it holds material number, quantity, delivery date, plant, and account assignment, and once it clears its release strategy a buyer converts it into a PO (transactions ME21N/ME57/ME58). Requisitions can be created manually or automatically by MRP runs, maintenance/production orders, or **network activities** in SAP PS. In project-based procurement the PR carries an **account assignment to a WBS element**, which is what ties the eventual spend to a project cost structure. Oracle Fusion Cloud creates a Requisition (manually or from catalog), routes it through a requisition approver, then processes requisition lines into a PO via the Document Builder; catalog/interface-sourced requisitions can auto-convert to POs without buyer action. ERPNext converts a Material Request into a PO, RFQ, or Supplier Quotation in one step.

**Requisition-to-PO workflow (normalized):** create PR → approve (release strategy) → source/select vendor → build PO from one or more approved PR lines → PO enters its own approval cycle. A single PR line may be split across multiple POs, and multiple PR lines may be consolidated onto one PO (Oracle explicitly supports viewing requisition life cycle grouped by resulting PO number).

### B. Material Requests vs. Purchase Requisitions (Topic 2)
Site/field material requests differ from formal PRs in that they are inventory-and-fulfillment oriented, not necessarily procurement-oriented. ERPNext's Material Request models this cleanly with a **purpose** field: Purchase (→ PO), Material Transfer (→ Stock Entry from another warehouse), Material Issue, Manufacture, Customer Provided. A field crew requesting material may be satisfied from existing site stores (a transfer/issue) rather than a new purchase. The domain lesson: a material request is a demand signal that may resolve either to a procurement action (creating/affecting a PO) or an internal stock movement (no commercial impact). For Downstream this matters because only the procurement-resolving branch produces commercial (PO/vendor/delivery) impact.

### C. Purchase Orders (Topic 3)
**Lifecycle states (synthesized from Oracle + SAP):**
- *Draft/Incomplete* — being authored.
- *Pending Approval / Blocked* — submitted, in release strategy.
- *Approved/Released → Open* — approved and open for fulfillment; may require *Pending Signature/Sent for Signature* for contract POs.
- *Pending Acknowledgment → Acknowledged* — supplier confirmation (Oracle "Pending Acknowledgment"; SAP order acknowledgment / confirmation control).
- *Amended / Pending Change Approval* — a change order/amendment triggers a new approval cycle.
- *On Hold* — receiving/invoicing temporarily suspended.
- *Closed for Receiving / Closed for Invoicing* — partial closure states.
- *Closed / Finally Closed* — no further activity; archivable.
- *Canceled / Rejected / Withdrawn* — terminal non-fulfillment states.

**Line-item structure:** PO header (vendor, org scope, currency, terms) → PO lines (material/service, quantity, price, cost-code/WBS account assignment) → schedule lines (dated delivery quantities). SAP allows separate delivery schedule lines within a line item, each with its own date; Oracle models Order → Line → Schedule → Distribution, where the distribution carries the project/task/cost account assignment.

**Relationship to contracts/commitments and cost codes:** POs may be issued against outline agreements / supplier agreements / blanket contracts (SAP outline agreements & scheduling agreements; Oracle supplier agreements). Each PO line's account assignment points at a cost code/WBS element, and the open (undelivered/uninvoiced) PO value is the committed cost on that code.

### D. Vendors (Topic 4)
**Master data structure (SAP, as the richest example):** vendor data is maintained at three independent levels — **General/Client data** (name, address — valid everywhere), **Company Code data** (accounting/payment — needed before invoice/payment), and **Purchasing Organization data** (purchasing terms). This means a single vendor is one master record with scope-specific views; a vendor may be usable for purchasing in one org scope but blocked in another (SAP supports blocking at company-code, purchasing-org, or source-list/plant level). Oracle maintains a Supplier profile with business-unit-specific site assignments.

**Qualification/prequalification:** suppliers are evaluated before they can bid/receive awards — assessing financial stability, technical capability/capacity, past performance, health & safety, quality assurance, and legal standing; public agencies maintain formal prequalified-vendor lists with expiration dates.

**Performance tracking:** ongoing evaluation on quality, delivery reliability, cost, and responsiveness via scorecards; SAP has vendor evaluation, IFS has supplier performance management.

**One vendor → many POs/commitments:** a vendor relates to many POs and commitments across a project/portfolio; the model needs Vendor 1—* PurchaseOrder and Vendor 1—* Commitment, scoped by org unit. A purchasing info record links a specific vendor+material combination with default pricing.

### E. Deliveries (Topic 5)
Goods receipt (SAP MIGO, movement type 101) posts received quantity against a PO schedule line, updating delivery status and reducing the commitment while creating actual cost. Partial deliveries are normal: over/under-delivery tolerances govern acceptance; a line accrues partial-delivery status until the **Delivery Completed Indicator (ELIKZ)** is set. A **confirmation control key** can require an inbound delivery / shipping notification (advance ship notice) before GR, giving in-transit visibility and expected-GR dates for long-lead items. Received goods may route to **Unrestricted Use, Quality Inspection, or Blocked stock**.

**Delivery status state machine (normalized):** *Scheduled → (Confirmed/ASN received) → In Transit → Partially Delivered → Delivered/Received → (Inspection) → Accepted / Rejected*. Delivery records connect to inventory/site receiving via the goods receipt posting and, in construction, to a Material Receiving Notice (MRN) with OS&D (Over, Short & Damaged) reporting.

### F. Schedules (Topic 6)
Procurement/delivery schedules link to the project schedule through **required-on-site (ROS) / required-on-job (ROJ) dates** and **lead-time management**. Working backward from the schedule activity's need date, the latest order-by date = need date − (submittal/approval + fabrication + transit + contingency). SAP PS ties this together: a network activity can be externally processed, auto-generating a PR whose commitment sits on the WBS; the schedule dates flow to the PR/PO delivery date. The domain object that expresses "this material must arrive by this date to support this activity" is a **ProcurementScheduleItem** linking a PO line/delivery to a ScheduleActivity with a required-on-site date and computed order-by date. Long-lead items (≥4 weeks, often much longer for engineered equipment) are flagged and expedited.

### G. Invoices (Topic 7)
Invoice processing centers on the **three-way match** (PO ↔ goods receipt ↔ invoice) with tolerance thresholds; failures place the invoice on hold. Construction extends this to matching every invoice to job/phase/cost-code and adds **four-way matching** (inspection) where quality verification is required. **Retention/retainage** (commonly 5–10%) is withheld on each progress payment against a schedule of values, accumulated as a retention-payable balance, and released at substantial/final completion (often half at substantial completion, half at the end of the defects-liability period). Invoice status (Draft → Matched/On Hold → Approved → Paid; plus Oracle life-cycle amounts: Invoiced, Partially Paid, Unpaid) relates directly to PO and delivery status: an invoice cannot fully three-way match beyond received quantities, and partial deliveries force partial invoicing.

### H. Commercial Approvals (Topic 8)
Commercial approvals are **value-threshold, multi-level release strategies** keyed on money and org unit. SAP builds release strategies from characteristics (net value via CEKKO-GNETW, plant, purchasing org), release groups, release codes, release indicators — e.g., a strategy where release points 1–4 must approve before the CEO (release point 5). Requisitions can be released at item level; external POs typically at document (header) level. Oracle uses approval hierarchies on requisitions and POs; Dynamics uses workflow approval stages with budget control.

**Contrast with engineering approvals:** commercial approval authority is financial (who can commit how much money, scoped by legal entity/purchasing org), triggered by dollar thresholds and PO/invoice value. Engineering approval authority is technical (discipline lead, engineer of record, architect) triggered by design correctness/constructability on RFIs, submittals, ASIs. Both are multi-level sign-off state machines, but they key on different attributes and different objects.

### I. Cost Codes (Topic 9)
- **CSI MasterFormat**: 50 divisions numbered 00–49, six-digit section codes (e.g., 03 30 00 = Concrete → Cast-in-Place → General), the de facto US standard, preferred for government/large commercial work; UniFormat is the elemental (building-system) complement.
- **SAP**: WBS elements in SAP PS form a hierarchical cost structure; PRs/POs account-assign to WBS elements; cost planning can be at WBS or network-activity level.
- **Oracle Projects**: task-based WBS plus a separate reusable **Cost Breakdown Structure (CBS)**; expenditures carry project/task/expenditure-type.
- **Dynamics 365**: project WBS + cost categories.
- **Custom contractor codes**: firm-specific structures, often MasterFormat-derived.

**Normalization approach:** a generic `CostCode` entity carrying (a) a normalized standard reference (e.g., MasterFormat section), (b) the system-native code/ID, (c) a hierarchy pointer (parent), and (d) org scope. This is the join key between engineering (SpecSection) and commercial (PO line) sides.

### J. Project Cost Control (Topic 10)
Real project-controls practice aligns with AACE International's **Total Cost Management (TCM)** framework — defined by AACE as "the effective application of professional and technical expertise to plan and control resources, costs, profitability and risk… a systematic approach to managing cost throughout the life cycle of any enterprise, program, facility, project, product or service" (TCM Framework, 2nd ed., ed. H. Lance Stephenson, CCP, 2015/rev. 2019), structured around the plan-do-check-act (PDCA) cycle. Per cost code/WBS element, practice tracks: **Budget (baseline, current) — Committed cost — Actual cost — Forecast/Estimate-to-Complete (ETC) — Estimate-at-Completion (EAC)**, with variance analysis. Committed cost = awarded contracts + POs + approved change orders; pending change orders and uncommitted costs represent risk exposure often carried in an Anticipated Cost Report. A **change order requires a budget/funding source** (supplemental appropriation/AFE, PO, or contingency drawdown); until approved it is a *pending* change (not in current budget); once approved it moves into the current budget and raises committed cost. Contingency is drawn down against risk events/change orders and reported distinctly (approved drawdowns, pending, released, remaining).

**How an engineering change flows in:** approved engineering change → cost/schedule impact assessed → change order created (pending) → on approval, budget adjustment + new/changed commitment on the affected WBS/cost code → forecast (EAC) updated. Committed cost moves before actuals.

### K. Engineering-Change Propagation, Concretely (Topic 11)
From the ERP's perspective, after an approved engineering change (e.g., an approved RFI or drawing revision) is received, the causal chain is:

1. **Trigger ingested**: the change references a spec section / drawing item / discipline.
2. **Cost-code / WBS mapping**: the affected spec section resolves to one or more cost codes/WBS elements.
3. **Affected commitments identified**: open PO lines and subcontract commitments carrying those cost codes (and matching spec_section_refs) are found — these are the candidate impacts.
4. **Commitment/budget adjustment**: a change order is raised; on approval the WBS budget and committed cost are adjusted (SAP predictive commitment ledger 0E updates immediately; availability control may check budget at PO save).
5. **PO state changes**: affected PO lines are amended (→ Pending Change Approval / new release cycle), cancelled (→ Canceled), or newly created; quantities/prices/dates change.
6. **Delivery schedule impact**: schedule lines re-dated; if a line is in fabrication or shipped, change is costlier and may trigger scrap/rework (this is why the fabrication sub-lifecycle matters).
7. **Invoice/match impact**: already-received/invoiced quantities constrain what can change; retention and already-paid amounts factor into recovery.
8. **Forecast update**: EAC/ETC on the cost code updated; contingency drawn if needed.

Object update order: CostCode/WBS budget & commitment → PO line (state + values) → Delivery/ScheduleLine → Invoice implications → Forecast.

### L. Org-Structure / Scoping (Topic 12)
SAP's procurement org hierarchy: **Client → Company Code (legal entity, accounting) → Purchasing Organization (negotiates terms, procures for one/more plants/company codes) → Plant → Storage Location**, with Purchasing Groups as buyer roles. Assignments constrain what a purchasing org can buy for which plants/company codes; a purchasing org may be plant-specific, company-specific, or cross-company (central). Vendor master views are scoped to company code and purchasing org. Oracle scopes through Business Unit (procurement BU, requisitioning BU, sold-to).

**Generic representation:** an `OrgScope` value object = {company_code, plant, business_unit, purchasing_org}. Every PO, vendor-view, delivery, and cost code carries an OrgScope; visibility/traceability queries must respect it (a PO in Plant A is not automatically visible to Plant B; a vendor blocked in one purchasing org may be active in another). This matches Downstream's frozen CommercialArtifactSnapshot org-scoping fields (company_code/plant/business_unit).

### M. The Ideal Reference Commercial System — Domain Model (Topic 13)

**Core entities, key fields, and state machines:**

1. **PurchaseRequisition** — {id, requester, org_scope, cost_code_ref, spec_section_ref (nullable), needed_by_date, status}. States: Draft → Pending Approval → Approved → Converted (→PO) / Rejected / Cancelled. Source: manual, MRP, or schedule-activity-driven.

2. **MaterialRequest** (field/site) — {id, purpose (Purchase | Transfer | Issue | Manufacture), site/location, cost_code_ref, needed_by_date, status}. Resolves to either PO (procurement branch) or StockMovement (fulfillment branch).

3. **PurchaseOrder** — header {id, vendor_ref, org_scope (company_code/plant/purchasing_org), currency, payment_terms, contract_ref (nullable), status}. States: Draft/Incomplete → Pending Approval (Blocked) → Approved/Released → Open → (Amended/Pending Change Approval) → Closed for Receiving / Closed for Invoicing → Closed → Finally Closed; plus Canceled/Rejected/Withdrawn/On Hold. Flags: acknowledged, delivery_completed, final_invoice.
   - **POLine** — {line_no, item/service, description, quantity, uom, unit_price, value, cost_code_ref, spec_section_refs[], lifecycle_position}. lifecycle_position ∈ {draft, issued, in_fabrication, shipped, installed} (the fabrication/expediting sub-lifecycle).
   - **POScheduleLine** — {schedule_no, quantity, required_on_site_date, promised_date, linked_schedule_activity_ref, delivery_status}.

4. **Commitment** — {id, source (PO | Subcontract | ChangeOrder), po_ref, cost_code_ref, org_scope, committed_amount, relieved_amount, open_amount, status}. States: Open → Partially Relieved → Fully Relieved / Cancelled. This is the object that carries committed cost against a cost code and is the primary quantitative impact surface.

5. **Contract/OutlineAgreement** — {id, vendor_ref, type (blanket | scheduling agreement | subcontract), value, retention_pct, org_scope}. Parent of POs/releases.

6. **Vendor** — {id, name, general_data, per-scope views [{org_scope, purchasing_terms, blocked_flag}], qualification_status (Prospective → Prequalified → Approved → Suspended/Blacklisted), performance_score}. Vendor 1—* PurchaseOrder, 1—* Commitment.

7. **Delivery/GoodsReceipt** — {id, po_line_ref, po_schedule_line_ref, quantity_received, receipt_date, stock_type (Unrestricted | Quality Inspection | Blocked), status, mrn_ref}. States: Scheduled → Confirmed/ASN → In Transit → Partially Delivered → Delivered → Accepted / Rejected.

8. **Invoice** — {id, vendor_ref, po_ref, matched_receipt_refs[], gross_amount, retention_withheld, net_amount, match_status (Unmatched | Matched | Exception/Hold), status}. States: Draft → Matched/On Hold → Approved → Partially Paid → Paid.

9. **CostCode/WBSElement** — {id, standard_ref (MasterFormat section), native_code, parent_ref, org_scope, budget_baseline, budget_current, committed, actual, etc, eac}. The normalization anchor.

10. **ProcurementScheduleItem** — {id, po_line_ref, linked_schedule_activity_ref, required_on_site_date, lead_time, order_by_date, status}. Expresses schedule dependency.

11. **ChangeOrder / CommercialEvent adjustment** — {id, trigger_ref (→ engineering RFI/DrawingVersion/DesignChange), affected_cost_codes[], affected_po_lines[], budget_delta, commitment_delta, status (Pending → Approved → Rejected)}.

12. **OrgScope** (value object) — {company_code, plant, business_unit, purchasing_org}.

**Explicit joins to the Reference Engineering System:**
- `POLine.cost_code_ref → CostCode ↔ SpecSection` (spec sections map to MasterFormat cost codes; POLine.spec_section_refs[] links directly to SpecSection nodes).
- `POScheduleLine.linked_schedule_activity_ref → ScheduleActivity` (procurement/delivery need-dates tie to schedule activities).
- `ChangeOrder.trigger_ref → RFI / DrawingVersion / DesignChange / Submittal` (the engineering trigger that initiates commercial impact).
- `Delivery` and `POLine.lifecycle_position` connect to DrawingItem/DrawingVersion via the affected physical scope (what is being fabricated/installed).
- `Vendor` ↔ Submittal (a submittal is often produced by the same vendor holding the PO — the submittal-approval gate is a lead-time input to ProcurementScheduleItem).

**State machines that must exist (minimum):** PO lifecycle; PO fabrication/expediting sub-lifecycle (draft → issued → drawings/submittals approved → released for fabrication → in fabrication → fabrication complete → FAT/inspection (Inspection Release Notice) → shipped/in-transit → delivered (Material Receiving Notice) → installed); Delivery status; Invoice status; Commitment status; Vendor qualification; ChangeOrder status. These are what let Downstream reason about *how much* impact a change causes as a function of *how far along* the affected PO lines are (a change hitting an in_fabrication line is far costlier than one hitting a draft line).

Note on the fabrication sub-lifecycle: EPC/construction expediting practice consistently names artifacts along this chain — order acknowledgment, vendor-drawing review/return, Start of Manufacturing (SOM), Factory Acceptance Test (FAT) gated by an Inspection Release Notice (IRN), Cargo Ready (CR)/Shipping Release Notice (SRN), Arrival at Site (AAS), and site receiving via a Material Receiving Notice (MRN) with Over/Short/Damaged (OS&D) reporting. There is no single normative standard, so the five-state enum (draft/issued/in_fabrication/shipped/installed) is the right level of abstraction for Downstream, with the finer artifacts available as sub-states if needed.

## Recommendations

1. **Model the Commitment as a first-class object now, not as a derived PO attribute.** It is the quantitative impact surface: committed cost changes before actuals (SAP's predictive commitment ledger 0E updates at PO save, before any goods receipt), and it is what cost control (and Downstream's Impacts) reason about. Threshold to revisit: if test scenarios only ever need "is this PO affected?" (boolean) and never "how much committed cost moves," a lighter model suffices — but that would undercut credible impact reasoning.

2. **Implement the PO fabrication/expediting sub-lifecycle (draft → issued → in_fabrication → shipped → installed) as an explicit enum on PO lines**, exactly matching Downstream's frozen lifecycle_position. This is the single most valuable realism feature for demonstrating engineering-to-commercial impact, because impact severity scales with lifecycle position. Seed test data with lines at each stage.

3. **Adopt a normalized CostCode entity carrying both a MasterFormat standard_ref and a system-native code.** Use MasterFormat section codes (format XX YY ZZ) as the canonical cross-walk between SpecSection (engineering) and POLine (commercial). This directly enables `PurchaseOrder.cost_code links to SpecSection`.

4. **Attach an OrgScope value object to every PO, vendor-view, delivery, and cost code, and enforce it in traceability queries.** Build at least one multi-plant/multi-company test scenario so impact tracing must respect scope boundaries (proving Downstream won't wrongly flag a PO in another legal entity, and correctly handles a vendor blocked in one purchasing org but active in another).

5. **Model deliveries at schedule-line granularity with partial-receipt states and ASN/in-transit visibility.** Include a confirmation-control analog so long-lead items expose expected-delivery dates — this is what makes "a change now will hit a shipment already in transit" reasoning possible.

6. **Represent the change-order → budget/commitment adjustment explicitly as the ChangeOrder entity linking engineering trigger to affected cost codes and PO lines**, with Pending vs. Approved states (pending changes are risk exposure, not yet in current budget) — mirroring AACE anticipated-cost / contingency practice.

7. **Keep commercial approval (value-threshold, org-scoped release strategy) structurally separate from engineering approval (discipline/technical).** Model both as multi-level sign-off state machines but key them on different attributes so Downstream can reason about them independently and about their hand-off.

8. **Benchmark for "enough realism":** the model is sufficient when a single seeded engineering trigger (approved RFI on a spec section) can be traced deterministically to (a) specific affected PO lines with lifecycle positions, (b) their vendors and org scopes, (c) affected delivery schedule lines and their required-on-site dates/schedule activities, and (d) a quantified committed-cost/budget delta on the cost code — with retention and already-invoiced amounts correctly excluded from recoverable impact. If any of those four cannot be produced, add the missing entity/state.

## Caveats
- **Naming and enums are partly configurable, not universal.** Oracle Fusion's 15 PO header statuses are documented and fixed; SAP release-indicator intermediate labels (e.g., "Partial Release") and changeability codes are customer-configured, so the model should treat state names as a normalized superset, not a copy of any one vendor.
- **The EPC fabrication/expediting milestone sequence has no single normative standard.** The draft → issued → in_fabrication → FAT → shipped → delivered → installed chain is synthesized from multiple practice sources (EPC contract exhibits, contractor expediting procedures, project-controls guides); contractors name and subdivide these differently (IRN/SRN, MRN, OS&D, SOM/CR/AAS). Treat it as representative industry practice.
- **Vendor performance scoring and prequalification specifics vary widely** by owner, jurisdiction, and public/private status; the model should carry a generic qualification_status and performance_score rather than a fixed scheme.
- **Some ERP marketing sources overstate integration/AI capabilities**; the domain-model facts here rely on official SAP/Oracle documentation and established construction-cost-control practice, not vendor marketing claims. Cost-overrun statistics cited in vendor blogs (e.g., "35% of projects exceed budget," "79% average overrun") come from secondary sources and should be treated as indicative, not authoritative.
- **This model deliberately omits payment/treasury, tax, and landed-cost detail** as out of scope for engineering-to-commercial impact tracing; if impact reasoning later needs cash-flow timing, add Payment and PaymentSchedule entities.