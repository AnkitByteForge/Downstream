-- Owned by: connector-procore. Exact schema per
-- docs/07_Downstream_Implementation_Blueprint.md §6 ("owned by:
-- connector-procore, connector-sap, connector-email (one row-set per
-- adapter, same shape)"). This adapter's own copy, guarding against
-- webhook redelivery (docs/05 Phase 1.1) — upstream of, and independent
-- from, ingestion-service's own ingestion_idempotency table.

CREATE TABLE IF NOT EXISTS connector_idempotency_cache (
    cache_key    VARCHAR(128) PRIMARY KEY,   -- resource_name:resource_id:event_type:occurred_at
    expires_at   TIMESTAMPTZ NOT NULL
);
