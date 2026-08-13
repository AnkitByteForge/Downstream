"""Contract test — runs against the REAL Reference Commercial System.
Skipped automatically if RCS isn't reachable; meant to run against the live
Docker Compose stack (infra/docker-compose.yml), not on a bare `pytest -q`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from seed_graph_commercial import authenticate, fetch_commercial_data, wait_for_rcs

RCS_BASE_URL = os.environ.get("RCS_BASE_URL", "http://localhost:8001")


def _rcs_reachable() -> bool:
    try:
        resp = httpx.get(f"{RCS_BASE_URL}/health", timeout=2.0)
        return resp.status_code == 200
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(
    not _rcs_reachable(), reason=f"Reference Commercial System not reachable at {RCS_BASE_URL}"
)


def test_wait_for_rcs_succeeds_against_live_health_endpoint():
    wait_for_rcs(RCS_BASE_URL, timeout_seconds=5)


def test_client_credentials_grant_against_real_rcs():
    token = authenticate(RCS_BASE_URL, "downstream-full-scope", "demo-client-secret")
    assert isinstance(token, str) and len(token) > 0


def test_fetch_commercial_data_finds_real_scenario_a():
    token = authenticate(RCS_BASE_URL, "downstream-full-scope", "demo-client-secret")
    data = fetch_commercial_data(RCS_BASE_URL, token)

    cost_codes = {cc["native_code"]: cc for cc in data["cost_codes"]}
    assert "23-100" in cost_codes
    assert cost_codes["23-100"]["standard_ref"] == "23 31 13"
    assert cost_codes["23-100"]["cost_code_format"] == "CSI_MASTERFORMAT"

    po_numbers = {po["po_number"] for po, _lines in data["pos_with_lines"]}
    assert "4500018823" in po_numbers  # po_4471
    assert None in po_numbers  # po_4488 — real, nullable po_number (ADR-017)

    po_4471_lines = next(lines for po, lines in data["pos_with_lines"] if po["po_number"] == "4500018823")
    assert len(po_4471_lines) == 1
    assert po_4471_lines[0]["cost_code_id"] == cost_codes["23-100"]["id"]
    assert po_4471_lines[0]["lifecycle_position"] == "in_fabrication"

    vendor_names = {v["name"] for v in data["vendor_by_id"].values()}
    assert "VendorCo Metals" in vendor_names


def test_org_scope_isolation_hides_scenario_b_from_the_scenario_a_client():
    """ADR-012, verified live: the seeded full-scope client is bound to
    company_code "1000" (Scenario A) — org-scope isolation still applies
    under "full" resource-type scope."""
    token = authenticate(RCS_BASE_URL, "downstream-full-scope", "demo-client-secret")
    data = fetch_commercial_data(RCS_BASE_URL, token)
    po_numbers = {po["po_number"] for po, _lines in data["pos_with_lines"]}
    assert "4500020045" not in po_numbers  # po_5201 (Scenario B, company_code "2000")
    assert "4500020091" not in po_numbers  # po_5202 (Scenario B)
