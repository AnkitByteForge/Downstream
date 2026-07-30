# Downstream

> When an approved engineering design change occurs, automatically compute its
> downstream commercial impact and present evidence-backed procurement actions
> before procurement mistakes happen.

Downstream sits between engineering systems of record (Procore, Autodesk
Construction Cloud) and commercial systems of record (SAP, Oracle ERP, ERPNext)
as the continuous synchronization layer between engineering reality and
commercial reality.

## Status

This repository is at the **repository initialization** stage: the monorepo
structure, service boundaries, shared packages, and Docker Compose topology
exist exactly as defined in the Implementation Blueprint. **No business logic,
APIs, or database tables have been implemented yet.** Every service is a
runnable-shell placeholder.

## Source of truth

The architecture is frozen. Every decision in this repository traces back to
the documents in [`/docs`](./docs), read in this order:

1. [`01_Downstream_The_Company.md`](./docs/01_Downstream_The_Company.md)
2. [`02_Downstream_Product_Design.md`](./docs/02_Downstream_Product_Design.md)
3. [`03_Downstream_Systems_Architecture.md`](./docs/03_Downstream_Systems_Architecture.md)
4. [`04_Downstream_Connector_Layer_Validation.md`](./docs/04_Downstream_Connector_Layer_Validation.md)
5. [`05_Downstream_Reference_Execution_Trace.md`](./docs/05_Downstream_Reference_Execution_Trace.md)
6. [`06_Downstream_Implementation_Backlog.md`](./docs/06_Downstream_Implementation_Backlog.md)
7. [`07_Downstream_Implementation_Blueprint.md`](./docs/07_Downstream_Implementation_Blueprint.md)

Do not invent features, services, APIs, or event names. Do not change service
boundaries. Implement only the milestone requested.

## Repository structure

```
downstream/
├── apps/                  # every independently-runnable service
│   ├── connector-procore/       # Milestone 1
│   ├── connector-sap/           # Milestone 1
│   ├── connector-email/         # Milestone 1
│   ├── connector-acc/           # stub — deferred
│   ├── connector-oracle/        # stub — deferred
│   ├── connector-erpnext/       # stub — deferred
│   ├── ingestion-service/
│   ├── key-resolution-service/
│   ├── reasoning-pipeline/
│   ├── commercial-event-service/
│   ├── ledger-service/
│   ├── realtime-gateway/
│   ├── notification-service/
│   ├── approval-service/
│   ├── synchronization-service/
│   └── web/
├── packages/               # shared, version-locked contracts
│   ├── envelope-schemas/
│   ├── connector-interface/
│   ├── domain-models/
│   ├── event-contracts/
│   └── shared-config/
├── infra/
│   ├── docker-compose.yml
│   ├── migrations/
│   └── mocks/
│       └── Reference Commercial System/   # mock SAP/Oracle — not yet implemented
├── reference-systems/
│   └── reference-engineering-system/      # backend (FastAPI) + frontend (Next.js) —
│                                           # see its own README; not a Downstream service,
│                                           # it's the external system Downstream connects into
└── docs/                    # the frozen design documents
```

## Running

```
docker compose -f infra/docker-compose.yml --project-directory . up
```

`--project-directory .` is required: Compose resolves every service's build
context relative to the project directory, not the compose file's own
location, and this file lives in `infra/` while every build path is written
relative to the repo root.

Deferred connectors (`connector-acc`, `connector-oracle`, `connector-erpnext`)
are declared under the `deferred` Compose profile and are not started by
default.

## Milestones

Development proceeds milestone by milestone, per
[`07_Downstream_Implementation_Blueprint.md`](./docs/07_Downstream_Implementation_Blueprint.md#9-development-roadmap-with-milestones).
Each milestone's "done" criterion is that the
[Reference Execution Trace](./docs/05_Downstream_Reference_Execution_Trace.md)
runs further through the system than it did at the end of the previous one.
Never implement a future milestone unless explicitly requested.
