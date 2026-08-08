I did not modify any files, generate code, or implement RES-4. I performed a read-only takeover review of the authoritative docs, ADRs, RES implementation, migrations, seed data, frontend, tests, and relevant git history.

HANDOFF REVIEW

A. My understanding of what Downstream is

Downstream is not an engineering system and not an ERP. It is the synchronization/intelligence layer between engineering reality and commercial reality.

Its core thesis is:“When an approved design change occurs, automatically identify downstream procurement impact and generate an evidence-backed procurement action plan.”Supported by:

C:\Users\ankit\Downstream\docs\01_Downstream_The_Company.md, lines 4–5

C:\Users\ankit\Downstream\docs\02_Downstream_Product_Design.md, lines 4–7

C:\Users\ankit\Downstream\docs\reference\Downstream_Intelligence_Specification.md, lines 8–19

Downstream watches approved engineering changes, resolves them through graph/key relationships, determines affected commercial commitments, computes confidence/severity, drafts actions, and requires human approval before any external commercial write-back.

Important constraints:

Downstream does not make engineering decisions.

Downstream does not replace engineering or commercial systems of record.

Downstream does not autonomously execute financial or contractual transactions.

Downstream writes only commercial-side approved actions, never edits engineering records.

Supported by:

C:\Users\ankit\Downstream\docs\reference\Downstream_Intelligence_Specification.md, lines 14–19

C:\Users\ankit\Downstream\docs\reference\Downstream_Intelligence_Specification.md, lines 237–259

C:\Users\ankit\Downstream\docs\03_Downstream_Systems_Architecture.md, lines 10–14

The primary object in Downstream is the Commercial Event / Change consequence, not an RFI or PO alone. Commercial State is computed from an immutable ledger, not stored as mutable CRUD state.

Supported by:

C:\Users\ankit\Downstream\docs\01_Downstream_The_Company.md, lines 35–40

C:\Users\ankit\Downstream\docs\03_Downstream_Systems_Architecture.md, lines 6–12

C:\Users\ankit\Downstream\docs\07_Downstream_Implementation_Blueprint.md, lines 431–455B. Role of the Reference Engineering System in the larger architecture

The Reference Engineering System is a reference external engineering platform that Downstream will later connect to through a connector adapter. It is Procore/ACC-realistic, but vendor-neutral.

It must emit raw, vendor-shaped engineering-system behavior, not Downstream’s canonical envelopes or reasoning outputs.

Supported by:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\README.md, lines 3–8

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\README.md, lines 3–10

C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 241–253

Critical boundary:

RES must not import or construct EngineeringEventEnvelope.

RES must not perform Downstream reasoning.

RES must not contain Kafka/Neo4j orchestration, Commercial Event state machines, approval workflows, synchronization services, settlement logic, or canonical envelope construction.

RES should expose realistic OAuth2, permission scope, pagination, rate limiting, thin webhooks, and REST resource APIs so a future connector can behave like it would against real Procore.

Supported by:

C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 245–253

C:\Users\ankit\Downstream\docs\04_Downstream_Connector_Layer_Validation.md, lines 160–177

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\README.md, lines 12–23C. Exact current implementation state of RES-1, RES-2, and RES-3

Current RES milestone is RES-3.

Supported by:

C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, line 3

C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 449–451

Git history shows RES commits:

cb53b04 — RES-1

03e1d35 — RES-2

467077e — RES-3

Note: git history also shows a later doc/PDF commit after RES-3, so IMPLEMENTATION_STATUS.md is not literally the latest git commit description anymore, but the implementation milestone remains RES-3.

RES-1

RES-1 implemented the initial Clean Architecture backend, core engineering domain, auth, Meridian Tower Scenario A seed data, and initial frontend.

Implemented entities include:

Project

Discipline

Location

SpecDivision

SpecSection

Drawing

DrawingVersion

RevisionCloud

RFI

BallInCourt

User

IntegrationUser

OAuthClient

OAuthToken

Supported by:

C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 255–267

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\domain\entities\project.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\domain\entities\drawing.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\domain\entities\rfi.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\domain\value_objects\ball_in_court.py

State machines:

RFI: DRAFT → OPEN → RESPONDED → CLOSED

Direct OPEN → CLOSED is allowed with response text because RFI-214 closes in one step in the reference trace.

DrawingVersion: DRAFT → ISSUED → REVISED → SUPERSEDED

Supported by:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\domain\state_machines\rfi_transitions.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\domain\state_machines\drawing_version_transitions.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\tests\unit\domain\test_rfi_transitions.py

Auth:

Human login uses an httpOnly JWT cookie named res_session.

Integration auth uses OAuth2 authorization-code and refresh-token grants.

Both resolve into ActingContext.

Supported by:

C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 275–282

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\api\deps.py, lines 321–380

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\api\v1\auth.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\api\v1\oauth.py

Migrations:

0001_core_project_structure.py

0002_users_and_integration_auth.py

0003_drawings.py

0004_rfis.py

Supported by:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\migrations\versions\0001_core_project_structure.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\migrations\versions\0002_users_and_integration_auth.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\migrations\versions\0003_drawings.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\migrations\versions\0004_rfis.py

Seed data:

Meridian Tower project

Mechanical discipline

Site/building/Level 4/Grid B-4 location tree

Spec 23 31 13

Drawing M-2.1, Rev B superseded by Rev C

RFI-214 closed at 2026-07-28T09:14:03Z

Five human users

OAuth2 clients

Supported by:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\seed\meridian_tower.py, lines 64–70, 103–118, 218–294

C:\Users\ankit\Downstream\docs\05_Downstream_Reference_Execution_Trace.md, lines 8–83

Frontend RES-1 pages:

/login

/dashboard

/projects

/projects/[projectId]/rfis

/projects/[projectId]/rfis/[rfiId]

Supported by:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\frontend\README.md, lines 13–25

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\frontend\src\app\login\page.tsx

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\frontend\src\app\projects[projectId]\rfis\page.tsx

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\frontend\src\app\projects[projectId]\rfis[rfiId]\page.tsx

RES-2

RES-2 added:

Webhook subscriptions

Webhook delivery log

Thin webhook dispatch for RFI close

HMAC signing

Activity Feed backend and frontend

API pagination

Per-client rate limiting

Drawing register/detail/revision timeline frontend pages

Supported by:

C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 369–445

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\domain\entities\webhook.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\application\webhook_payloads.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\infrastructure\webhooks\dispatcher.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\infrastructure\webhooks\signing.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\infrastructure\rate_limit\store.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\api\pagination.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\frontend\src\app\projects[projectId]\activity\page.tsx

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\frontend\src\app\projects[projectId]\drawings\page.tsx

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\frontend\src\app\projects[projectId]\drawings[drawingId]\page.tsx

Migrations:

0005_webhooks.py

0006_rate_limit_state.py

Supported by:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\migrations\versions\0005_webhooks.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\migrations\versions\0006_rate_limit_state.py

Webhook shape:

Exactly five fields:

resource_name

resource_id

project_id

event_type

timestamp

Supported by:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\application\webhook_payloads.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\tests\contract\test_webhook_thin_payload.py

RES-3

RES-3 added:

Submittals

SubmittalRevisions

Configurable SubmittalReviewStatus vocabulary

Procurement gate via gates_procurement

SubmittalPackage entity

Vendor entity

Minimal lifecycle-free Commitment entity/table/repository

Submittal requirements / spec-driven register

Scenario B engineering-side seed data: SUB-118

Submittal webhook dispatch

Submittal frontend register/detail pages

Supported by:

C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 449–532

C:\Users\ankit\Downstream\docs\adr\ADR-003.md

C:\Users\ankit\Downstream\docs\adr\ADR-004.md

C:\Users\ankit\Downstream\docs\adr\ADR-005.md

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\domain\entities\submittal.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\domain\entities\vendor.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\domain\state_machines\submittal_transitions.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\application\use_cases\submittal_use_cases.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\frontend\src\app\projects[projectId]\submittals\page.tsx

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\frontend\src\app\projects[projectId]\submittals[submittalId]\page.tsx

Migrations:

0007_vendors_and_commitments.py

0008_submittal_configuration.py

0009_submittals.py

0010_submittal_requirements.py

Supported by:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\migrations\versions\0007_vendors_and_commitments.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\migrations\versions\0008_submittal_configuration.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\migrations\versions\0009_submittals.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\migrations\versions\0010_submittal_requirements.py

Scenario B seed:

Adds Electrical discipline.

Adds Level 1 / electrical room / roof locations.

Adds Spec Sections 23 74 13 and 26 24 13.

Adds vendors:

Coastal Aire Equipment

Voltrex Switchgear Inc.

Ferro Electrical Supply

Adds submittal SUB-118 with Rev 0 and Rev 1.

Rev 1 reaches NO_EXCEPTIONS_TAKEN.

Supported by:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\seed\meridian_tower.py, lines 103–130, 150–164, 296–324, 327–393

C:\Users\ankit\Downstream\docs\reference\Canonical_Demo_Dataset.md, lines 94–118

Tests:

Architecture tests enforce no forbidden imports in domain/ and application/.

Unit tests cover RFI, DrawingVersion, Submittal state machines and use cases.

Integration tests cover rate limiting and submittal persistence.

Contract tests cover thin webhook payloads, 429 + Retry-After, pagination, submittal procurement gate behavior.

Supported by:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\tests\architecture\test_layer_boundaries.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\tests\unit\domain\test_rfi_transitions.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\tests\unit\domain\test_submittal_transitions.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\tests\contract\test_submittal_webhook_and_gate.py

C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 534–540

I did not run the test suite because the user explicitly requested no modifications and the contract/integration tests use a real database and create/delete rows.D. Architectural patterns established by RES-1/2/3 that future work must reuse

Clean Architecture layering

The backend uses:domain/application/infrastructure/api/Rules:

domain/ is pure Python dataclasses, value objects, repository ports, exceptions, state machines.

application/ contains use cases and ports; depends only on domain.

infrastructure/ contains SQLAlchemy, auth adapters, HMAC dispatch, config, rate-limit store.

api/ is the FastAPI composition root and routing layer.

Supported by:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\README.md, lines 12–23

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\tests\architecture\test_layer_boundaries.py

Pure state machines

State transitions are pure functions returning replaced dataclasses, not mutating the object in place.

Supported by:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\domain\state_machines\rfi_transitions.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\domain\state_machines\drawing_version_transitions.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\domain\state_machines\submittal_transitions.py

Repository ports + SQLAlchemy adapters

Every persistent domain concept has an abstract repository port in domain/repositories/ and a SQLAlchemy implementation in infrastructure/persistence/repositories/.

Supported by:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\domain\repositories*.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\infrastructure\persistence\repositories*.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\api\deps.py, lines 124–158

API routes are thin

Routes:

Resolve auth/context.

Enforce resource scope.

Call one use case.

Translate domain/application errors into HTTP status codes.

Apply pagination at API layer, not application layer.

Supported by:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\api\v1\rfis.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\api\v1\submittals.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\api\pagination.py

HTTP/protocol concerns stay out of domain

Rate limiting is deliberately not a domain entity. It lives in:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\infrastructure\rate_limit\store.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\api\deps.py, lines 383–420

Supported by:

C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 369–373

Webhook subscription/delivery are domain entities

Unlike rate limiting, webhook subscriptions and deliveries are treated as real RES business facts because this external system owns its webhook setup and delivery log.

Supported by:

C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 369–379

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\domain\entities\webhook.py

Thin webhook payload is sacred

Future work must not enrich webhook payloads with status, response text, drawing refs, etc. The whole point is to force the connector to perform GET-back enrichment.

Supported by:

C:\Users\ankit\Downstream\docs\04_Downstream_Connector_Layer_Validation.md, lines 160–177

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\application\webhook_payloads.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\tests\contract\test_webhook_thin_payload.py

Frontend consumes backend APIs only

The frontend must not fabricate data or bypass the backend.

Supported by:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\frontend\README.md, lines 9–11

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\frontend\src\lib\api-client\client.ts

No Downstream internal package dependency from RES

RES intentionally does not depend on packages/*.

Supported by:

C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 245–253E. Canonical Meridian Tower scenarios and why they exist

There are two canonical scenarios in one project: Meridian Tower.

Supported by:

C:\Users\ankit\Downstream\docs\reference\Canonical_Demo_Dataset.md, lines 7–18

Scenario A — “The Duct Reroute”

This is the original frozen trace from 05_Downstream_Reference_Execution_Trace.md.

Trigger:

RFI-214 closes.

It references Spec 23 31 13.

It references Drawing M-2.1 Rev C.

It concerns a duct reroute at Level 4 / Grid B-4.

Why it exists:

It is the exact end-to-end Downstream reference trace.

It proves thin webhook → GET-back → canonical envelope construction will be possible later.

It provides the original graph/reasoning/commercial-event story for PO-4471, PO-4488, PO-4512, and schedule activity 3410.

Supported by:

C:\Users\ankit\Downstream\docs\05_Downstream_Reference_Execution_Trace.md, lines 1–83, 123–160, 167–217

C:\Users\ankit\Downstream\docs\reference\Canonical_Demo_Dataset.md, lines 15–17, 84–90, 194–203

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\seed\meridian_tower.py, lines 218–294

Scenario B — “The HVAC Upsize”

This is the newer demo/intelligence scenario.

Trigger in current RES:

SUB-118 Rev 1 reaches NO_EXCEPTIONS_TAKEN.

It is a rooftop unit submittal.

Equipment changes from CA-RTU-40 / 180 A MCA to CA-RTU-55 / 240 A MCA.

The commercial impact is supposed to land later on electrical switchgear / feeder / conduit artifacts in the Reference Commercial System.

Why it exists:

It is the recommended live demo because “the AC got bigger, so the electrical gear already bought is now wrong” is immediately understandable.

It exercises cross-discipline reasoning: mechanical equipment change → electrical switchgear procurement exposure.

It demonstrates that Downstream is not hardcoded to RFI-214 or one trade.

Supported by:

C:\Users\ankit\Downstream\docs\reference\Downstream Demo Strategy.md, lines 3–6, 109–115

C:\Users\ankit\Downstream\docs\reference\Downstream_Intelligence_Specification.md, especially Section 13

C:\Users\ankit\Downstream\docs\reference\Canonical_Demo_Dataset.md, lines 94–118, 205–216

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\seed\meridian_tower.py, lines 296–393

Important current limitation:

Scenario B is only engineering-side producible today.

The commercial-side artifacts po_5201, po_5202, and req_5203 remain specification-only until the Reference Commercial System exists.

Supported by:

C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 530–531

C:\Users\ankit\Downstream\docs\reference\Canonical_Demo_Dataset.md, lines 153–164F. Boundary between Reference Engineering and Reference Commercial responsibilities

Reference Engineering System owns

Engineering-side artifacts and workflows:

Drawings / DrawingVersions

SpecSections

RFIs

Ball-in-court routing

Submittals / SubmittalRevisions

Submittal review dispositions

Submittal procurement-gate signal

Design Changes / Field Issues / ClashItems / Transmittals later, if implemented as RES-4+

Thin webhooks and raw engineering resource APIs

Supported by:

C:\Users\ankit\Downstream\docs\reference\The Reference Engineering System.md, lines 3–6

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\README.md, lines 3–8

Reference Commercial System owns

Commercial-side artifacts and workflows:

Purchase Requisitions

Purchase Orders

PO lines

Schedule lines / delivery

Vendor commercial state

Goods receipts

Invoices

CostCode/WBS

Procurement schedule items

Commercial ChangeOrders

OrgScope

Fabrication/expediting lifecycle

Supported by:

C:\Users\ankit\Downstream\docs\reference\The Reference Commercial System.md, lines 3–7, 161–177

Commitment nuance

RES includes a minimal Commitment because real Procore-like systems can expose commitment-like records, but RES intentionally keeps it lifecycle-free. The rich lifecycle-bearing PO/commitment model belongs to Reference Commercial.

Supported by:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\domain\entities\vendor.py, lines 13–29

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\migrations\versions\0007_vendors_and_commitments.py

C:\Users\ankit\Downstream\docs\04_Downstream_Connector_Layer_Validation.md, lines 16–24

C:\Users\ankit\Downstream\docs\reference\The Reference Commercial System.md, lines 3–7

Current actual code state: RES has a Commitment entity/table/repository, but I did not find a public Commitment API, seeded Commitment rows, or tests exercising Commitment behavior beyond schema/repository existence.

Supported by:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\domain\entities\vendor.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\domain\repositories\vendor_repository.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\infrastructure\persistence\repositories\sqlalchemy_vendor_repository.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\api\v1\vendors.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\seed\meridian_tower.pyG. Existing technical debt / known limitations explicitly documented

Documented limitations include:

In-memory pagination

Correct for current seed scale, not production-scale.

Source: C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 438–442

Webhook retry/backoff/dead-letter queue absent

One retry only; no dead-letter queue.

Source: C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 438–445

Source: C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\infrastructure\webhooks\dispatcher.py, lines 15–20

No frontend pagination UI

Backend pagination exists and is tested; frontend does not expose controls.

Source: C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 421–442

No Playwright/browser e2e suite

Deferred to RES-5.

Source: C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 438–443

DrawingVersion webhook coverage not added

Source: C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 525–528

SubmittalPackage is unused in seed data

Entity exists, no seeded package row.

Source: C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 527–529

Source: C:\Users\ankit\Downstream\docs\adr\ADR-005.md

SubmittalReviewStatus has no admin/config API

Config-driven storage exists; runtime UI/API customization does not.

Source: C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 528–530

No Design Change, Field Issue, ClashItem, Transmittal, ScheduleActivity, or ModelObject

These remain RES-4 / RES-5 scope.

Source: C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 530–531

Scenario B only half-producible

RES has submittal trigger side only; commercial artifacts await Reference Commercial System.

Source: C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 530–531

Docker compose pre-existing path issue

Still out of scope.

Source: C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 532

Open item: repo_structure.txt unreconciled

Source: C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 235–237H. What the repository currently says RES-4 is supposed to accomplish

RES-4 is not implemented.

The repository currently says RES-4 scope includes:

DesignChange family:

ASI

Bulletin

CCD

ChangeOrder

ChangeEvent / PCO / COR chain

FieldIssue

ClashItem

Transmittal

Some deferred frontend pages may also land across RES-2/RES-3/RES-4.

Supported by:

C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 330–332

C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 525–531

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\RES-1_USER_GUIDE.md, lines 186–193

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\frontend\README.md, lines 23–25

The reference docs also indicate the next high-value additions should be Design Changes and cross-entity linking:

Design changes follow an authority ladder:

RFI → ASI → PR/PCO → CCD → Change Order

RES should wire the design-change family with links from triggering RFI/submittal and affected drawing revision.

Field Issues are recommended after core Design Change / Submittal gate flow.

Supported by:

C:\Users\ankit\Downstream\docs\reference\The Enterprise Fidelity Review.md, lines 16–18, 143–152

C:\Users\ankit\Downstream\docs\reference\The Reference Engineering System.md, lines 155–161

C:\Users\ankit\Downstream\docs\reference\Canonical_Demo_Dataset.md, lines 121–123

Canonical Dataset gives a non-binding RES-4 continuity sketch:

Stage B2 may add ASI-07.

It would cite SUB-118 Rev 1 load increase.

It may supersede an electrical drawing DWG-E-1.1 Rev 0 → Rev 1.

It must not be seeded before RES-4.

Supported by:

C:\Users\ankit\Downstream\docs\reference\Canonical_Demo_Dataset.md, lines 121–123

Important distinction: C:\Users\ankit\Downstream\docs\07_Downstream_Implementation_Blueprint.md also has a Downstream Milestone 4 called “Realtime and human approval,” but that is not RES-4. It refers to Downstream’s own app/services milestone, not the Reference Engineering System milestone.

Supported by:

C:\Users\ankit\Downstream\docs\07_Downstream_Implementation_Blueprint.md, lines 599–600 from search resultsI. Contradictions or discrepancies found

Canonical_Demo_Dataset.md says DrawingVersion webhook was RES-3 scope, but implementation/status says it was not built

Canonical_Demo_Dataset.md says:

Drawing M-2.1 Rev C issued thin webhook is “extension confirmed in scope by RES-3 plan §2 item 6, not yet built.”

Source:

C:\Users\ankit\Downstream\docs\reference\Canonical_Demo_Dataset.md, lines 220–228

But IMPLEMENTATION_STATUS.md says DrawingVersion webhook coverage was explicitly not added because the approved RES-3 Implementation Contract only named Submittal changes.

Source:

C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 525–528

Actual code confirms no DrawingVersion webhook dispatch path comparable to RFI/Submittal.

Supported by absence in:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\application\use_cases\drawing_use_cases.py

Presence only in:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\application\use_cases\rfi_use_cases.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\application\use_cases\submittal_use_cases.py

Conclusion: documentation conflict exists; actual implementation matches IMPLEMENTATION_STATUS.md, not the older Canonical Dataset wording.

Canonical Dataset includes both MCA and FLA for SUB-118, but actual schema/code stores only one capacity value/unit

Canonical Dataset specifies:

Rev 0: MCA 180 A, FLA 150 A

Rev 1: MCA 240 A, FLA 200 A

Source:

C:\Users\ankit\Downstream\docs\reference\Canonical_Demo_Dataset.md, lines 102–109

Actual code stores only:

capacity_value

capacity_unit

Source:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\domain\entities\submittal.py, lines 74–79

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\migrations\versions\0009_submittals.py, lines 57–61

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\seed\meridian_tower.py, lines 341–353 and 368–380

Conclusion: actual RES-3 implementation captures MCA as generic capacity but does not model/store FLA separately. This is a real data-fidelity discrepancy relative to the canonical table.

Activity Feed API lacks explicit auth/scope dependency

Most /rest/v1.0 endpoints call get_acting_context and enforce ctx.can_see(...) / ctx.require_scope(...).

Examples:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\api\v1\rfis.py, lines 46–59 and 62–73

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\api\v1\submittals.py, lines 79–93 and 96–108

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\api\v1\documents.py, lines 40–67

But Activity Feed endpoint does not depend on get_acting_context.

Source:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\api\v1\activity.py, lines 12–15

It is under /rest/v1.0, so rate limiting dependency is attached at router level, but enforce_rate_limit returns immediately if there is no bearer token.

Source:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\api\v1\router.py, lines 26–39

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\api\deps.py, lines 392–404

Conclusion: unauthenticated access to /rest/v1.0/projects/{project_id}/activity appears possible in actual code. This conflicts with the general auth pattern and with the enterprise-security posture in the docs.

Path project_id is not compared against ActingContext.project_id

Routes use project_id from the URL and ActingContext for scope/resource visibility, but I did not find checks that ctx.project_id == project_id.

Examples:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\api\v1\rfis.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\api\v1\submittals.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\api\deps.py, lines 321–380

The broader Downstream architecture says tenant/project partitioning is a hard security boundary.

Source:

C:\Users\ankit\Downstream\docs\03_Downstream_Systems_Architecture.md, lines 212–214

Conclusion: perhaps acceptable for a single-seeded-project reference system so far, but actual code does not enforce project isolation at route level.

RES has Commitment schema/repository but no evident seeded commitments or public Commitment API

The RES-3 task/status says Vendors and minimal Commitments were in scope.

Source:

C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 449–451

Actual code includes:

Commitment dataclass

Commitment repository port

Commitment SQLAlchemy model/repository

Migration table

Sources:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\domain\entities\vendor.py, lines 13–29

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\domain\repositories\vendor_repository.py, lines 19–24

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\infrastructure\persistence\repositories\sqlalchemy_vendor_repository.py, lines 50–69

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\migrations\versions\0007_vendors_and_commitments.py

But I found:

Vendor list API only, no Commitment API.

Seed creates Scenario B vendors but does not instantiate Commitment rows.

No direct contract/integration test for Commitments.

Sources:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\api\v1\vendors.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\seed\meridian_tower.py, lines 296–299

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\tests

Conclusion: Commitment is structurally present but not meaningfully surfaced or seeded.J. Files/subsystems likely involved in RES-4 — no implementation proposal yet

Based on current architecture and documented RES-4 scope, likely involved areas are:

Domain

Likely new/extended entities and state machines under:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\domain\entities

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\domain\state_machines

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\domain\repositories

Potential concepts from docs:

DesignChange

ASI

Bulletin

CCD

ChangeOrder

ChangeEvent / PCO / COR, depending final RES-4 contract wording

FieldIssue

ClashItem

Transmittal

Cross-entity references/relationships

Supported by:

C:\Users\ankit\Downstream\IMPLEMENTATION_STATUS.md, lines 330–332, 525–531

C:\Users\ankit\Downstream\docs\reference\The Reference Engineering System.md, lines 3–6, 155–161

C:\Users\ankit\Downstream\docs\reference\The Enterprise Fidelity Review.md, lines 143–152

Application

Likely new use cases under:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\application\use_cases

Likely reuse:

WebhookDispatcherPort

build_thin_payload

repository ports

clock port

same “transition causes thin webhook + WebhookDelivery record” pattern used by RFI and Submittal

Supported by:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\application\use_cases\rfi_use_cases.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\application\use_cases\submittal_use_cases.py

Infrastructure / persistence

Likely new ORM models and SQLAlchemy repositories under:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\infrastructure\persistence\orm_models

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\infrastructure\persistence\repositories

Likely new Alembic migrations after:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\migrations\versions\0010_submittal_requirements.py

API

Likely new REST routes and schemas under:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\api\v1

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\api\schemas

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\api\deps.py

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\api\v1\router.py

Must preserve:

/rest/v1.0 resource shape

pagination where list endpoints exist

ActingContext scope enforcement

rate limiting for OAuth2 integration traffic

thin webhook pattern for state changes

Seed data

Likely file:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\backend\src\seed\meridian_tower.py

Canonical future hook:

ASI-07

possible DWG-E-1.1

link to SUB-118 Rev 1

Supported by:

C:\Users\ankit\Downstream\docs\reference\Canonical_Demo_Dataset.md, lines 121–123

Frontend

Likely files/areas:

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\frontend\src\lib\api-client\types.ts

C:\Users\ankit\Downstream\reference-systems\reference-engineering-system\frontend\src\lib\api-client\client.ts