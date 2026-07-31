from __future__ import annotations

from datetime import datetime, timedelta, timezone

from infrastructure.rate_limit.store import RateLimitStore


def test_allows_requests_under_the_budget(db_session):
    store = RateLimitStore(db_session)
    now = datetime.now(timezone.utc)
    for _ in range(3):
        result = store.check_and_record("client-a", now, timedelta(seconds=60), max_requests=5)
        assert result.allowed

def test_denies_once_budget_is_exhausted(db_session):
    store = RateLimitStore(db_session)
    now = datetime.now(timezone.utc)
    for _ in range(3):
        store.check_and_record("client-b", now, timedelta(seconds=60), max_requests=3)
    result = store.check_and_record("client-b", now, timedelta(seconds=60), max_requests=3)
    assert not result.allowed
    assert result.retry_after_seconds > 0


def test_resets_after_the_window_elapses(db_session):
    store = RateLimitStore(db_session)
    start = datetime.now(timezone.utc)
    for _ in range(3):
        store.check_and_record("client-c", start, timedelta(seconds=60), max_requests=3)
    denied = store.check_and_record("client-c", start, timedelta(seconds=60), max_requests=3)
    assert not denied.allowed

    later = start + timedelta(seconds=61)
    allowed_again = store.check_and_record("client-c", later, timedelta(seconds=60), max_requests=3)
    assert allowed_again.allowed


def test_different_clients_have_independent_budgets(db_session):
    store = RateLimitStore(db_session)
    now = datetime.now(timezone.utc)
    for _ in range(3):
        store.check_and_record("client-d", now, timedelta(seconds=60), max_requests=3)
    other_client_result = store.check_and_record("client-e", now, timedelta(seconds=60), max_requests=3)
    assert other_client_result.allowed
