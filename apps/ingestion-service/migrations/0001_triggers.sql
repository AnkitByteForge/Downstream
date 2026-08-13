-- Owned by: ingestion-service. Exact schema per
-- docs/07_Downstream_Implementation_Blueprint.md §6.

CREATE TABLE IF NOT EXISTS triggers (
    trigger_id            VARCHAR(32) PRIMARY KEY,
    project_id            VARCHAR(32) NOT NULL,
    type                   VARCHAR(32) NOT NULL,           -- RFI_APPROVED | DRAWING_REVISED | SPEC_UPDATED
    source_envelope_ref    VARCHAR(64) NOT NULL,
    spec_section_refs      JSONB NOT NULL DEFAULT '[]',
    drawing_refs           JSONB NOT NULL DEFAULT '[]',    -- [{item_id, version_id}]
    location_refs          JSONB NOT NULL DEFAULT '[]',
    raw_document_ref       TEXT,
    occurred_at            TIMESTAMPTZ NOT NULL,
    status                 VARCHAR(24) NOT NULL DEFAULT 'PENDING_RESOLUTION',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_triggers_project ON triggers(project_id);
