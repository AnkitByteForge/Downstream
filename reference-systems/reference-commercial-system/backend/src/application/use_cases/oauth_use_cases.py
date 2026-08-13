from __future__ import annotations

from datetime import timedelta

from domain.entities.user import OAuthToken
from domain.repositories.user_repository import OAuthClientRepository, OAuthTokenRepository

from application.exceptions import InvalidCredentials
from application.ports import ClockPort, OpaqueTokenServicePort, PasswordHasherPort


class IssueTokenFromClientCredentials:
    """grant_type=client_credentials — the only grant this system supports
    (docs/04: SAP/Oracle-shaped integration is service-account, headless,
    server-to-server; there is no user present to complete an
    authorization_code exchange, and no refresh_token dance — the client
    simply re-authenticates with its own long-lived client_secret when its
    access token expires)."""

    def __init__(
        self,
        client_repo: OAuthClientRepository,
        token_repo: OAuthTokenRepository,
        opaque_tokens: OpaqueTokenServicePort,
        hasher: PasswordHasherPort,
        clock: ClockPort,
        access_token_ttl: timedelta,
    ) -> None:
        self._client_repo = client_repo
        self._token_repo = token_repo
        self._opaque_tokens = opaque_tokens
        self._hasher = hasher
        self._clock = clock
        self._ttl = access_token_ttl

    def execute(self, client_id: str, client_secret: str) -> OAuthToken:
        client = self._client_repo.get_by_client_id(client_id)
        if client is None or not self._hasher.verify(client_secret, client.client_secret_hash):
            raise InvalidCredentials("Invalid client_id or client_secret")
        token = OAuthToken(
            id=None,
            access_token=self._opaque_tokens.generate(),
            client_id=client_id,
            expires_at=self._clock.now() + self._ttl,
        )
        return self._token_repo.add(token)
