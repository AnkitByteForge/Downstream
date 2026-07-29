# notification-service

**Status:** Scaffold only — no business logic implemented yet.

Notification & Delivery Service — routes severity-computed events to immediate push (Sev 1-2) or a digest (Sev 3-4), per org notification policy.

This service is part of the Downstream monorepo. The architecture is frozen — see
`/docs` for the source-of-truth design documents, and
`/docs/07_Downstream_Implementation_Blueprint.md` in particular for this
service's exact folder contract, database ownership, and API/event surface.

No business logic, APIs, or database tables have been implemented yet. This
folder is scaffold only, created as part of repository initialization.
