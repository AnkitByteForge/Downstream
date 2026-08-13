-- Milestone 0 — artifact identity map, exact schema per
-- docs/07_Downstream_Implementation_Blueprint.md §6 ("owned by: connector
-- layer, shared across adapters — the 'PO-4471 is really SAP PO 4500018823'
-- mapping").
--
-- SYNTHETIC/UNBACKED WARNING — deliberately empty in this milestone.
-- No rows are inserted here. The Reference Commercial System is being
-- implemented as a separate, independent system and does not exist as a
-- callable target yet — there is no real (or mock) commercial identifier for
-- any Milestone-1 artifact to map to. Per explicit instruction, this
-- milestone does not fabricate synthetic/unbacked commercial identities to
-- fill this table. The table exists now (satisfying the frozen blueprint's
-- Milestone-0 schema requirement) so that Milestone 2, once a real
-- Reference Commercial System identity exists, can populate it without any
-- schema change — the table is the isolation boundary the instruction asked
-- for: empty and ready, never fake.

CREATE TABLE IF NOT EXISTS artifact_identity_map (
    artifact_ref       VARCHAR(32) NOT NULL,
    project_id         VARCHAR(32) NOT NULL,
    source_system      VARCHAR(24) NOT NULL,   -- procore|sap|acc|oracle|erpnext
    source_identifier  VARCHAR(64) NOT NULL,
    org_scope          JSONB DEFAULT '{}',
    PRIMARY KEY (artifact_ref, source_system)
);
