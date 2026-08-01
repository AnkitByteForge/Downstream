from __future__ import annotations

from fastapi.testclient import TestClient

from api.deps import get_webhook_dispatcher
from api.main import app
from domain.entities import WebhookSubscription


class RecordingDispatcher:
    def __init__(self) -> None:
        self.calls: list[tuple[WebhookSubscription, dict]] = []

    def dispatch(self, subscription: WebhookSubscription, payload: dict) -> bool:
        self.calls.append((subscription, payload))
        return True


def _headers(fixture: dict) -> dict:
    return {"Authorization": f"Bearer {fixture['access_token']}"}


def test_disposition_dispatches_the_exact_thin_five_field_payload(submittal_contract_fixture):
    recorder = RecordingDispatcher()
    app.dependency_overrides[get_webhook_dispatcher] = lambda: recorder
    client = TestClient(app)
    try:
        response = client.patch(
            f"/rest/v1.0/projects/{submittal_contract_fixture['project_id']}"
            f"/submittals/{submittal_contract_fixture['submittal_id']}"
            f"/revisions/{submittal_contract_fixture['revision_id']}/disposition",
            json={"review_status_code": "NO_EXCEPTIONS_TAKEN", "disposed_by_user_id": submittal_contract_fixture["disposed_by_user_id"]},
            headers=_headers(submittal_contract_fixture),
        )
        assert response.status_code == 200

        assert len(recorder.calls) == 1
        subscription, payload = recorder.calls[0]
        assert subscription.id == submittal_contract_fixture["subscription_id"]
        assert set(payload.keys()) == {
            "resource_name",
            "resource_id",
            "project_id",
            "event_type",
            "timestamp",
        }
        assert payload["resource_name"] == "submittals"
        assert payload["resource_id"] == submittal_contract_fixture["submittal_id"]
        assert payload["event_type"] == "update"
    finally:
        app.dependency_overrides.pop(get_webhook_dispatcher, None)


def test_gating_disposition_reports_gates_procurement_true(submittal_contract_fixture):
    client = TestClient(app)
    response = client.patch(
        f"/rest/v1.0/projects/{submittal_contract_fixture['project_id']}"
        f"/submittals/{submittal_contract_fixture['submittal_id']}"
        f"/revisions/{submittal_contract_fixture['revision_id']}/disposition",
        json={"review_status_code": "NO_EXCEPTIONS_TAKEN", "disposed_by_user_id": submittal_contract_fixture["disposed_by_user_id"]},
        headers=_headers(submittal_contract_fixture),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["review_status_code"] == "NO_EXCEPTIONS_TAKEN"
    assert body["gates_procurement"] is True
    assert body["ball_in_court"] == "closed"


def test_blocking_disposition_reports_gates_procurement_false(submittal_contract_fixture):
    client = TestClient(app)
    response = client.patch(
        f"/rest/v1.0/projects/{submittal_contract_fixture['project_id']}"
        f"/submittals/{submittal_contract_fixture['submittal_id']}"
        f"/revisions/{submittal_contract_fixture['revision_id']}/disposition",
        json={"review_status_code": "REVISE_AND_RESUBMIT", "disposed_by_user_id": submittal_contract_fixture["disposed_by_user_id"]},
        headers=_headers(submittal_contract_fixture),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["review_status_code"] == "REVISE_AND_RESUBMIT"
    assert body["gates_procurement"] is False
    assert body["ball_in_court"] == "submitter"


def test_redisposing_an_already_terminal_revision_returns_409(submittal_contract_fixture):
    client = TestClient(app)
    headers = _headers(submittal_contract_fixture)
    path = (
        f"/rest/v1.0/projects/{submittal_contract_fixture['project_id']}"
        f"/submittals/{submittal_contract_fixture['submittal_id']}"
        f"/revisions/{submittal_contract_fixture['revision_id']}/disposition"
    )
    first = client.patch(path, json={"review_status_code": "NO_EXCEPTIONS_TAKEN", "disposed_by_user_id": submittal_contract_fixture["disposed_by_user_id"]}, headers=headers)
    assert first.status_code == 200
    second = client.patch(path, json={"review_status_code": "REVISE_AND_RESUBMIT", "disposed_by_user_id": submittal_contract_fixture["disposed_by_user_id"]}, headers=headers)
    assert second.status_code == 409


def test_submittals_list_paginates_with_x_total_header(submittal_contract_fixture):
    client = TestClient(app)
    response = client.get(
        f"/rest/v1.0/projects/{submittal_contract_fixture['project_id']}/submittals",
        headers=_headers(submittal_contract_fixture),
    )
    assert response.status_code == 200
    assert response.headers["X-Total"] == "1"
    assert len(response.json()) == 1
