"""Outbound REST client to the real Reference Engineering System — the
approved Milestone 1 integration target (RES plays the Procore/ACC-shaped
role a real connector-procore would otherwise point at a mock for).

RES contracts verified directly against its source
(reference-systems/reference-engineering-system/backend/src), not assumed
from the illustrative Reference Execution Trace payload. Two concrete,
recorded deviations from that illustrative payload:

1. Webhook signature header is `X-Signature` (infrastructure/webhooks/
   signing.py), not docs/05's illustrative `X-Procore-Signature`.
2. RFI.status is uppercase "CLOSED" (domain/entities/rfi.py RFI_STATUSES),
   not docs/05's illustrative lowercase "closed".
3. RES's real RFI resource (api/schemas/rfi.py RFIOut) exposes only internal
   numeric ID arrays for spec/drawing/location references
   (spec_section_ids, drawing_version_ids, location_ids) — NOT the
   human-readable strings docs/05's illustrative enrichment payload shows
   embedded directly (spec_section_references, drawing_references). This
   client therefore performs the additional resolution calls RES's real API
   actually requires (spec_sections list, locations list, per-version and
   per-drawing GET) that the illustrative single-GET trace did not show.

Auth: grant_type=client_credentials (application/use_cases/oauth_use_cases.py
IssueTokenFromClientCredentials, ADR-009) — the headless, server-to-server
grant RES built for exactly this caller shape, chosen over authorization_code
to avoid persisting/rotating a single-use-code-derived refresh token across
this service's own restarts (RES's seeded OAuthClient rows work with either
grant; both authenticate the same client_id/client_secret pair).
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx

from repository.connector_configuration_repository import ConnectorConfiguration


@dataclass
class ResolvedRFI:
    res_project_id: int
    rfi: dict
    spec_section_numbers: list[str]
    drawing_refs: list[tuple[str, str]]  # (sheet_number, revision_label)
    location_names: list[str]


class ResClient:
    def __init__(self, config: ConnectorConfiguration, timeout_seconds: float = 10.0) -> None:
        self._config = config
        self._timeout = timeout_seconds
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._get_token()}"}

    def _get_token(self) -> str:
        if self._access_token is not None and time.monotonic() < self._token_expires_at:
            return self._access_token
        resp = httpx.post(
            self._config.oauth_token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self._config.oauth_client_id,
                "client_secret": self._config.oauth_client_secret,
            },
            timeout=self._timeout,
        )
        resp.raise_for_status()
        body = resp.json()
        self._access_token = body["access_token"]
        # Refresh a little before the real expiry to avoid a request racing
        # against expiry mid-flight; RES's ACCESS_TOKEN_TTL is 1 hour.
        self._token_expires_at = time.monotonic() + max(body["expires_in"] - 30, 0)
        return self._access_token

    def get_rfi(self, project_id: int, rfi_id: int) -> dict:
        """The enrichment GET-back — Reference Execution Trace Phase 1.2."""
        resp = httpx.get(
            f"{self._config.base_url}/rest/v1.0/projects/{project_id}/rfis/{rfi_id}",
            headers=self._headers(),
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def resolve_rfi_references(self, project_id: int, rfi: dict) -> ResolvedRFI:
        """Turns RES's internal numeric ID arrays on the RFI into the
        human-readable reference strings EngineeringEventEnvelope needs —
        the additional resolution work RES's real API requires beyond the
        illustrative trace's single enrichment GET (module docstring, point 3)."""
        headers = self._headers()

        spec_section_numbers: list[str] = []
        if rfi["spec_section_ids"]:
            resp = httpx.get(
                f"{self._config.base_url}/rest/v1.0/projects/{project_id}/spec_sections",
                headers=headers,
                params={"per_page": 100},
                timeout=self._timeout,
            )
            resp.raise_for_status()
            by_id = {s["id"]: s for s in resp.json()}
            spec_section_numbers = [
                by_id[sid]["number"] for sid in rfi["spec_section_ids"] if sid in by_id
            ]

        location_names: list[str] = []
        if rfi["location_ids"]:
            resp = httpx.get(
                f"{self._config.base_url}/rest/v1.0/projects/{project_id}/locations",
                headers=headers,
                params={"per_page": 100},
                timeout=self._timeout,
            )
            resp.raise_for_status()
            by_id = {loc["id"]: loc for loc in resp.json()}
            location_names = [by_id[lid]["name"] for lid in rfi["location_ids"] if lid in by_id]

        drawing_refs: list[tuple[str, str]] = []
        for version_id in rfi["drawing_version_ids"]:
            version_resp = httpx.get(
                f"{self._config.base_url}/rest/v1.0/projects/{project_id}/documents/versions/{version_id}",
                headers=headers,
                timeout=self._timeout,
            )
            version_resp.raise_for_status()
            version = version_resp.json()
            drawing_resp = httpx.get(
                f"{self._config.base_url}/rest/v1.0/projects/{project_id}/documents/{version['drawing_id']}",
                headers=headers,
                timeout=self._timeout,
            )
            drawing_resp.raise_for_status()
            drawing = drawing_resp.json()
            drawing_refs.append((drawing["sheet_number"], version["revision_label"]))

        return ResolvedRFI(
            res_project_id=project_id,
            rfi=rfi,
            spec_section_numbers=spec_section_numbers,
            drawing_refs=drawing_refs,
            location_names=location_names,
        )
