from __future__ import annotations

from fastapi.testclient import TestClient

from api.deps import get_settings, get_webhook_dispatcher
from api.main import app
from domain.entities import WebhookSubscription
from infrastructure.config import settings
from infrastructure.persistence.db import SessionLocal
from infrastructure.persistence.repositories.sqlalchemy_webhook_repository import (
    SqlAlchemyWebhookDeliveryRepository,
)

# DesignChange contract tests (RES-4D): the design_changes REST surface
# exercised against the full app — real committed rows, real HTTP client.
# Covers ordering/pagination+X-Total, cross-project isolation, scope
# enforcement, the issue transition, rate limiting, and the thin webhook +
# WebhookDelivery record on issue.


class RecordingDispatcher:
    def __init__(self) -> None:
        self.calls: list[tuple[WebhookSubscription, dict]] = []

    def dispatch(self, subscription: WebhookSubscription, payload: dict) -> bool:
        self.calls.append((subscription, payload))
        return True


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- Authenticated list + pagination -----------------------------------------

def test_design_changes_list_requires_auth(design_change_contract_fixture):
    resp = TestClient(app).get(
        f"/rest/v1.0/projects/{design_change_contract_fixture['project_a']}/design_changes"
    )
    assert resp.status_code == 401


def test_design_changes_list_returns_seeded_rows_with_x_total(
    design_change_contract_fixture,
):
    client = TestClient(app)
    resp = client.get(
        f"/rest/v1.0/projects/{design_change_contract_fixture['project_a']}/design_changes",
        headers=_headers(design_change_contract_fixture["token_a_full"]),
    )
    assert resp.status_code == 200
    assert resp.headers["X-Total"] == "1"
    body = resp.json()
    assert len(body) == 1
    assert body[0]["display_number"] == "ASI-1"
    assert body[0]["type"] == "ASI"
    assert body[0]["status"] == "DRAFT"
    assert body[0]["source_rfi_id"] == design_change_contract_fixture["rfi_a"]


def test_design_changes_list_paginates_with_per_page(
    design_change_contract_fixture,
):
    client = TestClient(app)
    resp = client.get(
        f"/rest/v1.0/projects/{design_change_contract_fixture['project_a']}/design_changes?per_page=0",
        headers=_headers(design_change_contract_fixture["token_a_full"]),
    )
    assert resp.status_code == 422  # per_page floor is 1


def test_design_changes_get_returns_contract_fields(design_change_contract_fixture):
    client = TestClient(app)
    resp = client.get(
        f"/rest/v1.0/projects/{design_change_contract_fixture['project_a']}"
        f"/design_changes/{design_change_contract_fixture['design_change_a']}",
        headers=_headers(design_change_contract_fixture["token_a_full"]),
    )
    assert resp.status_code == 200
    body = resp.json()
    for field in (
        "id",
        "project_id",
        "number",
        "display_number",
        "type",
        "status",
        "change_reason",
        "discipline_code",
        "source_rfi_id",
        "ball_in_court",
        "affected_drawing_version_ids",
        "affected_spec_section_ids",
        "location_ids",
        "superseded_by_id",
        "issued_at",
        "acknowledged_at",
        "voided_at",
    ):
        assert field in body


# --- Scope enforcement --------------------------------------------------------

def test_design_changes_list_under_scoped_integration_returns_empty(
    design_change_contract_fixture,
):
    """A client scoped to rfis only (no design_changes) gets a silently empty
    list, not an error — docs/04's partial-scope posture."""
    client = TestClient(app)
    resp = client.get(
        f"/rest/v1.0/projects/{design_change_contract_fixture['project_a']}/design_changes",
        headers=_headers(design_change_contract_fixture["token_a_partial"]),
    )
    assert resp.status_code == 200
    assert resp.headers["X-Total"] == "0"
    assert resp.json() == []


def test_design_changes_get_under_scoped_integration_is_404(
    design_change_contract_fixture,
):
    client = TestClient(app)
    resp = client.get(
        f"/rest/v1.0/projects/{design_change_contract_fixture['project_a']}"
        f"/design_changes/{design_change_contract_fixture['design_change_a']}",
        headers=_headers(design_change_contract_fixture["token_a_partial"]),
    )
    assert resp.status_code == 404


def test_design_changes_issue_under_scoped_integration_is_404(
    design_change_contract_fixture,
):
    client = TestClient(app)
    resp = client.patch(
        f"/rest/v1.0/projects/{design_change_contract_fixture['project_a']}"
        f"/design_changes/{design_change_contract_fixture['design_change_a']}/issue",
        headers=_headers(design_change_contract_fixture["token_a_partial"]),
    )
    assert resp.status_code == 404


# --- Project isolation --------------------------------------------------------

def test_design_changes_cross_project_list_is_404(design_change_contract_fixture):
    client = TestClient(app)
    resp = client.get(
        f"/rest/v1.0/projects/{design_change_contract_fixture['project_b']}/design_changes",
        headers=_headers(design_change_contract_fixture["token_a_full"]),
    )
    assert resp.status_code == 404


def test_design_changes_resource_project_mismatch_is_404(
    design_change_contract_fixture,
):
    """A project A client must not reach project B's design change by id
    through a project A path — the fetched resource's project is verified."""
    client = TestClient(app)
    resp = client.get(
        f"/rest/v1.0/projects/{design_change_contract_fixture['project_a']}"
        f"/design_changes/{design_change_contract_fixture['design_change_b']}",
        headers=_headers(design_change_contract_fixture["token_a_full"]),
    )
    assert resp.status_code == 404


def test_design_changes_cross_project_get_is_404(design_change_contract_fixture):
    """A project B client can see its own change; a project A client asking for
    project B's change through project B's own path is still 404."""
    client = TestClient(app)
    resp = client.get(
        f"/rest/v1.0/projects/{design_change_contract_fixture['project_b']}"
        f"/design_changes/{design_change_contract_fixture['design_change_b']}",
        headers=_headers(design_change_contract_fixture["token_a_full"]),
    )
    assert resp.status_code == 404


def test_design_changes_same_project_isolated_projects_both_visible(
    design_change_contract_fixture,
):
    """Proof of non-collision: project A's token sees only A's change, and
    project B's token sees only B's change, despite both existing."""
    client = TestClient(app)
    list_a = client.get(
        f"/rest/v1.0/projects/{design_change_contract_fixture['project_a']}/design_changes",
        headers=_headers(design_change_contract_fixture["token_a_full"]),
    )
    assert [c["display_number"] for c in list_a.json()] == ["ASI-1"]
    list_b = client.get(
        f"/rest/v1.0/projects/{design_change_contract_fixture['project_b']}/design_changes",
        headers=_headers(design_change_contract_fixture["token_b"]),
    )
    assert list_b.status_code == 200, list_b.text
    assert [c["display_number"] for c in list_b.json()] == ["CCD-2"]


# --- Issue transition + thin webhook + WebhookDelivery -----------------------

def test_issue_design_change_transitions_and_dispatches_thin_webhook(
    design_change_contract_fixture,
):
    recorder = RecordingDispatcher()
    app.dependency_overrides[get_webhook_dispatcher] = lambda: recorder
    client = TestClient(app)
    try:
        resp = client.patch(
            f"/rest/v1.0/projects/{design_change_contract_fixture['project_a']}"
            f"/design_changes/{design_change_contract_fixture['design_change_a']}/issue",
            headers=_headers(design_change_contract_fixture["token_a_full"]),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ISSUED"
        assert body["issued_at"] is not None

        assert len(recorder.calls) == 1
        subscription, payload = recorder.calls[0]
        assert subscription.id == design_change_contract_fixture["subscription_a_id"]
        assert set(payload.keys()) == {
            "resource_name",
            "resource_id",
            "project_id",
            "event_type",
            "timestamp",
        }
        assert payload["resource_name"] == "design_changes"
        assert payload["resource_id"] == design_change_contract_fixture["design_change_a"]
        assert payload["project_id"] == design_change_contract_fixture["project_a"]
        assert payload["event_type"] == "update"
    finally:
        app.dependency_overrides.pop(get_webhook_dispatcher, None)


def test_issue_design_change_records_a_webhook_delivery(
    design_change_contract_fixture,
):
    """The issue step records a WebhookDelivery row regardless of delivery
    outcome — the append-only activity stream should show the SENT delivery."""
    recorder = RecordingDispatcher()
    app.dependency_overrides[get_webhook_dispatcher] = lambda: recorder
    client = TestClient(app)
    session = SessionLocal()
    delivery_repo = SqlAlchemyWebhookDeliveryRepository(session)
    try:
        resp = client.patch(
            f"/rest/v1.0/projects/{design_change_contract_fixture['project_a']}"
            f"/design_changes/{design_change_contract_fixture['design_change_a']}/issue",
            headers=_headers(design_change_contract_fixture["token_a_full"]),
        )
        assert resp.status_code == 200

        deliveries = delivery_repo.list_by_project(
            design_change_contract_fixture["project_a"], limit=10
        )
        matching = [
            d
            for d in deliveries
            if d.resource_name == "design_changes"
            and d.resource_id == design_change_contract_fixture["design_change_a"]
            and d.event_type == "update"
        ]
        assert len(matching) == 1
        assert matching[0].status == "SENT"
        assert matching[0].subscription_id == design_change_contract_fixture["subscription_a_id"]
    finally:
        app.dependency_overrides.pop(get_webhook_dispatcher, None)
        session.close()


def test_issue_already_issued_design_change_returns_409(
    design_change_contract_fixture,
):
    client = TestClient(app)
    headers = _headers(design_change_contract_fixture["token_a_full"])
    path = (
        f"/rest/v1.0/projects/{design_change_contract_fixture['project_a']}"
        f"/design_changes/{design_change_contract_fixture['design_change_a']}/issue"
    )
    first = client.patch(path, headers=headers)
    assert first.status_code == 200
    second = client.patch(path, headers=headers)
    assert second.status_code == 409


# --- Rate limiting ------------------------------------------------------------

def _tiny_budget_settings():
    return settings.model_copy(
        update={"rate_limit_max_requests": 2, "rate_limit_window_seconds": 3600}
    )


def test_design_changes_list_rate_limited_per_client_id(
    design_change_contract_fixture,
):
    app.dependency_overrides[get_settings] = _tiny_budget_settings
    client = TestClient(app)
    headers = _headers(design_change_contract_fixture["token_a_full"])
    path = (
        f"/rest/v1.0/projects/{design_change_contract_fixture['project_a']}"
        "/design_changes"
    )
    try:
        first = client.get(path, headers=headers)
        second = client.get(path, headers=headers)
        third = client.get(path, headers=headers)

        assert first.status_code == 200
        assert second.status_code == 200
        assert third.status_code == 429
        assert "Retry-After" in third.headers
        assert int(third.headers["Retry-After"]) > 0
    finally:
        app.dependency_overrides.pop(get_settings, None)