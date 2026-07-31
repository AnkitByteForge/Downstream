from __future__ import annotations

from fastapi.testclient import TestClient

from api.deps import get_settings
from api.main import app
from infrastructure.config import settings


def _tiny_budget_settings():
    return settings.model_copy(update={"rate_limit_max_requests": 2, "rate_limit_window_seconds": 3600})


def test_exceeding_the_per_client_budget_returns_429_with_retry_after(contract_fixture):
    """docs/04: 'a configurable per-client_id request budget returning 429 +
    Retry-After once exceeded' — exercised against the real app, not just
    the store in isolation."""
    app.dependency_overrides[get_settings] = _tiny_budget_settings
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {contract_fixture['access_token']}"}
    path = f"/rest/v1.0/projects/{contract_fixture['project_id']}/rfis"
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


def test_human_sessions_are_never_rate_limited(contract_fixture):
    """Rate limiting is scoped to OAuth2 client_id traffic per docs/04 — a
    request with no bearer token (and no session cookie either, in this
    test) simply hits normal auth handling, never a 429."""
    app.dependency_overrides[get_settings] = _tiny_budget_settings
    client = TestClient(app)
    path = f"/rest/v1.0/projects/{contract_fixture['project_id']}/rfis"
    try:
        responses = [client.get(path) for _ in range(4)]
        assert all(r.status_code == 401 for r in responses)  # no credentials at all — never 429
    finally:
        app.dependency_overrides.pop(get_settings, None)
