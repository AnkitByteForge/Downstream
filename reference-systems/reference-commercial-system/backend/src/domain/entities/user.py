from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from domain.value_objects import PermissionScope

# Roles per the approved Commercial System Implementation Plan v1 §9,
# sourced from 02_Downstream_Product_Design.md's procurement-side personas.
USER_ROLES = ("PROCUREMENT_MANAGER", "BUYER", "PROJECT_CONTROLS_QS", "ADMIN")


@dataclass
class User:
    """A human who logs into this system's own web application. This
    system has no Project entity (unlike the Reference Engineering
    System) — Meridian Tower is represented purely through OrgScope, and a
    human user sees across every org scope, matching a real procurement
    manager's cross-plant oversight of one project."""

    id: int | None
    name: str
    email: str
    role: str
    password_hash: str


@dataclass
class OAuthClient:
    """An OAuth2 client_credentials integration client (docs/04: SAP/
    Oracle-shaped integration is service-account, not user-delegated — no
    authorization_code grant, no refresh token). Scoped to exactly one
    company_code, so org-scope isolation (ADR-015) is testable at the
    credential level, not merely at the query level."""

    id: int | None
    client_id: str
    client_secret_hash: str
    company_code: str
    permission_scope: PermissionScope


@dataclass
class OAuthToken:
    id: int | None
    access_token: str
    client_id: str
    expires_at: datetime
