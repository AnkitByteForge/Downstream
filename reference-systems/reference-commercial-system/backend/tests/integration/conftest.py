from __future__ import annotations

import pytest
from sqlalchemy.orm import sessionmaker

from infrastructure.persistence.db import engine


@pytest.fixture()
def db_session():
    """One connection, one outer transaction rolled back after the test —
    every integration test runs against the real Commercial System schema
    but leaves no trace, matching the Reference Engineering System's own
    convention (independent copy, no shared code — ADR-011)."""
    connection = engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
