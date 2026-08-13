"""E.5 -- an authenticated HTTP client for RES's evidence-promotion API
(ADR-009). Uses RES's existing OAuth2 client_credentials grant; invents no
new authentication mechanism. Every credential is read from configuration
(environment variables by default), never hardcoded, never logged.

This module is deliberately narrow: it knows how to authenticate and how
to call exactly the two E.4 creation endpoints. It does not decide
idempotency policy, retry policy, or which facts are promotion-eligible --
those are the promotion orchestrator's job (E.6), which depends on this
client rather than embedding HTTP concerns itself.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

# --- Transport seam -----------------------------------------------------
# The one dependency-injection point in this module. Every test in
# tests/unit/test_res_client.py injects a fake transport; no test in the
# default suite makes a real network call or requires a live RES instance.


@dataclass(frozen=True)
class TransportResponse:
    status_code: int
    json_body: Any = None
    text: str = ""


class Transport(Protocol):
    def post(
        self,
        url: str,
        *,
        data: dict | None = None,
        json: dict | None = None,
        headers: dict | None = None,
        timeout: float | None = None,
    ) -> TransportResponse: ...

    def get(
        self, url: str, *, headers: dict | None = None, timeout: float | None = None
    ) -> TransportResponse: ...


class RequestsTransport:
    """The real, default transport -- a thin wrapper over `requests`. Kept
    as thin as possible so `Transport` (above) stays the actual contract
    tests and callers depend on, not this specific library."""

    def post(self, url, *, data=None, json=None, headers=None, timeout=None) -> TransportResponse:
        import requests

        resp = requests.post(url, data=data, json=json, headers=headers, timeout=timeout)
        return self._to_response(resp)

    def get(self, url, *, headers=None, timeout=None) -> TransportResponse:
        import requests

        resp = requests.get(url, headers=headers, timeout=timeout)
        return self._to_response(resp)

    @staticmethod
    def _to_response(resp) -> TransportResponse:
        try:
            body = resp.json()
        except ValueError:
            body = None
        return TransportResponse(status_code=resp.status_code, json_body=body, text=resp.text)


# --- Structured errors ----------------------------------------------------
# Deliberately a small hierarchy, not one generic exception -- E.6's retry
# policy needs to distinguish retryable failures (connection/timeout/5xx)
# from non-retryable ones (4xx: a malformed request will never succeed on
# retry) without string-matching an error message.


class ResClientError(Exception):
    """Base class for every error this client raises."""

    retryable: bool = False


class ResConnectionError(ResClientError):
    retryable = True

    def __init__(self, url: str, cause: Exception) -> None:
        self.url = url
        super().__init__(f"Could not connect to RES at {url}: {cause}")


class ResTimeoutError(ResClientError):
    retryable = True

    def __init__(self, url: str, timeout: float) -> None:
        self.url = url
        self.timeout = timeout
        super().__init__(f"RES request to {url} timed out after {timeout}s")


class ResHttpError(ResClientError):
    def __init__(self, url: str, status_code: int, body: Any) -> None:
        self.url = url
        self.status_code = status_code
        self.body = body
        self.retryable = status_code >= 500
        super().__init__(f"RES returned HTTP {status_code} for {url}: {body!r}")


class ResAuthenticationError(ResClientError):
    """The client_id/client_secret were rejected. Never retryable -- a
    bad credential does not become good on retry, and retrying would only
    hammer RES's auth endpoint."""

    retryable = False

    def __init__(self, url: str) -> None:
        self.url = url
        super().__init__(f"RES rejected the configured OAuth2 client credentials at {url}")


# --- Configuration ---------------------------------------------------------
# Every field is read from environment variables by default (never
# hardcoded, never committed) -- see README's "RES promotion client setup"
# section for the exact variable names, added alongside this module.

_ENV_BASE_URL = "DIP_RES_BASE_URL"
_ENV_CLIENT_ID = "DIP_RES_CLIENT_ID"
_ENV_CLIENT_SECRET = "DIP_RES_CLIENT_SECRET"
_ENV_TIMEOUT_SECONDS = "DIP_RES_TIMEOUT_SECONDS"

_DEFAULT_TIMEOUT_SECONDS = 10.0
# Refresh the token slightly before it actually expires, so a long-running
# promotion batch never sends a request with a token that expires between
# this check and RES receiving it.
_TOKEN_EXPIRY_SAFETY_MARGIN_SECONDS = 30.0


@dataclass(frozen=True)
class ResClientConfig:
    base_url: str
    client_id: str
    client_secret: str
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS

    @classmethod
    def from_env(cls) -> "ResClientConfig":
        """Reads every field from environment variables. Raises a clear,
        immediate error naming the missing variable rather than deferring
        to a confusing failure deep inside a later HTTP call -- credentials
        are a configuration precondition, not a runtime surprise."""
        missing = [
            name
            for name in (_ENV_BASE_URL, _ENV_CLIENT_ID, _ENV_CLIENT_SECRET)
            if not os.environ.get(name)
        ]
        if missing:
            raise ResClientError(
                f"Missing required environment variable(s) for the RES promotion client: {', '.join(missing)}"
            )
        timeout_raw = os.environ.get(_ENV_TIMEOUT_SECONDS)
        return cls(
            base_url=os.environ[_ENV_BASE_URL].rstrip("/"),
            client_id=os.environ[_ENV_CLIENT_ID],
            client_secret=os.environ[_ENV_CLIENT_SECRET],
            timeout_seconds=float(timeout_raw) if timeout_raw else _DEFAULT_TIMEOUT_SECONDS,
        )

    def __repr__(self) -> str:
        # Never let a stray `print(config)` / log line leak the secret.
        return (
            f"ResClientConfig(base_url={self.base_url!r}, client_id={self.client_id!r}, "
            f"client_secret='***redacted***', timeout_seconds={self.timeout_seconds})"
        )


# --- The client -------------------------------------------------------------


class ResPromotionClient:
    """Authenticated caller of RES's evidence-promotion API (E.4). Reuses
    one access token across calls until it's within
    _TOKEN_EXPIRY_SAFETY_MARGIN_SECONDS of expiring, then transparently
    re-authenticates -- callers never need to think about token lifecycle.
    """

    def __init__(
        self,
        config: ResClientConfig,
        transport: Transport | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._config = config
        self._transport = transport or RequestsTransport()
        self._clock = clock or time.monotonic
        self._access_token: str | None = None
        self._token_expires_at_monotonic: float | None = None

    # -- authentication ----------------------------------------------------

    def _ensure_token(self) -> str:
        now = self._clock()
        if (
            self._access_token is not None
            and self._token_expires_at_monotonic is not None
            and now < self._token_expires_at_monotonic - _TOKEN_EXPIRY_SAFETY_MARGIN_SECONDS
        ):
            return self._access_token

        url = f"{self._config.base_url}/oauth/token"
        try:
            resp = self._transport.post(
                url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._config.client_id,
                    "client_secret": self._config.client_secret,
                },
                timeout=self._config.timeout_seconds,
            )
        except _CONNECTION_EXCEPTIONS as exc:
            raise ResConnectionError(url, exc) from exc
        except _TIMEOUT_EXCEPTIONS as exc:
            raise ResTimeoutError(url, self._config.timeout_seconds) from exc

        if resp.status_code == 401:
            # Deliberately does not include the rejected secret anywhere in
            # the raised error -- see ResAuthenticationError's message.
            raise ResAuthenticationError(url)
        if resp.status_code >= 400:
            raise ResHttpError(url, resp.status_code, resp.json_body)

        body = resp.json_body or {}
        self._access_token = body["access_token"]
        self._token_expires_at_monotonic = now + float(body["expires_in"])
        return self._access_token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._ensure_token()}"}

    # -- requests -----------------------------------------------------------

    def _post_json(self, path: str, payload: dict) -> dict:
        url = f"{self._config.base_url}{path}"
        try:
            resp = self._transport.post(
                url, json=payload, headers=self._headers(), timeout=self._config.timeout_seconds
            )
        except _CONNECTION_EXCEPTIONS as exc:
            raise ResConnectionError(url, exc) from exc
        except _TIMEOUT_EXCEPTIONS as exc:
            raise ResTimeoutError(url, self._config.timeout_seconds) from exc

        if resp.status_code >= 400:
            raise ResHttpError(url, resp.status_code, resp.json_body)
        return resp.json_body or {}

    # -- public API: exactly the two E.4 creation endpoints -----------------

    def create_drawing(self, project_id: int, sheet_number: str, title: str, discipline_code: str) -> dict:
        """POST .../documents. Idempotent on RES's side (E.4) -- calling
        this twice with the same (project_id, sheet_number) returns the
        same Drawing, never creates a duplicate."""
        return self._post_json(
            f"/rest/v1.0/projects/{project_id}/documents",
            {"sheet_number": sheet_number, "title": title, "discipline_code": discipline_code},
        )

    def create_drawing_version(
        self,
        project_id: int,
        drawing_id: int,
        revision_label: str,
        discipline_code: str,
        revision_clouds: list[dict] | None = None,
    ) -> dict:
        """POST .../documents/{drawing_id}/versions. Idempotent on RES's
        side (E.4) -- calling this twice with the same (drawing_id,
        revision_label) returns the same DrawingVersion, never creates a
        duplicate. `revision_clouds` entries are plain dicts shaped like
        RES's RevisionCloudIn schema: {area, delta_number, description,
        source_evidence_ref}."""
        return self._post_json(
            f"/rest/v1.0/projects/{project_id}/documents/{drawing_id}/versions",
            {
                "revision_label": revision_label,
                "discipline_code": discipline_code,
                "revision_clouds": revision_clouds or [],
            },
        )


def _import_requests_exceptions():
    try:
        import requests.exceptions as exc

        return (exc.ConnectionError,), (exc.Timeout,)
    except ImportError:  # pragma: no cover - requests is a hard dependency
        return (), ()


_CONNECTION_EXCEPTIONS, _TIMEOUT_EXCEPTIONS = _import_requests_exceptions()
