# connector-interface

**Status:** Scaffold only — no schemas/models implemented yet.

The shared adapter contract every Connector implements: fetchEngineeringEvents, fetchArtifactSnapshot, pushAction, healthCheck.

This service is part of the Downstream monorepo. The architecture is frozen — see
`/docs` for the source-of-truth design documents, and
`/docs/07_Downstream_Implementation_Blueprint.md` in particular for this
service's exact folder contract, database ownership, and API/event surface.

No business logic, APIs, or database tables have been implemented yet. This
folder is scaffold only, created as part of repository initialization.
