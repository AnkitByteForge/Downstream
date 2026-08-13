-- Milestone 0 — connector configuration store (infra/migrations/README.md's
-- own stated scope: "the artifact identity map, the connector configuration
-- store, and the initial seeded Graph Layer").
--
-- Owned at the Connector Layer level (docs/07 §6 gives artifact_identity_map
-- the same "owned by: connector layer, shared across adapters" treatment;
-- no frozen document gives connector configuration an exact SQL shape, so
-- this is the minimal viable slice of that concept: enough for
-- connector-procore to authenticate against and call its one configured
-- source system in Milestone 1. Physically one Postgres instance
-- (operational-db) per docs/07 §6's "logically separate, physically one
-- Postgres instance at this scale."
--
-- Per docs/03's multi-tenancy rule, every row is project-scoped. Per docs/03
-- "Connector credentials are... stored in a secrets boundary the Connector
-- Layer alone can access" — in this dev/demo milestone that boundary is this
-- table itself (no separate secrets manager is specified by any frozen
-- document); production would move oauth_client_secret to a real secrets
-- manager, out of scope here.

CREATE TABLE IF NOT EXISTS connector_configurations (
    connection_id       VARCHAR(32)  PRIMARY KEY,
    project_id           VARCHAR(32)  NOT NULL,   -- Downstream's own project_id
    source_system         VARCHAR(24)  NOT NULL,   -- 'procore' (RES plays this role for Milestone 1)
    base_url               TEXT         NOT NULL,
    oauth_token_url         TEXT         NOT NULL,
    oauth_client_id           TEXT         NOT NULL,
    oauth_client_secret        TEXT         NOT NULL,
    granted_scope               JSONB        NOT NULL DEFAULT '[]',   -- e.g. ["rfis","submittals","documents"]
    integration_tier             VARCHAR(16)  NOT NULL DEFAULT 'read_only',
    webhook_secret                 TEXT         NOT NULL,   -- HMAC secret for verifying inbound webhook signatures
    created_at                       TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_connector_configurations_project_system
    ON connector_configurations(project_id, source_system);
