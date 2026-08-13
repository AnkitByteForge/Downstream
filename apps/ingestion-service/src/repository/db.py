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
