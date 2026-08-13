"""Connector-level idempotency cache — Reference Execution Trace Phase 1.1:
'The Procore adapter first checks its short-lived cache for
(resource_id, event_type, timestamp). Not seen before -- proceeds. Had
Procore redelivered this webhook, as at-least-once delivery permits, the
adapter would stop here.'

Table: connector_idempotency_cache (apps/connector-procore/migrations/0001).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from repository.db import get_connection

DEFAULT_TTL = timedelta(hours=24)


def build_cache_key(resource_name: str, resource_id: int, event_type: str, timestamp: str) -> str:
    return f"{resource_name}:{resource_id}:{event_type}:{timestamp}"


def already_seen(cache_key: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM connector_idempotency_cache WHERE cache_key = %s AND expires_at > now()",
            (cache_key,),
        ).fetchone()
        return row is not None


def mark_seen(cache_key: str, ttl: timedelta = DEFAULT_TTL) -> None:
    expires_at = datetime.now(timezone.utc) + ttl
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO connector_idempotency_cache (cache_key, expires_at)
            VALUES (%s, %s)
            ON CONFLICT (cache_key) DO NOTHING
            """,
            (cache_key, expires_at),
        )
