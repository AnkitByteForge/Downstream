"""Writes to `artifact_identity_map` (infra/migrations/0002_artifact_identity_map.sql
— schema owned at the Connector Layer level per blueprint §6; this service
is the interim writer for Milestone 2, since no connector-sap exists yet to
own it — a recorded scope decision, not silent assumption, per the
approved Milestone 2 plan's §E)."""

from __future__ import annotations

import json

from repository.db import get_connection
from domain.resolution import ResolvedCandidate

SOURCE_SYSTEM = "reference-commercial-system"


def upsert(project_id: str, candidate: ResolvedCandidate) -> None:
    org_scope = {"company_code": candidate.company_code, "plant": candidate.plant}
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO artifact_identity_map (artifact_ref, project_id, source_system, source_identifier, org_scope)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (artifact_ref, source_system) DO UPDATE SET
                project_id = EXCLUDED.project_id,
                source_identifier = EXCLUDED.source_identifier,
                org_scope = EXCLUDED.org_scope
            """,
            (
                candidate.artifact_ref,
                project_id,
                SOURCE_SYSTEM,
                candidate.source_identifier,
                json.dumps(org_scope),
            ),
        )
