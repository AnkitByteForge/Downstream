# Connector Layer — Validated Against Real Enterprise Systems
### Principal Integration Architect review · brutally realistic, no new architecture

## Verdict up front

The Connector Layer's shape — one interface, two envelope types, pull-or-push adapters — is the right shape. But **both envelopes, as designed, assume a cleaner world than any of these five systems actually offer.** Every one of them shares a pattern you did not originally design for: **events are thin, and the real data requires a callback.** SAP's Event Mesh sends you a changed field list and makes you call OData for the rest. Oracle's Business Events require Oracle Integration Cloud as a mandatory middleware hop before you ever see a payload, and even then it's a pointer, not the object. Procore's webhooks are famously minimal and push teams toward "webhook to know something changed, REST call to know what changed." This is not a coincidence — it is how every mature enterprise system protects itself from becoming a data-broadcast liability. **Your `EngineeringEventEnvelope` and `CommercialArtifactSnapshot` need to be built around "thin notification plus enrichment fetch" as the default case, not the exception.**

Second, and just as important: every system in this list has **an organizational scoping dimension your model doesn't have a field for** — SAP's Company Code/Plant, Oracle's Business Unit, Procore's permission-scoped integration user, ACC's per-module licensing. Ignore these and your "Certain" confidence tier will occasionally be certain about the wrong purchase order, or confidently wrong because the credentials that fetched it couldn't see half the project. That is not a hypothetical edge case; it is the normal condition of enterprise data.

Third: two of your five identifiers are not what you think they are. Procore's `RFI-214` and ACC's `display_id` are cosmetic — the real key is an opaque integer or GUID, and the human-readable number is a separate, editable field. Get this backwards and your citations point to the wrong thing the first time someone renumbers an RFI log.

None of this breaks the architecture. It sharpens two envelope schemas and disciplines how the mocks must lie to you exactly as convincingly as the real systems will.

---

## Procore

**1. Integration model.** REST API (versioned — v1.0/v1.1/v2.0 coexist across different resources), registered through Procore's Developer Portal, with an actual Sandbox environment (`login-sandbox.procore.com`) for pre-production testing — use it; it is not optional for a serious integration. Procore is unusual on this list in one respect worth stating plainly: **it is not cleanly an "engineering system."** It natively owns both RFIs/drawings/submittals *and* Commitments/Change Orders/Budget — meaning a single Procore connection can, for many customers, satisfy both your Engineering and Commercial connector families at once. Your clean two-family split needs to become a capability flag on a connection, not a hardcoded type.

**2. Authentication model.** OAuth 2.0, authorization-code grant, is the supported and documented path — and it is **user-delegated by design**, not a true service-account model. Nearly every endpoint is permission-scoped to whichever real Procore user the integration is connected as. In practice this means Downstream needs a dedicated, deliberately-provisioned "integration user" per customer, with a `permission_template_id` broad enough to see RFIs, Submittals, Commitments, and Budget simultaneously — and getting that provisioned is a customer IT/security conversation, not a checkbox.

**3. Event model.** Webhooks exist and are the documented best practice over polling — registered per resource type and event (created/updated/deleted), delivered to a callback URL. Payloads are minimal by design; production integrations consistently report needing a REST call back to get the full resource. Rate limit: 3,600 requests/hour per OAuth `client_id`, with `X-Rate-Limit-Remaining` headers to respect and standard `per_page`/`X-Total` pagination.

**4. Objects exposed.** RFIs, Submittals (with logs and ball-in-court status), Drawings/Documents, the tiered Change Event → Potential Change Order → Commitment Change Order → Prime Contract Change Order chain, Commitments (subcontracts/POs), Budget line items and cost codes, Daily Logs, Punch Items, Inspections.

**5. Identifiers.** A numeric `id`, always scoped under `company_id`/`project_id` in the URL path — this is the real primary key. The human-facing "RFI-214" is a separate, **editable** display number. Cost codes are configurable per company and often, but not always, mapped to CSI MasterFormat.

**6. APIs Downstream would realistically consume.** RFI show/index + webhook, Submittal show/index + webhook, Change Event / PCO / CCO read endpoints, Commitments show/index, Budget/cost-code list, Document/Drawing revision metadata, the Company/Vendor directory.

**7. Write operations possible.** Yes, genuinely — creating Change Events, posting RFI responses/comments, attaching documents to a Commitment Change Order, are all real, permission-gated write paths. A drafted Action could, in a deeper integration tier, land directly inside Procore as a comment or a new Change Event rather than only as an outbound email.

**8. Limitations.** The permission-scoped-user model is the sharpest one: a partially-scoped integration user will silently return incomplete data rather than erroring, which means an under-provisioned connection can produce a confidently wrong Commercial Event. Webhook payload richness is inconsistent across resource generations. API version fragmentation (v1.0 vs v1.1 vs v2.0 for different resources) means the connector's internal mapping layer must be maintained resource-by-resource, not assumed uniform.

**9. What the Connector Interface should normalize.** The Procore adapter must be able to emit into *both* envelope families from one connection, and must record which permission scope fetched each object.

**10. Envelope check.** Add `display_number` (separate from the true `source_id`), and add a scope indicator — call it `acting_credential_scope` — recording what the integration user could actually see at fetch time. Without it, a "Certain" tier from an under-scoped fetch is indistinguishable from a genuinely certain one, which is exactly the kind of false confidence the whole product is built to refuse.

---

## Autodesk Construction Cloud

**1. Integration model.** Autodesk Platform Services (APS, formerly Forge) — a family of REST APIs (Data Management, Construction.Issues, Construction.RFIs, Cost Management, Account Admin) under one token layer, registered in the APS Developer Portal. Data Management is hierarchical: Hubs → Projects → Folders → Items → Versions.

**2. Authentication model.** OAuth2 3-legged for user-delegated writes; 2-legged (client_credentials) for reads and admin calls; and, notably better than most on this list, **Service Accounts (SSA)** — JWT assertions signed with an RSA private key — exist specifically as the headless, server-to-server alternative. Even so, many write calls under a 2-legged or SSA token still require an explicit "act on behalf of" user header, because ACC enforces per-user attribution regardless of how the token was issued.

**3. Event model.** A native, mature Webhooks API (inherited from BIM 360's Data Management system, so it long predates ACC's construction-specific modules) — scoped to a hub/project/folder, firing on item or issue-status changes. Push-based and reliable by construction-tech standards.

**4. Objects exposed.** Construction.Issues (a supertype spanning design, safety, quality, and — depending on the customer's ACC generation — RFIs either as a dedicated Construction.RFIs API or as an Issue subtype; this ambiguity is real and must be probed per customer, not assumed). Cost Management API (budgets, contracts, change orders — meaning ACC, like Procore, can also be a commercial-side source where licensed). Submittals API. Documents via the Data Management version chain — which is precisely a drawing's revision history.

**5. Identifiers.** Hub ID (prefixed `b.`, derived from the Account ID), Project ID, and — the detail worth protecting — **Item ID and Version ID are two distinct fields**, not one collapsed "drawing reference." The Version chain on an Item *is* the revision history; losing that distinction loses the ability to diff two revisions later. Issues carry both a GUID and a per-project sequential display number, same duality as Procore.

**6. APIs Downstream would realistically consume.** Construction.Issues/RFIs (read + webhook), Data Management Item/Version metadata (to resolve exactly which sheet and revision an RFI cites), Cost Management (where licensed), Account Admin for project/user scoping.

**7. Write operations possible.** Yes — creating/updating Issues, transitioning status, adding comments, and, where Cost Management is licensed, creating change orders.

**8. Limitations.** The Issues-vs-RFIs modeling split must be detected per customer, not assumed. API calls must be routed to the region (US/EMEA/etc.) matching where the account was created — a real, easy-to-miss configuration detail. Cost Management is a separately licensed module; a large share of ACC customers simply won't have it enabled, so ACC-as-commercial-source must be treated as optional and probed, never assumed present.

**9. What the Connector Interface should normalize.** Same capability-flag treatment as Procore — the ACC adapter can be Engineering-only or Engineering-plus-Commercial depending on licensing, discovered at connection time.

**10. Envelope check.** Add `region` (for correct, replay-safe routing). Split any single "drawing reference" field into explicit `item_id` and `version_id`. Add a `module_available` capability set (Issues/RFIs, Submittals, Cost Management may each be independently licensed) so the Reasoning Pipeline never assumes a data source exists that the customer never turned on.

---

## SAP (S/4HANA)

**1. Integration model.** OData services (V2 legacy, V4 preferred), exposed via SAP Gateway on-premise or SAP BTP/API Management in the cloud. Heavier integrations route through SAP Integration Suite (Cloud Integration) as middleware rather than calling OData directly. On S/4HANA Cloud, an admin must first configure a **Communication Arrangement** in Fiori for the external system — without it, every call returns 403 even with otherwise-valid credentials. This is a mandatory Basis/IT administrative step, not something Downstream can self-provision.

**2. Authentication model.** On-premise: Basic Auth is still common, or OAuth2 client_credentials configured through SICF/SOAUTH2 — and **every write requires a CSRF token**, fetched via a GET with an `X-CSRF-Token: fetch` header before the actual POST/PATCH/DELETE. On Cloud: OAuth2 client_credentials only, and the authorization server **must** be SAP BTP's XSUAA — you cannot point a generic third-party OAuth provider at it, which constrains how Downstream's credential vault has to be structured for SAP specifically.

**3. Event model.** SAP Event Mesh / Advanced Event Mesh for cloud-native pub/sub — and this is the pattern to internalize: **the event payload is deliberately minimal, key fields and changed fields only; the consumer is expected to call back to the OData API for the complete object.** On-premise systems frequently have no native event push at all — the fallback is polling with an OData `$filter` on a changed-since timestamp, or, on very old landscapes, IDoc/BAPI batch integration.

**4. Objects exposed.** Purchase Order (`API_PURCHASEORDER_PROCESS_SRV`), Material/Product Master, Vendor/Business Partner, Cost Center, and — where SAP Project System is in use — WBS Elements, the closest SAP analog to a construction cost code. Also genuinely useful: SAP's native Change Documents (CDHDR/CDPOS) — a built-in, field-level audit trail that is arguably a better source of "what changed and when" than reconstructing it yourself.

**5. Identifiers.** Purchase Order Number (a fixed-format numeric string), Vendor/Business Partner ID, Material Number, and two scoping dimensions with no equivalent anywhere in Procore or ACC: **Company Code and Plant**. WBS Element is the cost-code analog when Project System is active.

**6. APIs Downstream would realistically consume.** Purchase Order header + line items + status, Business Partner/Vendor Master, Cost Center/WBS reads, and the Change Documents API for native lifecycle history.

**7. Write operations possible.** Yes, the same OData service supports create/update/delete on POs, CSRF-protected — subject, as it should be, to the customer's own release-strategy workflow remaining the real gatekeeper of whether the write takes effect.

**8. Limitations.** Communication Arrangement setup is a genuine per-customer administrative bottleneck, not a self-service OAuth app registration. On-premise landscapes without event infrastructure degrade Downstream's real-time promise to polling latency — this should be stated to prospects honestly, not glossed over. Company Code/Plant/Purchasing Org must be explicitly configured per customer; there is no automatic discovery.

**9. What the Connector Interface should normalize.** SAP is unambiguously Commercial-only — no native RFI/drawing concept — so it's the cleanest single-family case on this list.

**10. Envelope check.** `cost_code` needs a format tag, because SAP's WBS-element structure is not the same shape as CSI MasterFormat, and the Graph Layer's key-matching logic needs to know which normalizer to apply. Add `company_code`/`plant`/`purchasing_org` as explicit fields — without them, the same PO number can collide across org units in a large landscape, a real data-integrity risk, not a theoretical one.

---

## Oracle ERP (Fusion Cloud)

**1. Integration model.** REST APIs under `fscmRestApi/resources/{version}` for real-time single-record reads/writes; FBDI for bulk import; BICC for bulk/incremental export; Business Events plus **Oracle Integration Cloud (OIC) as a mandatory middleware hop** for event-driven workflows. You cannot subscribe a third-party webhook endpoint directly to an Oracle business event — OIC sits in between by design.

**2. Authentication model.** OAuth 2.0 bearer tokens via Oracle IAM/IDCS; Basic Auth still seen in older integrations. Broadly comparable to Procore/ACC/SAP-cloud — no unusual departure.

**3. Event model.** Business Events fire on standard transactions — the Purchase Order event is enabled by default, a genuinely good sign for this use case — but only reach a third party via OIC, which calls an "enrichment service" to fetch the full object from Oracle's own REST API before forwarding it onward. This is the same thin-event-thick-lookup pattern as SAP, now confirmed across two of the largest ERP vendors on earth — treat it as a load-bearing assumption for the Connector Interface, not a guess.

**4. Objects exposed.** Purchase Order (Requisition → PO → Receipt → Invoice matching), Supplier, Project/Task (Oracle Projects — the closest analog to a construction project's cost-code structure), Business Unit, Bank Account/vendor financial master.

**5. Identifiers.** `PurchaseOrderId` (system surrogate key) plus `PONumber` (the human-facing business identifier) — the same display-vs-key duality seen everywhere else on this list. `ProjectId` + `TaskId` are the cost-code analog. **Business Unit** is Oracle's scoping dimension, structurally equivalent to SAP's Company Code but with no shared vocabulary — another reason a generic `org_scope` concept belongs in the envelope rather than a SAP-specific field name.

**6. APIs Downstream would realistically consume.** Purchase Orders resource (header + lines), Suppliers, Projects/Tasks, and Business Events via OIC for the PO-changed trigger.

**7. Write operations possible.** Yes, the Purchase Orders REST resource supports create/update, again subject to Oracle's own approval hierarchy actually governing whether the change is accepted.

**8. Limitations.** The OIC dependency is a real cost and a real vendor relationship most prospective customers may not already have — if they run Oracle ERP without an OIC subscription, the real-time event path simply doesn't exist and the connector must fall back to REST polling, same as un-instrumented on-premise SAP. FBDI/BICC are batch tools, useful only for the one-time historical calibration pass, never for steady-state detection. Oracle's construction-specific document platform, Aconex, is a separate acquisition and would need its own connector if a customer runs Oracle ERP alongside it — don't assume "Oracle" covers the engineering side too.

**9. What the Connector Interface should normalize.** Cleanly Commercial-only, same as SAP.

**10. Envelope check.** Add `business_unit` as an explicit scoping field. Add a field recording whether a given snapshot arrived via the OIC real-time path or the polling fallback — this is a genuine freshness/trust difference and should feed the confidence tier, not be silently treated as equally fresh regardless of source.

---

## ERPNext

**1. Integration model.** The Frappe framework auto-generates a full REST API for every DocType (`/api/resource/:doctype`) — including custom doctypes a specific customer has added. This is a materially different posture from the other four: there is no separate API-design step for customization, because the framework generates the surface directly from whatever schema exists.

**2. Authentication model.** Token-based auth (API Key + API Secret, sent as `Authorization: token api_key:api_secret`) is the primary, lightest-weight model on this entire list; OAuth2 (authorization_code, standard access/refresh tokens) is also available for user-delegated cases. No Communication Arrangement, no OIC subscription, no CSRF ceremony — genuinely the fastest of the five to provision a pilot against.

**3. Event model.** A native Webhook DocType, configurable per-DocType and per-event (`after_insert`, `on_update`, `on_submit`, `on_cancel`) directly in the admin UI — delivered as a plain HTTP POST. **This is the only one of the five with zero mandatory middleware hop for real-time push.** Whether the payload is thin or full depends on how the webhook is configured (it can be made to include the full document), which is itself worth noting as a difference from the other four's enforced minimalism.

**4. Objects exposed.** Purchase Order, Purchase Receipt, Supplier, Material Request, Project, Cost Center — plus whatever construction-specific custom doctypes a given implementation has added (a "Site RFI" or "Change Order" doctype that doesn't exist in stock ERPNext at all is common in practice, since ERPNext is frequently extended per-industry).

**5. Identifiers.** The `name` field is Frappe's universal primary key — and uniquely on this list, it is frequently **also** the human-meaningful identifier (e.g., `PO-00001`), collapsing the display-vs-key duality that every other system requires separate handling for.

**6. APIs Downstream would realistically consume.** `/api/resource/Purchase Order`, `/api/resource/Supplier`, `/api/resource/Project`, `/api/resource/Material Request`, plus customer-specific custom doctypes discovered at onboarding.

**7. Write operations possible.** Yes, full CRUD via the same REST surface, governed by Frappe's native role-permission system — no CSRF ceremony, no arrangement gate.

**8. Limitations.** Because ERPNext is open-source and commonly customized per deployment, there is **no guaranteed stable schema across customers** — onboarding must include a genuine schema-discovery step (introspecting the actual doctype and field list) rather than reusing one fixed mapping. Many deployments are self-hosted, meaning Downstream may need VPN/allowlist access to a customer's own infrastructure rather than a guaranteed public cloud endpoint — a deployment-topology variable none of the other four generally present.

**9. What the Connector Interface should normalize.** Commercial-only in stock form, but the schema-discovery requirement means this adapter needs a configuration-time field-mapping step the other four can mostly hardcode.

**10. Envelope check.** `cost_code` must map onto whatever Cost Center/Project-Task structure a specific deployment actually uses — inherently a per-customer configuration artifact here, not a fixed parser.

---

## What this means for the two envelopes, synthesized once

**`EngineeringEventEnvelope` needs four additions:**
- `display_number` — separate from `source_id`, because Procore's and ACC's human-facing numbers are editable, cosmetic fields, not primary keys.
- `item_id` and `version_id` as distinct fields — never collapse a document reference into one opaque string; ACC's whole revision-diffing capability depends on this split.
- `region` — for APS/ACC endpoint routing and safe replay.
- `acting_credential_scope` — what the fetching credential could actually see. This is the single highest-value addition: without it, every downstream confidence tier is quietly assuming full visibility that may not exist.

**`CommercialArtifactSnapshot` needs three additions:**
- An `org_scope` structure generalizing SAP's Company Code/Plant and Oracle's Business Unit — without it, the same PO number can collide across org units in any real enterprise landscape.
- `cost_code_format` — an explicit tag (CSI MasterFormat | SAP WBS | Oracle Project/Task | ERPNext Cost Center | Customer-defined) so the Graph Layer's key-matching applies the correct normalizer instead of assuming one universal shape. This is arguably the most consequential missing field of all ten: "cost code" is not one concept, it is five, and the whole Key Resolution stage silently depends on knowing which one it's looking at.
- `data_freshness_path` — real-time-event, polled, or one-time-bulk-import. A polled SAP snapshot and a webhook-pushed Procore snapshot are not equally trustworthy, and the confidence-tiering stage should know the difference rather than treat all data as uniformly fresh.

Both envelopes were directionally right and genuinely incomplete — not wrong in shape, but built for a tidier world than five real systems actually provide.

---

## The Mock Engineering System and Mock ERP

The governing rule for both mocks: **their job is to lie to the Connector adapters exactly as convincingly, and exactly as inconveniently, as the real systems will.** A mock that hands back clean, full payloads on every webhook is worse than no mock at all — it lets an adapter ship that will break the first day it meets a real system's thin-event contract. Fidelity to the *awkward* parts validated above is the entire point.

### Mock Engineering System (models Procore/ACC's shared shape)

- **Auth:** an OAuth2 token endpoint (`authorization_code` and `refresh_token` grants, `access_token`/`refresh_token`/`expires_in` in the real shape), so the adapter's token-refresh logic is genuinely exercised, not assumed.
- **Resources:** company/project-scoped RFI and Document endpoints. Every RFI carries both an opaque `id` and a separate, editable `display_number` — deliberately, so an adapter that conflates them fails against the mock exactly as it would against real Procore. Documents expose an `item_id` with a `version_id` chain, mirroring ACC's Data Management model.
- **Webhooks:** on an RFI status change, the mock POSTs a **thin** payload — resource type, resource id, project id, event type, timestamp, nothing else — forcing the adapter to perform the real GET-back for full detail. This one behavior is the most important thing the mock must get right, because it's the exact place a too-convenient mock produces a broken production adapter.
- **Rate limiting and pagination:** a configurable per-`client_id` request budget returning `429` + `Retry-After` once exceeded, plus `per_page`/`page` params and an `X-Total` header — so backoff and pagination logic are real, not theoretical.
- **Permission scoping:** a seeded integration user whose visible resource types can be deliberately restricted, so the onboarding and health-check flow can be tested against both fully- and partially-scoped credentials — the direct test bed for the new `acting_credential_scope` field.

### Mock ERP (models SAP/Oracle's shared shape)

- **Auth:** OAuth2 `client_credentials` only — no user delegation — matching the server-to-server posture of both real ERPs.
- **CSRF ceremony:** a GET on the Purchase Order resource with `X-CSRF-Token: fetch` returns a token; any POST/PATCH/DELETE without it is rejected with `403`. Cheap to build now, and exactly the kind of enterprise-reality detail that's expensive to discover for the first time against a real customer's sandbox.
- **Purchase Order resource:** supports a `$filter` on a changed-since timestamp (to exercise the polling fallback honestly) and carries explicit `company_code`/`plant` fields — seeded with **overlapping PO number ranges across two different company codes**, deliberately, so an adapter that treats PO number as globally unique fails against the mock before it ever gets the chance to fail against a real customer.
- **Thin business-event webhook:** on a PO status change, POSTs a minimal `{event_type, business_object, key: {po_number, company_code}, changed_fields, occurred_at}` payload — no full object — forcing the same enrichment-callback discipline as the real SAP Event Mesh / Oracle OIC pattern.
- **Write-back with idempotency:** a PATCH endpoint for holding a PO or attaching a note, requiring the CSRF token, and honoring an idempotency key — replaying the same request returns the original result rather than double-applying it, exercising the Synchronization Service's actual guarantee rather than assuming it.

### Why this makes "swap the mock for real Procore, zero Reasoning Engine changes" true — and what it actually requires

That guarantee is not a property of the mock. It is a property of **where the canonical envelope gets produced.** If envelope construction lives entirely inside each Connector adapter — and nowhere upstream of it ever sees a raw Procore or SAP payload — then replacing Mock Procore with real Procore is purely a matter of changing a base URL, a set of credentials, and possibly a field-name mapping *inside that one adapter*. The Reasoning Engine only ever sees `EngineeringEventEnvelope` and `CommercialArtifactSnapshot`, which don't change.

The actual engineering discipline this requires, stated plainly: write **contract tests** against the envelope-producing behavior of each adapter — "given this raw webhook payload shape, the adapter must produce an envelope with these fields, including a correct GET-back for full detail" — and run the identical contract test suite against both the mock and, eventually, a real sandbox tenant. If both pass the same suite, the swap is safe. If the mock was too convenient (full payloads on webhooks, no rate limiting, no permission scoping, one global PO-number space), the contract tests will pass against the mock and fail the moment they run against reality — which is precisely the failure this whole validation exercise exists to prevent you from discovering in front of a customer instead of in front of yourselves.

---

## Recommendations

1. **Rebuild both envelopes with the seven additions above before writing a line of adapter code.** They cost nothing structurally and prevent the exact class of bug enterprise integrations are famous for.
2. **Build the Mock ERP's thin-event-plus-CSRF-plus-org-scoping behavior first**, not the Mock Engineering System — it's the more demanding contract, and an adapter that survives it will handle ERPNext's much gentler contract for free.
3. **Treat Procore and ACC's "capability flag, not fixed type" reality as a first-class configuration concept**, not an edge case — for a meaningful share of real customers, one connection will need to serve both envelope families at once.
4. **Write the contract tests before the real-sandbox integration, and run them against the mock as a gate.** The mock's value is entirely a function of how honestly it fails you now instead of later.

## Caveats

- API details (endpoint paths, rate-limit thresholds, exact grant types) are current as of this review but all five platforms version and evolve their APIs continuously — treat specific numbers (3,600 requests/hour, `fscmRestApi/resources/11.13.18.05`, etc.) as illustrative of the *pattern*, and re-verify exact current values against each vendor's live developer documentation before finalizing adapter code.
- Several sources describing real-world integration friction (permission-scoping surprises, webhook payload thinness, schema drift across ERPNext deployments) are third-party integration vendors and community posts rather than the platform vendors' own documentation — directionally reliable, but worth confirming against a real sandbox tenant for any customer-specific edge case before it becomes a production assumption.
- ACC's Issues-vs-RFIs API modeling and Oracle's Aconex-vs-Fusion-ERP separation are both areas of active product evolution at their respective vendors; confirm current module boundaries per customer at onboarding rather than assuming this document's snapshot remains accurate indefinitely.