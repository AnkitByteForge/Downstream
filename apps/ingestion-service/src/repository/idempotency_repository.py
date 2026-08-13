"""ingestion-service's own dedup layer — docs/03 Stage 2: 'deduplicates (via
the idempotency cache above)'; docs/06 item 5: 'the dedup check against the
idempotency cache' keyed on (source_system, source_id, occurred_at).
Independent from, and downstream of, connector-procore's own
connector_idempotency_cache (which guards against webhook redelivery, a
different failure mode from envelope resubmission by the connector itself)."""

from __future__ import annotations

from datetime import datetime

from repository.db import get_connection


def build_dedup_key(source_system: str, source_id: str, occurred_at: datetime) -> str:
    return f"{source_system}:{source_id}:{occurred_at.isoformat()}"


def existing_trigger_id(dedup_key: str) -> str | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT trigger_id FROM ingestion_idempotency WHERE dedup_key = %s", (dedup_key,)
        ).fetchone()
        return row[0] if row else None


def record(dedup_key: str, trigger_id: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO ingestion_idempotency (dedup_key, trigger_id)
            VALUES (%s, %s)
            ON CONFLICT (dedup_key) DO NOTHING
            """,
            (dedup_key, trigger_id),
        )
