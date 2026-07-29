# synchronization-service

**Status:** Scaffold only — no business logic implemented yet.

Synchronization Service — dispatches approved Actions outward through the Connector Layer (drafted communication or ERP write-back), idempotently, with a confirmation loop.

This service is part of the Downstream monorepo. The architecture is frozen — see
`/docs` for the source-of-truth design documents, and
`/docs/07_Downstream_Implementation_Blueprint.md` in particular for this
service's exact folder contract, database ownership, and API/event surface.

No business logic, APIs, or database tables have been implemented yet. This
folder is scaffold only, created as part of repository initialization.
