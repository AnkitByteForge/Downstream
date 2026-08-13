"""Read-only access to ingestion-service's `triggers` table — see
config/settings.py's module docstring for why this is a direct query
rather than a synchronous API call."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from repository.db import get_connection


@dataclass(frozen=True)
class TriggerRecord:
    trigger_id: str
    project_id: str
    type: str
    spec_section_refs: list[str]
    drawing_refs: list[dict]
    location_refs: list[str]
    occurred_at: datetime


def get_trigger(trigger_id: str) -> TriggerRecord | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT trigger_id, project_id, type, spec_section_refs, drawing_refs,
                   location_refs, occurred_at
            FROM triggers WHERE trigger_id = %s
            """,
            (trigger_id,),
        ).fetchone()
    if row is None:
        return None
    return TriggerRecord(
        trigger_id=row[0],
        project_id=row[1],
        type=row[2],
        spec_section_refs=list(row[3]),
        drawing_refs=list(row[4]),
        location_refs=list(row[5]),
        occurred_at=row[6],
    )
