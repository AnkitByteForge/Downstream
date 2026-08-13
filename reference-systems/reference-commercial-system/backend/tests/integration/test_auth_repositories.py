from __future__ import annotations

from datetime import datetime, timedelta, timezone

from domain.entities.user import OAuthClient, OAuthToken, User
from domain.value_objects import PermissionScope
from infrastructure.csrf.store import CsrfTokenStore
from infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SqlAlchemyOAuthClientRepository,
    SqlAlchemyOAuthTokenRepository,
    SqlAlchemyUserRepository,
)


def test_user_round_trips_and_get_by_email(db_session) -> None:
    # Deliberately not a canonical seed email (e.g. Ananya Rao's) — this
    # is a real, rollback-isolated fixture row, but the canonical seed
    # itself is committed permanently, so reusing its business keys here
    # would collide with it (a genuine bug this exact scenario caught
    # once already; see the CS-1 completion report).
    repo = SqlAlchemyUserRepository(db_session)
    created = repo.add(
        User(
            id=None,
            name="Integration Test User",
            email="integration.test.user@example.com",
            role="PROCUREMENT_MANAGER",
            password_hash="hashed",
        )
    )
    fetched = repo.get_by_email("integration.test.user@example.com")
    assert fetched.id == created.id
    assert fetched.role == "PROCUREMENT_MANAGER"


def test_oauth_client_round_trips_with_permission_scope(db_session) -> None:
    # client_id deliberately distinct from the canonical seed's own
    # "downstream-partial-scope" client, which is committed permanently.
    repo = SqlAlchemyOAuthClientRepository(db_session)
    created = repo.add(
        OAuthClient(
            id=None,
            client_id="integration-test-partial-scope",
            client_secret_hash="hashed",
            company_code="1000",
            permission_scope=PermissionScope.partial("purchase_orders", "vendors"),
        )
    )
    fetched = repo.get_by_client_id("integration-test-partial-scope")
    assert fetched.company_code == "1000"
    assert fetched.permission_scope.grants("purchase_orders")
    assert not fetched.permission_scope.grants("commitments")


def test_oauth_client_full_scope_grants_everything(db_session) -> None:
    repo = SqlAlchemyOAuthClientRepository(db_session)
    repo.add(
        OAuthClient(
            id=None,
            client_id="integration-test-full-scope",
            client_secret_hash="hashed",
            company_code="1000",
            permission_scope=PermissionScope.full(),
        )
    )
    fetched = repo.get_by_client_id("integration-test-full-scope")
    assert fetched.permission_scope.grants("anything_at_all")


def test_oauth_token_round_trips(db_session) -> None:
    repo = SqlAlchemyOAuthTokenRepository(db_session)
    expires = datetime(2026, 8, 1, tzinfo=timezone.utc)
    repo.add(OAuthToken(id=None, access_token="opaque-token-abc", client_id="cs-client", expires_at=expires))
    fetched = repo.get_by_access_token("opaque-token-abc")
    assert fetched.client_id == "cs-client"
    assert fetched.expires_at == expires


def test_csrf_token_issue_and_single_use_consume(db_session) -> None:
    store = CsrfTokenStore(db_session)
    now = datetime(2026, 7, 30, tzinfo=timezone.utc)
    token = store.issue("human:1", now, timedelta(minutes=15))

    assert store.validate_and_consume("human:1", token, now) is True
    # single-use: a second consume of the same token must fail
    assert store.validate_and_consume("human:1", token, now) is False


def test_csrf_token_rejects_wrong_actor(db_session) -> None:
    store = CsrfTokenStore(db_session)
    now = datetime(2026, 7, 30, tzinfo=timezone.utc)
    token = store.issue("human:1", now, timedelta(minutes=15))
    assert store.validate_and_consume("integration:some-client", token, now) is False


def test_csrf_token_rejects_expired(db_session) -> None:
    store = CsrfTokenStore(db_session)
    now = datetime(2026, 7, 30, tzinfo=timezone.utc)
    token = store.issue("human:1", now, timedelta(minutes=15))
    later = now + timedelta(minutes=16)
    assert store.validate_and_consume("human:1", token, later) is False


def test_csrf_token_rejects_unknown_token(db_session) -> None:
    store = CsrfTokenStore(db_session)
    now = datetime(2026, 7, 30, tzinfo=timezone.utc)
    assert store.validate_and_consume("human:1", "not-a-real-token", now) is False
