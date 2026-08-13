-- Milestone 2 — found while implementing key-resolution-service's
-- artifact_identity_map write path: the approved implementation
-- instruction specifies source_system = "reference-commercial-system"
-- (28 chars) literally, but 0002_artifact_identity_map.sql's
-- source_system column is VARCHAR(24) — sized for the blueprint's own
-- comment ("procore|sap|acc|oracle|erpnext", all <=7 chars), which never
-- anticipated a full reference-system name as the value. This is
-- Downstream's own table (artifact_identity_map, owned at the Connector
-- Layer level per blueprint §6) — not a change to RES or RCS.
--
-- Additive widening, not an in-place edit of 0002's already-applied
-- migration (matching the additive-migration discipline RES/RCS's own
-- Alembic chains already use).

ALTER TABLE artifact_identity_map ALTER COLUMN source_system TYPE VARCHAR(64);
