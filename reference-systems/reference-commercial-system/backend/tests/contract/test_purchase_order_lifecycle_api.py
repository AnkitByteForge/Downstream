from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _csrf_token(client: TestClient, po_number: str, headers: dict) -> str:
    resp = client.get(f"/rest/v1/purchase_orders/{po_number}", headers={**headers, "X-CSRF-Token": "fetch"})
    return resp.headers["X-CSRF-Token"]


def _patch(client: TestClient, path: str, headers: dict, csrf_token: str):
    return client.patch(path, headers={**headers, "X-CSRF-Token": csrf_token})


def test_purchase_order_full_header_lifecycle_via_api(cs_contract_fixture):
    """DRAFT -> PENDING_APPROVAL -> OPEN -> acknowledged, driven entirely
    through the REST surface, each write CSRF-protected."""
    client = TestClient(app)
    headers = _bearer(cs_contract_fixture["token_full_a"])
    po_number = cs_contract_fixture["po_a_number"]

    get_resp = client.get(f"/rest/v1/purchase_orders/{po_number}", headers=headers)
    assert get_resp.json()["status"] == "DRAFT"

    token1 = _csrf_token(client, po_number, headers)
    submit = _patch(client, f"/rest/v1/purchase_orders/{po_number}/submit", headers, token1)
    assert submit.status_code == 200
    assert submit.json()["status"] == "PENDING_APPROVAL"

    token2 = _csrf_token(client, po_number, headers)
    approve = _patch(client, f"/rest/v1/purchase_orders/{po_number}/approve", headers, token2)
    assert approve.status_code == 200
    assert approve.json()["status"] == "OPEN"

    token3 = _csrf_token(client, po_number, headers)
    ack = _patch(client, f"/rest/v1/purchase_orders/{po_number}/acknowledge", headers, token3)
    assert ack.status_code == 200
    assert ack.json()["acknowledged"] is True


def test_illegal_transition_returns_409(cs_contract_fixture):
    """approve before submit must fail — DRAFT -> OPEN directly is not a
    legal transition (domain state machine enforced through the API)."""
    client = TestClient(app)
    headers = _bearer(cs_contract_fixture["token_full_a"])
    po_number = cs_contract_fixture["po_a_number"]

    token = _csrf_token(client, po_number, headers)
    resp = _patch(client, f"/rest/v1/purchase_orders/{po_number}/approve", headers, token)
    assert resp.status_code == 409


def test_transition_on_unknown_po_number_is_404(cs_contract_fixture):
    client = TestClient(app)
    headers = _bearer(cs_contract_fixture["token_full_a"])
    token = _csrf_token(client, cs_contract_fixture["po_a_number"], headers)
    resp = _patch(client, "/rest/v1/purchase_orders/does-not-exist/submit", headers, token)
    assert resp.status_code == 404


def test_po_line_fabrication_lifecycle_via_api(cs_contract_fixture):
    client = TestClient(app)
    headers = _bearer(cs_contract_fixture["token_full_a"])
    po_number = cs_contract_fixture["po_a_number"]

    get_resp = client.get(f"/rest/v1/purchase_orders/{po_number}/lines/1", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["lifecycle_position"] == "draft"

    token1 = _csrf_token(client, po_number, headers)
    issue = _patch(client, f"/rest/v1/purchase_orders/{po_number}/lines/1/issue", headers, token1)
    assert issue.status_code == 200
    assert issue.json()["lifecycle_position"] == "issued"

    token2 = _csrf_token(client, po_number, headers)
    fab = _patch(client, f"/rest/v1/purchase_orders/{po_number}/lines/1/start_fabrication", headers, token2)
    assert fab.status_code == 200
    assert fab.json()["lifecycle_position"] == "in_fabrication"


def test_po_line_cannot_skip_stage_via_api(cs_contract_fixture):
    client = TestClient(app)
    headers = _bearer(cs_contract_fixture["token_full_a"])
    po_number = cs_contract_fixture["po_a_number"]

    token = _csrf_token(client, po_number, headers)
    resp = _patch(client, f"/rest/v1/purchase_orders/{po_number}/lines/1/start_fabrication", headers, token)
    assert resp.status_code == 409


def test_unknown_line_no_is_404(cs_contract_fixture):
    client = TestClient(app)
    headers = _bearer(cs_contract_fixture["token_full_a"])
    resp = client.get(f"/rest/v1/purchase_orders/{cs_contract_fixture['po_a_number']}/lines/999", headers=headers)
    assert resp.status_code == 404


def test_purchase_orders_list_has_x_total_header(cs_contract_fixture):
    client = TestClient(app)
    resp = client.get("/rest/v1/purchase_orders", headers=_bearer(cs_contract_fixture["token_full_a"]))
    assert resp.status_code == 200
    assert "X-Total" in resp.headers
    assert int(resp.headers["X-Total"]) >= 1


def test_purchase_orders_pagination_per_page_floor(cs_contract_fixture):
    client = TestClient(app)
    resp = client.get(
        "/rest/v1/purchase_orders?per_page=0", headers=_bearer(cs_contract_fixture["token_full_a"])
    )
    assert resp.status_code == 422


def test_purchase_orders_changed_since_filter_excludes_untouched_pos(cs_contract_fixture):
    """docs/04's polling-fallback pattern: a PO that has never transitioned
    carries no changed_at and must not appear in a changed_since query."""
    client = TestClient(app)
    headers = _bearer(cs_contract_fixture["token_full_a"])
    resp = client.get("/rest/v1/purchase_orders?changed_since=2026-01-01T00:00:00Z", headers=headers)
    assert resp.status_code == 200
    numbers = {po["po_number"] for po in resp.json()}
    assert cs_contract_fixture["po_a_number"] not in numbers  # never transitioned, changed_at is null
