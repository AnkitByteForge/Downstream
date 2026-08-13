from __future__ import annotations

from datetime import timedelta

import pytest

from application.exceptions import InvalidCredentials
from application.use_cases.auth_use_cases import LoginUser
from application.use_cases.oauth_use_cases import IssueTokenFromClientCredentials
from domain.entities.user import OAuthClient, User
from domain.value_objects import PermissionScope
from infrastructure.auth.opaque_token_service import SecureOpaqueTokenService
from infrastructure.auth.password_hashing import Pbkdf2PasswordHasher

from tests.unit.application.fakes import FakeClock, InMemoryOAuthClientRepository, InMemoryOAuthTokenRepository, InMemoryUserRepository


class _FakeSessionTokenService:
    def issue(self, claims) -> str:
        return f"token-for-{claims.user_id}-{claims.role}"

    def verify(self, token: str):
        raise NotImplementedError


def test_login_success() -> None:
    hasher = Pbkdf2PasswordHasher()
    user_repo = InMemoryUserRepository()
    user_repo.add(
        User(
            id=None,
            name="Ananya Rao",
            email="ananya.rao@meridiangc.example",
            role="PROCUREMENT_MANAGER",
            password_hash=hasher.hash("demo-password"),
        )
    )
    use_case = LoginUser(user_repo, hasher, _FakeSessionTokenService())
    token = use_case.execute("ananya.rao@meridiangc.example", "demo-password")
    assert "PROCUREMENT_MANAGER" in token


def test_login_wrong_password_raises() -> None:
    hasher = Pbkdf2PasswordHasher()
    user_repo = InMemoryUserRepository()
    user_repo.add(
        User(id=None, name="A", email="a@example.com", role="BUYER", password_hash=hasher.hash("correct"))
    )
    use_case = LoginUser(user_repo, hasher, _FakeSessionTokenService())
    with pytest.raises(InvalidCredentials):
        use_case.execute("a@example.com", "wrong")


def test_login_unknown_email_raises() -> None:
    hasher = Pbkdf2PasswordHasher()
    use_case = LoginUser(InMemoryUserRepository(), hasher, _FakeSessionTokenService())
    with pytest.raises(InvalidCredentials):
        use_case.execute("nobody@example.com", "whatever")


def test_issue_token_from_client_credentials_success() -> None:
    hasher = Pbkdf2PasswordHasher()
    client_repo = InMemoryOAuthClientRepository()
    client_repo.add(
        OAuthClient(
            id=None,
            client_id="cs-client",
            client_secret_hash=hasher.hash("secret"),
            company_code="1000",
            permission_scope=PermissionScope.full(),
        )
    )
    token_repo = InMemoryOAuthTokenRepository()
    clock = FakeClock()
    use_case = IssueTokenFromClientCredentials(
        client_repo, token_repo, SecureOpaqueTokenService(), hasher, clock, timedelta(hours=1)
    )
    token = use_case.execute("cs-client", "secret")
    assert token.client_id == "cs-client"
    assert token.expires_at == clock.now() + timedelta(hours=1)


def test_issue_token_wrong_secret_raises() -> None:
    hasher = Pbkdf2PasswordHasher()
    client_repo = InMemoryOAuthClientRepository()
    client_repo.add(
        OAuthClient(
            id=None,
            client_id="cs-client",
            client_secret_hash=hasher.hash("secret"),
            company_code="1000",
            permission_scope=PermissionScope.full(),
        )
    )
    use_case = IssueTokenFromClientCredentials(
        client_repo,
        InMemoryOAuthTokenRepository(),
        SecureOpaqueTokenService(),
        hasher,
        FakeClock(),
        timedelta(hours=1),
    )
    with pytest.raises(InvalidCredentials):
        use_case.execute("cs-client", "wrong-secret")


def test_issue_token_unknown_client_raises() -> None:
    hasher = Pbkdf2PasswordHasher()
    use_case = IssueTokenFromClientCredentials(
        InMemoryOAuthClientRepository(),
        InMemoryOAuthTokenRepository(),
        SecureOpaqueTokenService(),
        hasher,
        FakeClock(),
        timedelta(hours=1),
    )
    with pytest.raises(InvalidCredentials):
        use_case.execute("does-not-exist", "whatever")
