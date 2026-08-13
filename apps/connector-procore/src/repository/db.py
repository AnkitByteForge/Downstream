"""Thin psycopg connection helper. No ORM — the tables this service touches
(connector_idempotency_cache, and reads from connector_configurations) are
small and simple enough that raw SQL is the honest, minimal choice; no
frozen document specifies an ORM for Downstream's own services."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg

from config.settings import settings


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    conn = psycopg.connect(settings.database_url, autocommit=True)
    try:
        yield conn
    finally:
        conn.close()
