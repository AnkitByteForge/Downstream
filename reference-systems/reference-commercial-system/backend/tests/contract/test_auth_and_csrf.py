from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app
from infrastructure.persistence.db import SessionLocal
from infrastructure.persistence.orm_models import VendorModel


def _delete_vendor(vendor_id: int) -> None:
    session = SessionLocal()
    try:
        session.execute(VendorModel.__table__.delete().where(VendorModel.id == vendor_id))
        session.commit()
    finally:
        session.close()

# CSRF ceremony contract tests (docs/04, docs/05 Phase 12.2): a GET request
# carrying X-CSRF-Token: fetch must issue a token; any mutating request
# without a valid token must be rejected with 403 — exactly the "GET with
# X-CSRF-Token: fetch returns a token; any POST/PATCH/DELETE without it is
# rejected with 403" behavior the Reference Commercial System is built to
# reproduce honestly.


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_rest_endpoint_requires_auth(cs_contract_fixture):
    resp = TestClient(app).get("/rest/v1/vendors")
    assert resp.status_code == 401


def test_human_session_cookie_authenticates(cs_contract_fixture):
    client = TestClient(app)
    client.cookies.set("cs_session", cs_contract_fixture["human_cookie"])
    resp = client.get("/rest/v1/vendors")
    assert resp.status_code == 200


def test_bearer_token_authenticates(cs_contract_fixture):
    client = TestClient(app)
    resp = client.get("/rest/v1/vendors", headers=_bearer(cs_contract_fixture["token_full_a"]))
    assert resp.status_code == 200


def test_invalid_bearer_token_rejected(cs_contract_fixture):
    client = TestClient(app)
    resp = client.get("/rest/v1/vendors", headers=_bearer("not-a-real-token"))
    assert resp.status_code == 401


def test_create_vendor_without_csrf_token_is_rejected(cs_contract_fixture):
    client = TestClient(app)
    resp = client.post(
        "/rest/v1/vendors",
        json={"name": "Should Not Be Created"},
        headers=_bearer(cs_contract_fixture["token_full_a"]),
    )
    assert resp.status_code == 403


def test_get_with_fetch_header_issues_csrf_token(cs_contract_fixture):
    client = TestClient(app)
    resp = client.get(
        f"/rest/v1/purchase_orders/{cs_contract_fixture['po_a_number']}",
        headers={**_bearer(cs_contract_fixture["token_full_a"]), "X-CSRF-Token": "fetch"},
    )
    assert resp.status_code == 200
    assert "X-CSRF-Token" in resp.headers
    assert resp.headers["X-CSRF-Token"] != "fetch"


def test_write_with_valid_csrf_token_succeeds(cs_contract_fixture):
    client = TestClient(app)
    headers = _bearer(cs_contract_fixture["token_full_a"])
    fetch_resp = client.get(
        f"/rest/v1/purchase_orders/{cs_contract_fixture['po_a_number']}",
        headers={**headers, "X-CSRF-Token": "fetch"},
    )
    csrf_token = fetch_resp.headers["X-CSRF-Token"]

    resp = client.post(
        "/rest/v1/vendors",
        json={"name": "Created With Valid CSRF Token"},
        headers={**headers, "X-CSRF-Token": csrf_token},
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Created With Valid CSRF Token"
    _delete_vendor(resp.json()["id"])


def test_csrf_token_is_single_use(cs_contract_fixture):
    client = TestClient(app)
    headers = _bearer(cs_contract_fixture["token_full_a"])
    fetch_resp = client.get(
        f"/rest/v1/purchase_orders/{cs_contract_fixture['po_a_number']}",
        headers={**headers, "X-CSRF-Token": "fetch"},
    )
    csrf_token = fetch_resp.headers["X-CSRF-Token"]

    first = client.post(
        "/rest/v1/vendors", json={"name": "First Use"}, headers={**headers, "X-CSRF-Token": csrf_token}
    )
    assert first.status_code == 201
    _delete_vendor(first.json()["id"])

    second = client.post(
        "/rest/v1/vendors", json={"name": "Second Use"}, headers={**headers, "X-CSRF-Token": csrf_token}
    )
    assert second.status_code == 403


def test_csrf_token_is_bound_to_the_actor_that_fetched_it(cs_contract_fixture):
    """A token issued to one integration client cannot be spent by another
    actor — the ceremony authenticates the actor, not just possession of a
    string."""
    client = TestClient(app)
    fetch_resp = client.get(
        f"/rest/v1/purchase_orders/{cs_contract_fixture['po_a_number']}",
        headers={**_bearer(cs_contract_fixture["token_full_a"]), "X-CSRF-Token": "fetch"},
    )
    csrf_token = fetch_resp.headers["X-CSRF-Token"]

    resp = client.post(
        "/rest/v1/vendors",
        json={"name": "Should Not Be Created"},
        headers={**_bearer(cs_contract_fixture["token_full_b"]), "X-CSRF-Token": csrf_token},
    )
    assert resp.status_code == 403
