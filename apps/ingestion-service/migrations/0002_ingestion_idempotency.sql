-- Owned by: ingestion-service. Not given an exact SQL shape by any frozen
-- document; docs/03 Stage 2 and docs/06 item 5 both name the behavior
-- ("dedup check against the idempotency cache", keyed on
-- (source_system, source_id, occurred_at)) without specifying columns, so
-- this is the minimal table that behavior requires. Distinct from
-- connector-procore's own connector_idempotency_cache (webhook redelivery
-- dedup, upstream of this one) — this is the second, independent dedup
-- layer docs/03's "Consistency, idempotency, and failure" section calls for
-- against envelope resubmission from the connector's own retry behavior.

CREATE TABLE IF NOT EXISTS ingestion_idempotency (
    dedup_key    VARCHAR(160) PRIMARY KEY,   -- source_system:source_id:occurred_at
    trigger_id   VARCHAR(32) NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
