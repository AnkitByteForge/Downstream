from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app


def test_rfi_list_returns_x_total_header(contract_fixture):
    client = TestClient(app)
    response = client.get(
        f"/rest/v1.0/projects/{contract_fixture['project_id']}/rfis",
        headers={"Authorization": f"Bearer {contract_fixture['access_token']}"},
    )
    assert response.status_code == 200
    assert response.headers["X-Total"] == "1"
    assert len(response.json()) == 1


def test_rfi_list_respects_per_page(contract_fixture):
    client = TestClient(app)
    response = client.get(
        f"/rest/v1.0/projects/{contract_fixture['project_id']}/rfis?per_page=0",
        headers={"Authorization": f"Bearer {contract_fixture['access_token']}"},
    )
    # per_page has a floor of 1 (ge=1) — 0 is rejected as invalid input, not silently clamped.
    assert response.status_code == 422


def test_rfi_list_page_beyond_range_returns_empty_with_accurate_total(contract_fixture):
    client = TestClient(app)
    response = client.get(
        f"/rest/v1.0/projects/{contract_fixture['project_id']}/rfis?page=99",
        headers={"Authorization": f"Bearer {contract_fixture['access_token']}"},
    )
    assert response.status_code == 200
    assert response.json() == []
    assert response.headers["X-Total"] == "1"
