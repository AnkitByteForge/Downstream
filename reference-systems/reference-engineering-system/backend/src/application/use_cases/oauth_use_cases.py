from __future__ import annotations

from datetime import timedelta

from application.exceptions import InvalidCredentials, Unauthorized
from application.ports import ClockPort, OpaqueTokenServicePort, PasswordHasherPort
from domain.entities import OAuthToken
from domain.repositories import OAuthClientRepository, OAuthTokenRepository

ACCESS_TOKEN_TTL = timedelta(hours=1)


def _authenticate_client(
    client_repo: OAuthClientRepository,
    hasher: PasswordHasherPort,
    client_id: str,
    client_secret: str,
):
    client = client_repo.get(client_id)
    if client is None or not hasher.verify(client_secret, client.client_secret_hash):
        raise InvalidCredentials("Invalid client_id or client_secret")
    return client


class IssueTokenFromAuthorizationCode:
    """grant_type=authorization_code — the initial connect. The code is
    single-use, matching real OAuth2 and forcing a genuine exchange rather
    than a reusable shared secret."""

    def __init__(
        self,
        client_repo: OAuthClientRepository,
        token_repo: OAuthTokenRepository,
        opaque_tokens: OpaqueTokenServicePort,
        hasher: PasswordHasherPort,
        clock: ClockPort,
    ) -> None:
        self._client_repo = client_repo
        self._token_repo = token_repo
        self._opaque_tokens = opaque_tokens
        self._hasher = hasher
        self._clock = clock

    def execute(self, client_id: str, client_secret: str, code: str) -> OAuthToken:
        client = _authenticate_client(self._client_repo, self._hasher, client_id, client_secret)
        if client.authorization_code is None or client.authorization_code != code:
            raise Unauthorized("Invalid or already-consumed authorization code")
        token = OAuthToken(
            access_token=self._opaque_tokens.generate(),
            refresh_token=self._opaque_tokens.generate(),
            client_id=client_id,
            expires_at=self._clock.now() + ACCESS_TOKEN_TTL,
        )
        self._client_repo.consume_authorization_code(client_id)
        return self._token_repo.add(token)


class RefreshOAuthToken:
    """grant_type=refresh_token — genuinely exercises token-refresh logic
    rather than assuming an adapter implements it correctly (docs/04)."""

    def __init__(
        self,
        client_repo: OAuthClientRepository,
        token_repo: OAuthTokenRepository,
        opaque_tokens: OpaqueTokenServicePort,
        hasher: PasswordHasherPort,
        clock: ClockPort,
    ) -> None:
        self._client_repo = client_repo
        self._token_repo = token_repo
        self._opaque_tokens = opaque_tokens
        self._hasher = hasher
        self._clock = clock

    def execute(self, client_id: str, client_secret: str, refresh_token: str) -> OAuthToken:
        _authenticate_client(self._client_repo, self._hasher, client_id, client_secret)
        existing = self._token_repo.get_by_refresh_token(refresh_token)
        if existing is None or existing.client_id != client_id:
            raise Unauthorized("Invalid refresh token")
        self._token_repo.delete(existing.access_token)
        new_token = OAuthToken(
            access_token=self._opaque_tokens.generate(),
            refresh_token=self._opaque_tokens.generate(),
            client_id=client_id,
            expires_at=self._clock.now() + ACCESS_TOKEN_TTL,
        )
        return self._token_repo.add(new_token)
