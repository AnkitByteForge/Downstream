from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from domain.value_objects import PermissionScope

# Roles per Reference Engineering System doc §1, "Role division observed in practice".
USER_ROLES = (
    "PROJECT_MANAGER",
    "PROJECT_ENGINEER",
    "SUBCONTRACTOR",
    "ARCHITECT_ENGINEER_OF_RECORD",
    "ADMIN",
)


@dataclass
class User:
    """A human who logs into this system's own web application — distinct
    from IntegrationUser, which authenticates a machine/API client. Keeping
    these separate preserves the acting_credential_scope distinction docs/04
    cares about: a human login is never mistaken for a scoped API connection.
    """

    id: int | None
    project_id: int
    name: str
    email: str
    role: str
    password_hash: str


@dataclass
class IntegrationUser:
    """The seeded credential an OAuth2 client authenticates as — carries the
    permission scope that becomes acting_credential_scope on anything it fetches.
    """

    id: int | None
    project_id: int
    name: str
    permission_scope: PermissionScope


@dataclass
class OAuthClient:
    client_id: str
    client_secret_hash: str
    integration_user_id: int
    authorization_code: str | None = None  # single-use, seeded for this reference system


@dataclass
class OAuthToken:
    access_token: str
    refresh_token: str
    client_id: str
    expires_at: datetime
