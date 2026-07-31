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


def test_closing_an_rfi_dispatches_the_exact_thin_five_field_payload(contract_fixture):
    """The single most important behavior in docs/04's Mock Engineering
    System spec: the webhook fired on an RFI status change must carry
    exactly resource_name/resource_id/project_id/event_type/timestamp —
    nothing richer, forcing a real subscriber to GET back for detail,
    exactly like real Procore. This test fails loudly the moment anyone
    "helpfully" adds a field to the payload.
    """
    recorder = RecordingDispatcher()
    app.dependency_overrides[get_webhook_dispatcher] = lambda: recorder
    client = TestClient(app)
    try:
        response = client.patch(
            f"/rest/v1.0/projects/{contract_fixture['project_id']}/rfis/{contract_fixture['rfi_id']}/close",
            json={"response_text": "Contract test close."},
            headers={"Authorization": f"Bearer {contract_fixture['access_token']}"},
        )
        assert response.status_code == 200

        assert len(recorder.calls) == 1
        subscription, payload = recorder.calls[0]
        assert subscription.id == contract_fixture["subscription_id"]

        assert set(payload.keys()) == {
            "resource_name",
            "resource_id",
            "project_id",
            "event_type",
            "timestamp",
        }
        assert payload["resource_name"] == "rfis"
        assert payload["resource_id"] == contract_fixture["rfi_id"]
        assert payload["project_id"] == contract_fixture["project_id"]
        assert payload["event_type"] == "update"
        # No status, no response text, no drawing reference — thin means thin.
        assert "status" not in payload
        assert "response" not in payload
    finally:
        app.dependency_overrides.pop(get_webhook_dispatcher, None)
