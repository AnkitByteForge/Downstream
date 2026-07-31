from __future__ import annotations

import pytest

from infrastructure.persistence.db import engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def db_session():
    """One connection, one outer transaction rolled back after the test —
    every integration test runs against the real schema but leaves no trace,
    so these can run repeatedly against the same dev database."""
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
