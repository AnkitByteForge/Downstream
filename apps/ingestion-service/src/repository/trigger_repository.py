"""Owns the `triggers` table — the first durable write in the whole system
(docs/03 Stage 2)."""

from __future__ import annotations

import json

from domain_models.trigger import Trigger

from repository.db import get_connection


def insert(trigger: Trigger) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO triggers (
                trigger_id, project_id, type, source_envelope_ref,
                spec_section_refs, drawing_refs, location_refs,
                raw_document_ref, occurred_at, status, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
            """,
            (
                trigger.trigger_id,
                trigger.project_id,
                trigger.type,
                trigger.source_envelope_ref,
                json.dumps(trigger.spec_section_refs),
                json.dumps([r.model_dump(mode="json") for r in trigger.drawing_refs]),
                json.dumps(trigger.location_refs),
                trigger.raw_document_ref,
                trigger.occurred_at,
                trigger.status,
            ),
        )


def get(trigger_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT trigger_id, project_id, type, source_envelope_ref,
                   spec_section_refs, drawing_refs, location_refs,
                   raw_document_ref, occurred_at, status, created_at
            FROM triggers WHERE trigger_id = %s
            """,
            (trigger_id,),
        ).fetchone()
    if row is None:
        return None
    return {
        "trigger_id": row[0],
        "project_id": row[1],
        "type": row[2],
        "source_envelope_ref": row[3],
        "spec_section_refs": row[4],
        "drawing_refs": row[5],
        "location_refs": row[6],
        "raw_document_ref": row[7],
        "occurred_at": row[8],
        "status": row[9],
        "created_at": row[10],
    }


def count_by_project(project_id: str) -> int:
    with get_connection() as conn:
        row = conn.execute("SELECT count(*) FROM triggers WHERE project_id = %s", (project_id,)).fetchone()
        return row[0]
