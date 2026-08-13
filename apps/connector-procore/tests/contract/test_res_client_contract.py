"""Contract test — runs against the REAL Reference Engineering System, per
docs/04's discipline ('write contract tests... run the identical suite
against both the mock and, eventually, a real sandbox tenant'), except here
there is no separate mock to also run against: RES *is* Milestone 1's real
integration target (approved decision).

Skipped automatically if RES isn't reachable — these are meant to run
against the live Docker Compose stack (infra/docker-compose.yml), not on
every bare `pytest -q` at the repo root. See IMPLEMENTATION_STATUS.md-style
"how to verify this state yourself" instructions in the Milestone 1 report
for how to bring the stack up first.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from client.res_client import ResClient
from repository.connector_configuration_repository import ConnectorConfiguration

RES_BASE_URL = os.environ.get("RES_BASE_URL", "http://localhost:8000")


def _res_reachable() -> bool:
    try:
        resp = httpx.get(f"{RES_BASE_URL}/health", timeout=2.0)
        return resp.status_code == 200
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(
    not _res_reachable(), reason=f"Reference Engineering System not reachable at {RES_BASE_URL}"
)


@pytest.fixture()
def config() -> ConnectorConfiguration:
    return ConnectorConfiguration(
        connection_id="conn_res_meridian",
        project_id="proj_meridian_tower",
        source_system="procore",
        base_url=RES_BASE_URL,
        oauth_token_url=f"{RES_BASE_URL}/oauth/token",
        oauth_client_id="downstream-partial",
        oauth_client_secret="partial-scope-secret",
        granted_scope=["rfis", "submittals", "documents"],
        integration_tier="read_only",
        webhook_secret="seed-webhook-secret",
    )


def test_client_credentials_grant_issues_bearer_token(config):
    client = ResClient(config)
    token = client._get_token()
    assert isinstance(token, str) and len(token) > 0


def test_can_fetch_and_resolve_rfi_214(config):
    client = ResClient(config)
    projects = httpx.get(
        f"{RES_BASE_URL}/rest/v1.0/projects", headers={"Authorization": f"Bearer {client._get_token()}"}
    ).json()
    assert len(projects) == 1
    project_id = projects[0]["id"]

    rfis = httpx.get(
        f"{RES_BASE_URL}/rest/v1.0/projects/{project_id}/rfis",
        headers={"Authorization": f"Bearer {client._get_token()}"},
        params={"per_page": 100},
    ).json()
    rfi = next(r for r in rfis if r["display_number"] == "RFI-214")
    assert rfi["status"] == "CLOSED"

    full_rfi = client.get_rfi(project_id, rfi["id"])
    assert full_rfi["display_number"] == "RFI-214"
    assert full_rfi["closed_at"] is not None

    resolved = client.resolve_rfi_references(project_id, full_rfi)
    # Verified live against the real seeded RES instance, not assumed from
    # the illustrative Reference Trace: the seeded partial-scope credential
    # (rfis, submittals, documents) does NOT include "spec_sections" or
    # "locations" — RES's own ctx.can_see() returns [] for both, silently,
    # per docs/04's designed behavior for an under-provisioned credential.
    # "documents" IS granted, so drawing_refs resolves correctly. This is a
    # recorded, real deviation from the illustrative trace (which assumes
    # all three resolve for this exact credential) — see the Milestone 1
    # report's Known Limitations section.
    assert resolved.spec_section_numbers == []
    assert resolved.location_names == []
    assert ("M-2.1", "Rev C") in resolved.drawing_refs


def test_partial_scope_credential_cannot_see_locations_it_was_never_granted():
    """docs/04's highest-value real-world behavior: a partially-scoped
    credential silently returns incomplete data, never a 403. This
    connection IS granted 'documents' but the point stands for whatever
    it's genuinely NOT granted — verified here against vendors, which the
    seeded partial-scope IntegrationUser (rfis, submittals, documents) does
    not include."""
    partial_config = ConnectorConfiguration(
        connection_id="conn_res_meridian",
        project_id="proj_meridian_tower",
        source_system="procore",
        base_url=RES_BASE_URL,
        oauth_token_url=f"{RES_BASE_URL}/oauth/token",
        oauth_client_id="downstream-partial",
        oauth_client_secret="partial-scope-secret",
        granted_scope=["rfis", "submittals", "documents"],
        integration_tier="read_only",
        webhook_secret="seed-webhook-secret",
    )
    client = ResClient(partial_config)
    projects = httpx.get(
        f"{RES_BASE_URL}/rest/v1.0/projects", headers={"Authorization": f"Bearer {client._get_token()}"}
    ).json()
    project_id = projects[0]["id"]
    vendors = httpx.get(
        f"{RES_BASE_URL}/rest/v1.0/projects/{project_id}/vendors",
        headers={"Authorization": f"Bearer {client._get_token()}"},
    )
    assert vendors.status_code == 200
    assert vendors.json() == []
    assert vendors.headers["X-Total"] == "0"
