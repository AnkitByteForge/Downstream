# Downstream — Product Design
### Chief Product Officer / Principal Architect brief · pure product, no implementation

**The mission, unchanged, governing every decision below:**
> When an approved engineering design change occurs, automatically compute its downstream commercial impact and present evidence-backed procurement actions before procurement mistakes happen.

**Our position, restated so it disciplines every design choice:** we sit between engineering systems of record (Procore, Autodesk Construction Cloud) and commercial systems of record (SAP, Oracle ERP). We do not replace either. We are the continuous synchronization layer between engineering reality and commercial reality. Every page, object, and interaction below exists to make that synchronization visible, trustworthy, and actionable — never to become a third place where project information is filed.

---

# PART 1 — Downstream as a real SaaS platform

### Who logs in
- **Procurement Manager / Lead** — the daily user. Owns the purchase orders, vendor relationships, and commitments on a live project. Downstream exists for this person first; every other user is secondary to their workflow.
- **Project Director / Senior PM** — weekly user. Wants portfolio-level exposure, not individual events. Cares whether the project's commercial state is under control, not the mechanics of any one event.
- **Quantity Surveyor / Cost Engineer** — event-triggered user. Pulled in specifically to verify quantum on a flagged event before an action is authorized. Doesn't live in the product; is summoned by it.
- **Engineering / Design Lead** — almost never logs in. They are the *source* of events (their approvals in Procore/ACC are what triggers Downstream), not a consumer of it. If they ever open Downstream, it's because a procurement manager looped them in to confirm a "Probable" impact.
- **Admin / IT** — sets up the organization, connects systems, manages roles and notification policy. Infrequent, high-stakes sessions.
- **Executive / Owner's representative** — monthly or ad hoc. Wants one number: is commercial reality in sync with engineering reality, across the whole portfolio, right now.

### The problem they have every morning
The procurement manager does not wake up wondering "what do I need to review today?" — every other tool in their life already asks them that, and they're numb to it. They wake up with a much sharper, more anxious question: **"Did anything change last night that makes something I've already bought wrong?"** They cannot answer that question themselves without manually re-checking drawings against POs — the exact six-hours-a-week failure mode the mission exists to kill. Downstream's entire reason to exist is to have already answered that question before they open their laptop.

### What Downstream becomes in their daily workflow
Not a tool they perform a task inside. A **standing monitor of whether their commercial world still matches engineering reality** — closer to how an SRE relates to a monitoring console than how a clerk relates to a filing system. You don't "use" a monitoring console; you glance at it, and it's either quiet (good) or it isn't (act now). Downstream should occupy exactly that relationship: a tab that's open all day, silent 95% of the time, and the single most trusted signal in the 5% of the time it isn't.

### When they open it
- **First thing each morning** — a 10-second glance to confirm nothing broke overnight, the same ritual as checking a monitoring dashboard before starting work.
- **The instant a notification arrives** — a new Commercial Event pushed to them, proportional to severity (detailed under notification design, Part 2).
- **Before committing to something irreversible** — before releasing a PO to fabrication, signing a pay application, or approving a vendor invoice, as a "check clean" ritual, the procurement equivalent of checking CI status before merging code.
- **During a dispute or claim** — pulling the audit ledger as evidence of what was known, when, and what was done about it.

### When they deliberately do NOT open it
- **To search for a document.** That's Procore's job. If a procurement manager is opening Downstream to *look something up*, we have failed and become a second filing cabinet — the exact fate we must design away from.
- **To ask it a general question.** If the habit becomes "let me ask Downstream," we have become a chatbot with a procurement skin, precisely the pattern Kaya warned against and precisely what four other teams in this track already are.
- **When nothing has changed.** An empty Downstream should be *confidently, restfully silent* — no manufactured content, no "you have 0 new insights!" filler. Silence is the product working, not the product being empty.

### The primary object — and why it is not what you'd guess

The brief offers four candidates: Commercial Events, Commercial State, Alerts, Risk Objects. None of them is right as stated, but the correct answer is hiding inside two of them, at two different altitudes.

**Reject "Alert."** An alert is something you dismiss. It carries no obligation, no lifecycle, no ownership — it's a notification, not a unit of work. Alerts are exactly what breeds the fatigue and eventual ignoring that kills every monitoring product that gets this wrong. If Downstream's primary object is an alert, the product's ceiling is "smart notifications," and smart notifications get muted within a month.

**Reject "Risk Object."** Risk implies probability of future harm — a risk *register* is a compliance artifact everyone maintains and no one reads, because most listed risks never materialize and the register earns no trust. Much of what Downstream detects is not a *risk* that a PO *might* be wrong. It is a **fact**: the PO's scope has *already* diverged from approved engineering reality. Naming the object "risk" undersells the certainty tier and drags the whole product down to the credibility level of a spreadsheet nobody opens.

**The correct primary object is the Commercial Event — but it must behave nothing like a passive log entry.** A Commercial Event is the discrete, timestamped record that an approved engineering change has occurred and has been evaluated against the project's live commercial commitments. Critically, it is not merely *logged* — it is **opened, owned, and closed**, exactly like an operational incident: it has a severity, a status that must reach a terminal state, a blast radius of affected commercial artifacts, evidence, and a set of actions that must each be resolved before the event can close. This is what makes it a genuine unit of *work*, not a notification.

**"Commercial State" is real, but it is not the primary object — it is the derived read-model above it.** A project's Commercial State ("synchronized" or "N events open, 1 critical") is not a thing anyone creates or edits; it is *computed* as the live aggregate of all open Commercial Events, the same way a system's health status is computed from its open incidents rather than being its own database table. This is the correct architectural relationship: **Commercial Events are the append-only source of truth; Commercial State is the always-current summary derived from them.** It also happens to be the exact same pattern as a mature financial ledger — a detail that matters later (Part 5) because that ledger is the company's long-term asset, not just its UI convenience.

---

# PART 2 — The complete user journey

### 1. Evaluation and purchase
A GC's procurement or project-controls leadership evaluates Downstream against a live, painful memory (a change that cost real money weeks after the fact). Downstream is sold and piloted **per active project**, not as an org-wide rollout on day one — trust has to be earned project by project before it's earned company-wide. The sale is made on a single proof: "connect one project, and within a week we'll show you a change your current process would have missed."

### 2. Company onboarding
An organization account is created. SSO is configured. Roles are assigned (Procurement Manager, Project Director, QS, Admin) — deliberately mirroring the org's real reporting lines, not inventing new ones. Notification policy is set at the org level first (defaults are sane; individual projects can tighten them).

### 3. Project creation
A project is created inside Downstream as a **pointer to a real project**, not a blank workspace: its name, contract value, contract type (lump sum, GMP, cost-plus), and CSI/cost-code convention are entered once. This single field — the coding convention — matters enormously, because it is the literal key system the whole engine resolves against; getting it right at onboarding is the single highest-leverage setup step there is.

### 4. Connecting systems — the trust moment
Downstream requests **read-only access first**, always, to two categories of system: the engineering system of record (Procore/ACC — RFIs, drawing revisions, specs) and the commercial system of record (the ERP or Procore's Commitments module — purchase orders, vendors, schedule of values). The connection screen states plainly, in the admin's own language, *exactly* what is read and why — "we read RFI approvals and drawing revisions to detect changes; we read your PO log and vendor master to know what might be affected. We do not write to either system without an explicit action you approve." Write access — the ability to push a hold notice or a drafted revision query — is a **separate, later-granted scope**, requested only once the org has seen Downstream work correctly for a period on read-only data. This staged trust model is not a technicality; it is the single most important enterprise-credibility decision in the whole product, because a construction company will never grant write access to a system they haven't watched be right first.

### 5. Initial calibration
Before the first live event, Downstream ingests the project's existing documents once to build its internal key-index — the mapping between spec sections, cost codes, drawing sheet references, and the PO/vendor/schedule records that share them. This is shown to the admin as a visible, honest process with a completion state ("Project vocabulary indexed: 412 spec sections linked to 1,204 PO line items"), never as instant, unexplained magic. A system that claims to understand your project in zero seconds is a system nobody trusts with their next dispute.

### 6. Steady state — an engineering event occurs
An RFI is approved or a drawing revision is issued in the engineering system. Downstream detects it (via API/webhook where available, scheduled poll otherwise) and opens a **new Commercial Event**, in status **Detected**.

### 7. Reasoning
The event is resolved through the project's key-index to candidate commercial artifacts (purchase orders, vendors, scheduled deliveries) that share its spec section, cost code, or location. Each candidate is tagged with a **confidence tier — Certain, Probable, or Possible** — and each artifact's **lifecycle position** (draft / issued / in fabrication / shipped) is read from the commercial system to compute the event's **severity**. The event moves to status **Triaged**.

### 8. Notification — proportional, not indiscriminate
A **Severity 1** event (an already-shipped or in-fabrication commitment) pushes an immediate, individual notification to the procurement manager, by whatever channel they've configured (in-app, email, Slack/Teams). A **Severity 3–4** event (a draft PO, cheap to fix) is held and delivered in a **daily digest** instead. This single design decision is what keeps Downstream from becoming the alert-fatigue product it explicitly refuses to be — severity governs urgency of delivery, not just urgency of color.

### 9. Review
The procurement manager opens the event. They see the trigger, the blast radius grouped by confidence tier, the evidence behind every claim (each one opening to the exact source document), and a **drafted action per affected artifact** — a hold notice, a revision query, a resequencing request — already written, never left as an exercise for the human.

### 10. Approval — never bulk, always attributable
Each drafted action is approved, edited, or rejected **individually**. There is no "approve all" for anything above the lowest severity — bulk-approval of financial and contractual actions is exactly the kind of shortcut that later becomes indefensible in a dispute. Every approval records who approved it, when, and what (if anything) they changed before approving.

### 11. Synchronization
Approved actions are routed: in the current integration tier, as a drafted, ready-to-send communication (an email or PDF to the vendor, a hold flag visible in the commercial system); in a deeper integration tier, as a proposed transaction written into the ERP's own commitments workflow — never executed silently, always still subject to that system's own controls. Downstream **proposes and routes**; it never becomes the system of record for the money itself.

### 12. Closure and the ledger
As each action is completed, the event's status advances — **Detected → Triaged → Actioned → Contained → Closed**. A closed event does not disappear; it becomes a permanent, timestamped, evidence-linked entry in the project's ledger. This ledger is not a UI convenience — it is the artifact a claims consultant or auditor will eventually pull, and, at scale, the accumulated asset that lets Downstream anticipate blast radius before it even finishes traversing the graph. Every closed event makes the next prediction better; this is the compounding loop the whole company is built on.

### 13. The rollup layer
Project Directors see a weekly portfolio view of **Commercial State** across their projects (a derived read, never a separate data entry). Executives see a monthly cross-portfolio rollup. Neither of these personas ever touches an individual event unless they choose to drill in — the aggregate is designed to be sufficient on its own.

---

# PART 3 — The pages, and why each one exists (or doesn't)

### Commercial State (home)
**Purpose:** answer, in under two seconds, "is my commercial world in sync with engineering reality right now?" **User goal:** confirm calm, or find the one thing that isn't calm. **Primary CTA:** open the highest-severity open event. **Information hierarchy:** one hero status line first ("Synchronized" or "3 open events, 1 critical"), then a short severity-sorted list — nothing else competes with these two elements. **Visible immediately:** the hero status and the top event. **Deliberately hidden:** historical trends, project settings, anything that isn't "what needs me right now" — those live one click away, never on the home screen. This page must never accumulate the twenty-widget sprawl of a generic BI dashboard; if a second version of this page ever needs more than the hero line and one list, that is a sign the product is drifting back toward "another dashboard," and the extra content should be cut, not accommodated.

### Event Inbox
**Purpose:** the working queue for a procurement manager triaging more than one open event. **User goal:** work through everything open, in the order it actually matters. **Primary CTA:** open the next event. **Hierarchy:** severity first, recency second — never simple chronological order, because a Sev-4 from this morning must never outrank a Sev-1 from yesterday. **Interactions:** low-severity events can be acknowledged in bulk ("seen, no action needed"); **actions themselves are never bulk-approved**, even from this view — opening the individual event is required before anything commercial is authorized. **Hidden:** closed events (they live in the Ledger, not the working queue — an inbox that never empties isn't an inbox).

### Event Detail — the core page
**Purpose:** everything needed to understand and resolve one Commercial Event. **User goal:** decide, per affected artifact, what to authorize. **Primary CTA:** approve (or edit, or reject) the next drafted action. **Hierarchy, top to bottom:** the trigger in one sentence → severity and containment status (a visible counter: "1 of 3 contained") → the blast radius, grouped by confidence tier, each item showing its lifecycle position → for the item currently in focus, its evidence (collapsed by default, one click to expand to the exact source passage) and its drafted action. **Interactions:** clicking any claim opens its source document at the cited location; approving an action visibly advances that item's state and the event's containment counter. **Visible immediately:** severity and the containment counter — these two numbers are the entire emotional register of the page. **Deliberately hidden:** the underlying graph traversal and confidence-scoring mechanics — available one click away ("how we know"), never in the primary flow, because a procurement manager making a decision under time pressure needs the conclusion first and the mechanism only on demand.

### Evidence Explorer
**Purpose:** a narrow, secondary viewer for the *specific* source documents cited by events — not a general document repository. **User goal:** verify a claim beyond its citation snippet, usually to satisfy a skeptical vendor or a QS. **Primary CTA:** none of its own — it is only ever entered *from* a citation link. **Why it exists as a separate page and not inline:** keeping deep document inspection out of the Event Detail page protects that page's focus; keeping it one click away, rather than absent, protects trust. It must never grow into a general-purpose project document browser — that ambition belongs to Procore, and reaching for it is the single fastest way to become "just another dashboard."

### Project Graph
**Purpose:** show, for the rare user who wants it, how the key-index actually connects spec sections, cost codes, POs, and vendors — the mechanism behind every event's reasoning. **User goal:** either build initial trust during onboarding ("here is how we understood your project") or debug a specific event's reasoning ("why did this resolve here"). **Primary CTA:** none — it's an inspection surface, not a workflow. **Why it is not the home page or the hero of any demo:** it is genuinely impressive and genuinely tempting to lead with, but leading with it turns Downstream into an architecture diagram instead of a product that makes decisions for you. It earns its place as a *secondary* trust artifact, never the star.

### Integrations
**Purpose:** connection health for every engineering and commercial system, exact read/write scopes granted, and re-authentication. **User goal (admin only):** confirm both systems are syncing and understand precisely what access has been granted. **Primary CTA:** connect a new system, or upgrade a read-only connection to include write scope. **Why the scope display matters as much as the health indicator:** an enterprise buyer's security team will read this page line by line before anyone signs a contract; it must be more legible than any other integrations page they've seen, not merely functional.

### Timeline / Ledger
**Purpose:** the permanent, chronological record of every Commercial Event a project has ever raised, and exactly how it resolved. **User goal:** produce evidence for a dispute, an audit, or a retrospective — "prove what we knew and when." **Primary CTA:** export a defensible record for a specific event or date range. **Why this page is not a nice-to-have:** this is, literally, the asset described in Downstream's long-term thesis — the accumulating record of change and its cost across a project's life. It should feel less like a page and more like a **filing cabinet that has never lost a page and never will**.

### Settings / Admin
**Purpose:** org structure, roles, notification thresholds (which severities interrupt immediately versus digest), project configuration, billing. **User goal:** tune the product to the org's risk tolerance and attention budget. **Primary CTA:** save configuration. Unremarkable by design — this page's job is to be competent and boring, not memorable.

### Should there be a chat interface? **No — deliberately, and this is worth defending explicitly.**
A persistent chat box invites the user to *ask* Downstream things, which reframes the entire product as a system you query rather than a system that already told you. It is also, precisely, the pattern every generic "AI-powered construction assistant" now has, and the pattern this product's entire positioning is built to escape. The narrow exception — clicking a claim to see its source, or clicking "how we know" on an event's reasoning — is not chat. It is **evidence disclosure**, a one-directional reveal of what's already computed, not a conversational surface with a text box waiting for a question. If a future version ever needs a text box, it should be scoped so tightly (e.g., "flag this confidence tier as wrong") that it can never be mistaken for a general assistant.

---

# PART 4 — The first-time experience

### Within 5 seconds
The screen reads something like **"Commercial State: 3 open events · 1 critical."** In five seconds, a judge or a new user has already absorbed that this is a live monitor of financial exposure, not a document library — the single most important first impression the product can make, because it silently answers "is this another filing cabinet?" before anyone asks.

### Within 30 seconds
They've opened the critical event and seen a blast radius grouped honestly into Certain / Probable / Possible, each item showing not just *that* it's affected but *how far along* it already is (draft, in fabrication, shipped) — and they've clicked one citation and watched it jump to the real, highlighted source line in a real document. In thirty seconds, the product has proven two things simultaneously: it reasons in calibrated confidence rather than false certainty, and every claim is independently checkable.

### Within 2 minutes
They've watched a new event arrive on its own, watched its severity compute rather than get assigned, approved a drafted action, watched the event's containment counter tick to closed — and, in the same motion, watched a computed cost figure appear: what this would have cost found at the dock, against what it cost found here, now. In two minutes, the full loop — detect, reason, act, close, prove its own value — has played out without the user having to operate anything.

### Reducing cognitive load
Every page carries exactly one primary hierarchy (severity) and, at most, one primary action. Nothing is ever the user's job to prioritize; Downstream has already ordered the world by what matters most. The graph, the raw extraction, the model internals — all real, all impressive, all deliberately kept **one click beneath** the surface a busy procurement manager actually needs.

### Maximizing trust
Trust is earned by *never asserting past what's known*. The confidence tiers are the mechanism: "Certain" is shown with the plainness of a fact; "Possible" is shown, honestly, as a question worth a human's attention — not padded into false confidence to look more finished. A product that says "we're not sure about this one, here's why" earns far more long-run trust than one that shows a single unearned percentage and gets caught being wrong once.

### Communicating AI confidence
Never a bare percentage. Always a **named tier plus a stated reason** — "Certain: RFI-214 §2 cites Spec 23 31 13, which is PO-4471's cost code, an exact match" versus "Possible: this vendor also supplies adjacent scope on grid B, worth confirming." The tier is a claim about the *quality of the match*, and the reason is always inspectable.

### Presenting evidence
Collapsed by default, one click to expand, and expansion always lands on the **actual source document at the actual cited location** — never a paraphrase, never a second-hand summary of what the document supposedly says.

### What makes it memorable
Not a screen. A **motion**: calm, then a change lands unbidden, then severity computes live, then the blast radius resolves in front of you, then one click contains it, then the counter reaches zero, then the product tells you, in real currency, what it just saved you. A screen is looked at. A motion is remembered — because it has a beginning, a complication, and a resolution, the same shape as every story anyone has ever found memorable.

---

# PART 5 — Information architecture (the database's foundation)

**Organization** — the paying entity. Has many Users, many Projects, one notification policy (overridable per project).

**Project** — a pointer to a real construction project. Has one CSI/cost-code convention, one contract type, many Users (via role assignment), many Integrations, many Commercial Artifacts, many Commercial Events, one Graph/KeyIndex, one Ledger (the ordered history of its own Commercial Events).

**User** — belongs to an Organization, holds a Role (Procurement Manager, Project Director, QS, Admin) per Project, receives Notifications per their role's default policy.

**Commercial Event** — the primary object. Belongs to one Project. Has one Trigger (a reference to the source engineering change: an RFI, drawing revision, or spec update — an external pointer, not a copy, so the source of truth always remains the engineering system). Has a computed Severity. Has a Status that must progress toward a terminal state (Detected → Triaged → Actioned → Contained → Closed). Has many Impacts.

**Impact** — the join between a Commercial Event and a Commercial Artifact. This is the object that actually carries the interesting data: a Confidence Tier (Certain / Probable / Possible), a stated Reason for that tier, the artifact's Lifecycle Position at time of detection (which feeds the event's severity calculation), one or more Evidence references, and one Action.

**Commercial Artifact** — a superclass with three real subtypes on day one: **Purchase Order**, **Vendor**, **Delivery/Schedule Activity**. Each belongs to a Project, carries its own identity and history independent of any single event (a PO can appear in many Impacts across its life), and exposes its current Lifecycle Position (draft / issued / in fabrication / shipped / installed) as a field the reasoning engine reads directly from the connected commercial system, not one Downstream invents.

**Evidence** — a citation: a reference to an external source Document (in the engineering or commercial system of record) plus the specific location within it (a clause, a page region, a line item). Evidence belongs to an Impact's claim; the underlying Document is never copied into Downstream's own storage, only referenced, so there is never a second, potentially stale copy of the truth.

**Action** — belongs to one Impact. Has a Type (hold notice, revision query, resequencing request), a drafted Content, and a Status (Drafted → Approved/Rejected/Edited → Sent → Completed).

**Approval** — a distinct object from Action, deliberately: it is the immutable record of *who* decided *what*, *when*, separated from the action's own content so that the decision-audit-trail can never be edited after the fact, even if the action's content could theoretically be revised before sending.

**Graph / KeyIndex** — belongs to a Project. The internal substrate — spec sections, cost codes, drawing references, schedule activity IDs, and the mappings between them — that Impacts are resolved through. Mostly invisible to daily users; exposed deliberately and only on the Project Graph page.

**Integration** — belongs to a Project. Has a System type (Procore, ACC, SAP, Oracle, etc.), a Scope (read-only or read/write, and precisely which data categories), and a Health status.

**Ledger entry** — an immutable, append-only record of every state transition on every Commercial Event, Impact, and Approval within a Project. This is not a convenience log; it is the long-term asset. Nothing in this table is ever edited or deleted, only appended to — the same discipline a real financial ledger requires, because it will eventually be read by people (auditors, claims consultants, opposing counsel) who need to trust that it hasn't been.

The relationship worth underlining above all others: **the Commercial Event is the atomic unit of work; Commercial State, at the project or portfolio level, is never its own stored table — it is always computed live from the current set of open Events.** Get this one relationship right and the rest of the schema, and the whole product's honesty, follows from it.

---

# PART 6 — A day inside Downstream, as the procurement manager who has to live there

**What would annoy me:** being pinged for something that turns out to be nothing — every false positive spends trust I won't get back easily, which is exactly why severity-gated notification and honest "Possible" tiers exist rather than a single noisy stream. Being asked to re-enter information the system should already have from the systems it's connected to. Being blamed by the language of the product — an event framed as "procurement's mistake" rather than "a change that just occurred," when the fault, if any, was upstream in a design decision that hasn't reached them yet. Anything that executes on my behalf without my click — the instant Downstream sends an email or holds a PO without my explicit approval, I stop trusting it with anything.

**What would delight me:** opening the app to genuine silence, and believing it. A drafted email so accurate I only have to hit send. A vendor pushing back on a hold notice, and having the exact clause and drawing revision ready in one click instead of a half-hour dig through my inbox. Seeing, in real currency, what today's silence was worth — not a vague "we're helping," an actual number.

**What I actually need, every day:** what changed, why it's my problem, how sure the system is, and what to do about it right now. That's the whole list.

**What should never be shown to me:** any other project's data, full stop. Raw model internals or a chain-of-thought transcript — I am not equipped to evaluate that and it will only erode confidence rather than build it. Any confidence number I can't trace back to a reason. Any language that implies the AI decided something on the project's behalf — every action on screen must read as *proposed*, never as *done*, until I have said so.

---

# PART 7 — Self-critique, as the Stage 2 judge who has already seen four other teams

I have watched a bid-gate, a document copilot, a structural-substitution validator, and a five-mode analyst suite. I now open Downstream, actively looking for the moment it reveals itself as "just another dashboard." Here is where that risk actually lives, and the fix for each.

**Risk: the home screen becomes a generic BI page.** The moment "Commercial State" grows a second chart, a filter panel, or a trend widget beyond the one hero line and the top event, it starts to look like every construction analytics tool that's ever demoed to me. **Fix:** hold the line at one hero status and one list, permanently — resist every internal pitch to "add just one more widget," because that request will come and the product's whole differentiation is the discipline to say no to it.

**Risk: Event Detail reads like a Jira ticket.** A trigger, a status, some fields, an approve button — described flatly, that's a ticketing system. **Fix:** the differentiation was never going to live in the page's layout; it lives in the **motion** — severity computing in front of you, the containment counter moving, evidence resolving to a real document on click. A judge evaluating a screenshot sees a ticket. A judge watching it happen sees something they haven't seen before. This means the demo, not the static page, is where the real argument gets made — which is exactly why Part 8 exists.

**Risk: the Project Graph reads as AI theater.** A node-link diagram is the single most overused "look how smart our AI is" visual in every hackathon I've judged. **Fix:** it is not the home page, not the demo's hero moment, and every node carries a real, specific ID rather than an abstract circle — the difference between "AI theater" and "verifiable mechanism" is entirely in whether what's on screen is checkable or merely pretty.

**Risk: the whole product is, underneath the language, "a list you click on."** Strip away the severity badges and confidence tiers, and an inbox of items you open and approve is a pattern I've seen a hundred times. **Fix:** the two things no one else in this track has — an event that **counts down to a real zero** rather than just being marked read, and a **live cost figure computed from what actually happened**, not estimated — are the two elements that must appear in literally every demo, because they are the two things that don't reduce to "a list."

**Risk: the drafted-action emails look like generic auto-generated notifications.** If the output looks like "New Alert: PO-4471 flagged," it reads as a notification product. **Fix:** the email or transaction itself must visibly *be the solution*, not a description of the problem — a vendor reading it should see a ready-to-execute revision query with the clause already cited, not a summary of what went wrong.

---

# PART 8 — Demo Mode

Demo Mode is a real mode of the real product — a toggle a sales team would use for any prospect, not a hackathon-only fiction. That distinction matters: it is itself evidence that Downstream was built as an enterprise product from day one, not staged for one panel.

**Seeded projects:** one rich, believable project, pre-loaded with a populated Ledger (several already-closed prior events, so the Timeline page never looks empty and the product looks lived-in, not brand new) — plus exactly one live trigger reserved and ready to fire on cue.

**Do events trigger live?** Yes, always. The presenter never manually creates or queries the event — it **arrives**, exactly as it would on a real morning, because the entire positioning rests on Downstream being a reflex the user watches happen to them, not a tool they operate.

**Animation discipline:** minimal, and every motion maps to a real computation — the blast radius resolving artifact by artifact as the graph traversal actually completes, a severity badge computing rather than appearing pre-set, the containment counter advancing one real approval at a time. No animation exists for decoration; if it isn't backed by a real state change, it doesn't ship in Demo Mode either.

**Evidence expansion:** at least one live click, mid-demo, from a claim straight to the real, highlighted line in the real source document. This single click is the most important trust-proof moment in the whole sixty seconds and must never be allowed to be flaky — rehearse it more than any other beat.

**Graph traversal:** shown once, briefly, as the "here's how we know" moment — never lingered on, because it is supporting proof, not the headline.

**After clicking Approve:** the drafted action visibly routes (a "sent to VendorCo" confirmation), the Impact's status advances, the event's containment counter ticks toward zero, and — the closing beat — a computed cost figure appears: what this would have cost discovered at the dock, against what it cost discovered here, now. The camera then pulls back to Commercial State, where the open-event count has visibly dropped. In the last two seconds, and only there, the dormant sockets for Schedule, Cost, and Subcontracts are visible once, unexplained, beside the now-quiet Procurement panel — letting the room complete the thought themselves rather than being told it.

**Fallback:** a pre-recorded capture of this exact sequence, ready, so a flaky connection or a stalled service never costs the room the moment.

**The one unforgettable moment, restated in product terms:** *calm → a change arrives unbidden → severity computes live → the blast radius resolves with evidence attached → one click contains it → the counter reaches zero → the product states, in real currency, what it just saved → and, for a heartbeat, the room glimpses everything this becomes next.* That sequence — not any single screen — is Downstream.