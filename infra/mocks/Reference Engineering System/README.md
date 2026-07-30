# mock-engineering-system

Mock Procore/ACC — models the shared shape of the engineering systems of
record, per `04_Downstream_Connector_Layer_Validation.md`. Its job is to lie
to the Connector adapters exactly as convincingly, and exactly as
inconveniently, as the real systems will: thin webhook payloads requiring a
GET-back, OAuth2 token refresh, rate limiting/pagination, and configurable
permission scoping.

No mock behavior has been implemented yet. This folder is scaffold only.
