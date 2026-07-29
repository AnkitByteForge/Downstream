# connector-sap

**Status:** Scaffold only — not yet implemented. Wired into Milestone 1 per the Implementation Blueprint.

SAP Connector Adapter — fetchArtifactSnapshot and pushAction (CSRF-token ceremony, OData PATCH) against SAP S/4HANA. Wired into Milestone 1, run against infra/mocks/mock-erp.

This service is part of the Downstream monorepo. The architecture is frozen — see
`/docs` for the source-of-truth design documents, and
`/docs/07_Downstream_Implementation_Blueprint.md` in particular for this
service's exact folder contract, database ownership, and API/event surface.

No business logic, APIs, or database tables have been implemented yet. This
folder is scaffold only, created as part of repository initialization.
