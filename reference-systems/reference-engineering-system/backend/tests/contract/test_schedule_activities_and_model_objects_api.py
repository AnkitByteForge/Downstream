from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app

# ScheduleActivity / ModelObject contract tests (RES-5E): read-only surface
# exercised against the full app — real committed rows, real HTTP client.
# Covers auth, X-Total, contract-field shape, scoped-integration 404/empty
# semantics, and cross-project isolation, mirroring the DesignChange contract
# suite's coverage for a mutation-free surface (no issue/webhook/409 cases —
# neither entity has a lifecycle, ADR-008).


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- ScheduleActivity ---------------------------------------------------------

def test_schedule_activities_list_requires_auth(res5_contract_fixture):
    resp = TestClient(app).get(
        f"/rest/v1.0/projects/{res5_contract_fixture['project_a']}/schedule_activities"
    )
    assert resp.status_code == 401


def test_schedule_activities_list_returns_seeded_rows_with_x_total(res5_contract_fixture):
    client = TestClient(app)
    resp = client.get(
        f"/rest/v1.0/projects/{res5_contract_fixture['project_a']}/schedule_activities",
        headers=_headers(res5_contract_fixture["token_a_full"]),
    )
    assert resp.status_code == 200
    assert resp.headers["X-Total"] == "1"
    body = resp.json()
    assert body[0]["activity_code"] == "A-1"
    assert body[0]["type"] == "TASK"


def test_schedule_activities_get_returns_contract_fields(res5_contract_fixture):
    client = TestClient(app)
    resp = client.get(
        f"/rest/v1.0/projects/{res5_contract_fixture['project_a']}"
        f"/schedule_activities/{res5_contract_fixture['schedule_activity_a']}",
        headers=_headers(res5_contract_fixture["token_a_full"]),
    )
    assert resp.status_code == 200
    body = resp.json()
    for field in (
        "id",
        "project_id",
        "activity_code",
        "type",
        "wbs",
        "predecessor_ids",
        "successor_ids",
        "linked_submittal_ids",
        "delivery_milestone",
    ):
        assert field in body


def test_schedule_activities_list_under_scoped_integration_returns_empty(res5_contract_fixture):
    client = TestClient(app)
    resp = client.get(
        f"/rest/v1.0/projects/{res5_contract_fixture['project_a']}/schedule_activities",
        headers=_headers(res5_contract_fixture["token_a_partial"]),
    )
    assert resp.status_code == 200
    assert resp.headers["X-Total"] == "0"
    assert resp.json() == []


def test_schedule_activities_get_under_scoped_integration_is_404(res5_contract_fixture):
    client = TestClient(app)
    resp = client.get(
        f"/rest/v1.0/projects/{res5_contract_fixture['project_a']}"
        f"/schedule_activities/{res5_contract_fixture['schedule_activity_a']}",
        headers=_headers(res5_contract_fixture["token_a_partial"]),
    )
    assert resp.status_code == 404


def test_schedule_activities_cross_project_list_is_404(res5_contract_fixture):
    client = TestClient(app)
    resp = client.get(
        f"/rest/v1.0/projects/{res5_contract_fixture['project_b']}/schedule_activities",
        headers=_headers(res5_contract_fixture["token_a_full"]),
    )
    assert resp.status_code == 404


def test_schedule_activities_cross_project_get_is_404(res5_contract_fixture):
    client = TestClient(app)
    resp = client.get(
        f"/rest/v1.0/projects/{res5_contract_fixture['project_a']}"
        f"/schedule_activities/{res5_contract_fixture['schedule_activity_b']}",
        headers=_headers(res5_contract_fixture["token_a_full"]),
    )
    assert resp.status_code == 404


# --- ModelObject ----------------------------------------------------------------

def test_model_objects_list_requires_auth(res5_contract_fixture):
    resp = TestClient(app).get(
        f"/rest/v1.0/projects/{res5_contract_fixture['project_a']}/model_objects"
    )
    assert resp.status_code == 401


def test_model_objects_list_returns_seeded_rows_with_x_total(res5_contract_fixture):
    client = TestClient(app)
    resp = client.get(
        f"/rest/v1.0/projects/{res5_contract_fixture['project_a']}/model_objects",
        headers=_headers(res5_contract_fixture["token_a_full"]),
    )
    assert resp.status_code == 200
    assert resp.headers["X-Total"] == "1"
    body = resp.json()
    assert body[0]["discipline_code"] == "E"
    assert body[0]["appearance_profile"] == "INSTALL"
    assert body[0]["resource_link_id"] == res5_contract_fixture["schedule_activity_a"]


def test_model_objects_get_returns_contract_fields(res5_contract_fixture):
    client = TestClient(app)
    resp = client.get(
        f"/rest/v1.0/projects/{res5_contract_fixture['project_a']}"
        f"/model_objects/{res5_contract_fixture['model_object_a']}",
        headers=_headers(res5_contract_fixture["token_a_full"]),
    )
    assert resp.status_code == 200
    body = resp.json()
    for field in (
        "id",
        "project_id",
        "discipline_code",
        "appearance_profile",
        "location_id",
        "resource_link_id",
    ):
        assert field in body


def test_model_objects_list_under_scoped_integration_returns_empty(res5_contract_fixture):
    client = TestClient(app)
    resp = client.get(
        f"/rest/v1.0/projects/{res5_contract_fixture['project_a']}/model_objects",
        headers=_headers(res5_contract_fixture["token_a_partial"]),
    )
    assert resp.status_code == 200
    assert resp.headers["X-Total"] == "0"
    assert resp.json() == []


def test_model_objects_cross_project_get_is_404(res5_contract_fixture):
    client = TestClient(app)
    resp = client.get(
        f"/rest/v1.0/projects/{res5_contract_fixture['project_a']}"
        f"/model_objects/{res5_contract_fixture['model_object_b']}",
        headers=_headers(res5_contract_fixture["token_a_full"]),
    )
    assert resp.status_code == 404


def test_model_objects_cross_project_list_is_404(res5_contract_fixture):
    client = TestClient(app)
    resp = client.get(
        f"/rest/v1.0/projects/{res5_contract_fixture['project_b']}/model_objects",
        headers=_headers(res5_contract_fixture["token_a_full"]),
    )
    assert resp.status_code == 404
