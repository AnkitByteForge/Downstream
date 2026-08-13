from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app

# Org-scope isolation contract tests (ADR-012/ADR-015): an integration
# client scoped to one company_code must never reach another company_code's
# PurchaseOrder — in a list or by direct number — even though both exist in
# the same database. A partially-scoped credential must silently omit
# resource types outside its scope (docs/04's real Procore/SAP behavior),
# never a 403.


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_full_scope_client_sees_only_its_own_company_code_in_list(cs_contract_fixture):
    client = TestClient(app)
    resp = client.get("/rest/v1/purchase_orders", headers=_bearer(cs_contract_fixture["token_full_a"]))
    assert resp.status_code == 200
    numbers = {po["po_number"] for po in resp.json()}
    assert cs_contract_fixture["po_a_number"] in numbers
    assert cs_contract_fixture["po_b_number"] not in numbers


def test_cross_company_code_get_by_number_is_404(cs_contract_fixture):
    """The company_code=1000 client can never fetch company_code=2000's
    PO, even knowing its exact po_number."""
    client = TestClient(app)
    resp = client.get(
        f"/rest/v1/purchase_orders/{cs_contract_fixture['po_b_number']}",
        headers=_bearer(cs_contract_fixture["token_full_a"]),
    )
    assert resp.status_code == 404


def test_own_company_code_get_by_number_succeeds(cs_contract_fixture):
    client = TestClient(app)
    resp = client.get(
        f"/rest/v1/purchase_orders/{cs_contract_fixture['po_a_number']}",
        headers=_bearer(cs_contract_fixture["token_full_a"]),
    )
    assert resp.status_code == 200
    assert resp.json()["org_scope"]["company_code"] == "1000"


def test_second_scope_client_sees_its_own_po_not_the_others(cs_contract_fixture):
    client = TestClient(app)
    resp = client.get(
        f"/rest/v1/purchase_orders/{cs_contract_fixture['po_b_number']}",
        headers=_bearer(cs_contract_fixture["token_full_b"]),
    )
    assert resp.status_code == 200

    cross = client.get(
        f"/rest/v1/purchase_orders/{cs_contract_fixture['po_a_number']}",
        headers=_bearer(cs_contract_fixture["token_full_b"]),
    )
    assert cross.status_code == 404


def test_human_session_sees_across_every_company_code(cs_contract_fixture):
    """Unlike integration clients, a human procurement manager's session is
    never company_code-scoped — real cross-plant oversight of one project."""
    client = TestClient(app)
    client.cookies.set("cs_session", cs_contract_fixture["human_cookie"])
    resp_a = client.get(f"/rest/v1/purchase_orders/{cs_contract_fixture['po_a_number']}")
    resp_b = client.get(f"/rest/v1/purchase_orders/{cs_contract_fixture['po_b_number']}")
    assert resp_a.status_code == 200
    assert resp_b.status_code == 200


def test_partial_scope_client_gets_empty_commitments_list(cs_contract_fixture):
    """docs/04: an under-scoped credential silently returns incomplete
    data, never a 403."""
    client = TestClient(app)
    resp = client.get("/rest/v1/commitments", headers=_bearer(cs_contract_fixture["token_partial_a"]))
    assert resp.status_code == 200
    assert resp.json() == []
    assert resp.headers["X-Total"] == "0"


def test_partial_scope_client_gets_404_on_direct_commitment_get(cs_contract_fixture):
    client = TestClient(app)
    resp = client.get(
        f"/rest/v1/commitments/{cs_contract_fixture['commitment_a_id']}",
        headers=_bearer(cs_contract_fixture["token_partial_a"]),
    )
    assert resp.status_code == 404


def test_partial_scope_client_can_still_see_its_granted_resource_type(cs_contract_fixture):
    client = TestClient(app)
    resp = client.get(
        f"/rest/v1/purchase_orders/{cs_contract_fixture['po_a_number']}",
        headers=_bearer(cs_contract_fixture["token_partial_a"]),
    )
    assert resp.status_code == 200
