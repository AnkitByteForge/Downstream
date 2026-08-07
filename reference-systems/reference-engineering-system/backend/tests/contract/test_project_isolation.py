from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from api.main import app
from application.ports import SessionClaims
from domain.entities import (
    Discipline,
    IntegrationUser,
    OAuthClient,
    OAuthToken,
    Project,
    RFI,
    User,
    WebhookDelivery,
    WebhookSubscription,
)
from domain.value_objects import BallInCourt, PermissionScope
from infrastructure.auth.jwt_service import JwtSessionTokenService
from infrastructure.auth.password_hashing import Pbkdf2PasswordHasher
from infrastructure.config import settings
from infrastructure.persistence.db import SessionLocal
from infrastructure.persistence.orm_models import (
    DisciplineModel,
    IntegrationUserModel,
    OAuthClientModel,
    OAuthTokenModel,
    ProjectModel,
    RateLimitStateModel,
    RFIModel,
    UserModel,
    WebhookDeliveryModel,
    WebhookSubscriptionModel,
)
from infrastructure.persistence.repositories.sqlalchemy_project_repository import (
    SqlAlchemyDisciplineRepository,
    SqlAlchemyProjectRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_rfi_repository import SqlAlchemyRFIRepository
from infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SqlAlchemyIntegrationUserRepository,
    SqlAlchemyOAuthClientRepository,
    SqlAlchemyOAuthTokenRepository,
    SqlAlchemyUserRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_webhook_repository import (
    SqlAlchemyWebhookDeliveryRepository,
    SqlAlchemyWebhookSubscriptionRepository,
)

HASHER = Pbkdf2PasswordHasher()


def _integration_credential(integration_repo, client_repo, token_repo, project, name, scope, client_key):
    integration_user = integration_repo.add(
        IntegrationUser(id=None, project_id=project.id, name=name, permission_scope=scope)
    )
    client = client_repo.add(
        OAuthClient(
            client_id=client_key,
            client_secret_hash=HASHER.hash("isolation-secret"),
            integration_user_id=integration_user.id,
        )
    )
    token = token_repo.add(
        OAuthToken(
            access_token=f"{client_key}-access",
            refresh_token=f"{client_key}-refresh",
            client_id=client.client_id,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
    )
    return {"integration_user_id": integration_user.id, "client": client, "token": token}


@pytest.fixture()
def isolation_fixture():
    """Two fully isolated real projects with RFIs, plus both auth surfaces.

    project A owns: RFI A, a full-scope integration client, a partial-scope
    client (no 'activity' visibility), and a human user. project B owns: RFI B
    and a full-scope integration client. Teardown deletes everything created.
    """
    session = SessionLocal()
    hasher = Pbkdf2PasswordHasher()
    grade = {"tokens": [], "clients": [], "integration_users": []}
    project_a = project_b = rfi_a = rfi_b = human = None
    try:
        discipline_repo = SqlAlchemyDisciplineRepository(session)
        project_repo = SqlAlchemyProjectRepository(session)
        rfi_repo = SqlAlchemyRFIRepository(session)
        integration_repo = SqlAlchemyIntegrationUserRepository(session)
        client_repo = SqlAlchemyOAuthClientRepository(session)
        token_repo = SqlAlchemyOAuthTokenRepository(session)
        user_repo = SqlAlchemyUserRepository(session)
        subscription_repo = SqlAlchemyWebhookSubscriptionRepository(session)
        delivery_repo = SqlAlchemyWebhookDeliveryRepository(session)

        discipline_a = discipline_repo.add(Discipline(code="PIA", name="Isolation Test A"))
        discipline_b = discipline_repo.add(Discipline(code="PIB", name="Isolation Test B"))

        project_a = project_repo.add(
            Project(id=None, name="Isolation Project A", spec_format="MF2020")
        )
        project_b = project_repo.add(
            Project(id=None, name="Isolation Project B", spec_format="MF2020")
        )

        rfi_a = rfi_repo.add(
            RFI(
                id=None,
                project_id=project_a.id,
                number="1",
                display_number="RFI-A1",
                subject="Isolation test RFI A",
                ball_in_court=BallInCourt("assignee", None),
                status="OPEN",
                discipline_code=discipline_a.code,
            )
        )
        rfi_b = rfi_repo.add(
            RFI(
                id=None,
                project_id=project_b.id,
                number="1",
                display_number="RFI-B1",
                subject="Isolation test RFI B",
                ball_in_court=BallInCourt("assignee", None),
                status="OPEN",
                discipline_code=discipline_b.code,
            )
        )

        # Full-scope integration credential on each project.
        cred_a = _integration_credential(
            integration_repo, client_repo, token_repo, project_a, "Iso Client A",
            PermissionScope.full(), "iso-client-a",
        )
        cred_b = _integration_credential(
            integration_repo, client_repo, token_repo, project_b, "Iso Client B",
            PermissionScope.full(), "iso-client-b",
        )
        # Partial-scope credential on project A WITHOUT activity visibility.
        cred_a_partial = _integration_credential(
            integration_repo, client_repo, token_repo, project_a, "Iso Client A partial",
            PermissionScope.partial("rfis"), "iso-client-a-partial",
        )
        for c in (cred_a, cred_b, cred_a_partial):
            grade["tokens"].append(c["token"])
            grade["clients"].append(c["client"])
            grade["integration_users"].append(c["integration_user_id"])

        # Human user on project A.
        human = user_repo.add(
            User(
                id=None,
                project_id=project_a.id,
                name="Iso Human A",
                email="iso-human-a@example.test",
                role="ADMIN",
                password_hash=hasher.hash("unused"),
            )
        )
        session_tokens = JwtSessionTokenService(settings)
        human_cookie = session_tokens.issue(
            SessionClaims(user_id=human.id, project_id=project_a.id, role="ADMIN")
        )

        # Webhook subscription + delivery on project A so the activity success
        # path has real content.
        subscription_a = subscription_repo.add(
            WebhookSubscription(
                id=None,
                project_id=project_a.id,
                resource_name="rfis",
                event_type="update",
                target_url="http://127.0.0.1:9/unreachable",
                secret="isolation-secret",
            )
        )
        delivery_a = delivery_repo.add(
            WebhookDelivery(
                id=None,
                project_id=project_a.id,
                subscription_id=subscription_a.id,
                resource_name="rfis",
                resource_id=rfi_a.id,
                event_type="update",
                occurred_at=datetime(2026, 7, 28, 9, 14, 3, tzinfo=timezone.utc),
                status="SENT",
                dispatched_at=datetime(2026, 7, 28, 9, 14, 3, tzinfo=timezone.utc),
            )
        )

        session.commit()

        yield {
            "project_a": project_a.id,
            "project_b": project_b.id,
            "rfi_a": rfi_a.id,
            "rfi_b": rfi_b.id,
            "token_a": cred_a["token"].access_token,
            "token_b": cred_b["token"].access_token,
            "token_a_partial": cred_a_partial["token"].access_token,
            "human_cookie": human_cookie,
            "human_id": human.id,
            "delivery_a": delivery_a.id,
            "_subscription_a": subscription_a.id,
        }
    finally:
        if project_a is not None and project_b is not None:
            for tok in grade["tokens"]:
                session.execute(
                    RateLimitStateModel.__table__.delete().where(
                        RateLimitStateModel.client_id == tok.client_id
                    )
                )
            session.execute(
                WebhookDeliveryModel.__table__.delete().where(
                    WebhookDeliveryModel.project_id.in_([project_a.id, project_b.id])
                )
            )
            for tok in grade["tokens"]:
                session.execute(
                    OAuthTokenModel.__table__.delete().where(
                        OAuthTokenModel.client_id == tok.client_id
                    )
                )
            for client in grade["clients"]:
                session.execute(
                    OAuthClientModel.__table__.delete().where(
                        OAuthClientModel.client_id == client.client_id
                    )
                )
            for iu_id in grade["integration_users"]:
                session.execute(
                    IntegrationUserModel.__table__.delete().where(IntegrationUserModel.id == iu_id)
                )
            session.execute(
                WebhookSubscriptionModel.__table__.delete().where(
                    WebhookSubscriptionModel.project_id == project_a.id
                )
            )
            if human is not None:
                session.execute(UserModel.__table__.delete().where(UserModel.id == human.id))
            session.execute(
                RFIModel.__table__.delete().where(
                    RFIModel.project_id.in_([project_a.id, project_b.id])
                )
            )
            session.execute(
                ProjectModel.__table__.delete().where(
                    ProjectModel.id.in_([project_a.id, project_b.id])
                )
            )
            session.execute(
                DisciplineModel.__table__.delete().where(
                    DisciplineModel.code.in_(["PIA", "PIB"])
                )
            )
            session.commit()
        session.close()

# --- Cross-project reads fail for BOTH auth surfaces -------------------------

def test_integration_cross_project_get_rfi_is_404(isolation_fixture):
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {isolation_fixture['token_a']}"}
    # Project A client asks for project B's RFI through project B's path.
    resp = client.get(
        f"/rest/v1.0/projects/{isolation_fixture['project_b']}/rfis/{isolation_fixture['rfi_b']}",
        headers=headers,
    )
    assert resp.status_code == 404


def test_human_cross_project_get_rfi_is_404(isolation_fixture):
    client = TestClient(app)
    client.cookies.set("res_session", isolation_fixture["human_cookie"])
    resp = client.get(
        f"/rest/v1.0/projects/{isolation_fixture['project_b']}/rfis/{isolation_fixture['rfi_b']}"
    )
    assert resp.status_code == 404


def test_integration_cross_project_list_rfis_is_404(isolation_fixture):
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {isolation_fixture['token_a']}"}
    resp = client.get(f"/rest/v1.0/projects/{isolation_fixture['project_b']}/rfis", headers=headers)
    assert resp.status_code == 404


def test_human_same_project_get_rfi_succeeds(isolation_fixture):
    client = TestClient(app)
    client.cookies.set("res_session", isolation_fixture["human_cookie"])
    resp = client.get(
        f"/rest/v1.0/projects/{isolation_fixture['project_a']}/rfis/{isolation_fixture['rfi_a']}"
    )
    assert resp.status_code == 200
    assert resp.json()["display_number"] == "RFI-A1"


# --- Resource-project mismatch via the caller's OWN project path -------------

def test_resource_project_mismatch_get_rfi_is_404(isolation_fixture):
    """A project A client must not reach project B's RFI by id through a
    project A path — the fetched resource's project is verified."""
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {isolation_fixture['token_a']}"}
    resp = client.get(
        f"/rest/v1.0/projects/{isolation_fixture['project_a']}/rfis/{isolation_fixture['rfi_b']}",
        headers=headers,
    )
    assert resp.status_code == 404


def test_cross_project_mutation_respond_is_404(isolation_fixture):
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {isolation_fixture['token_a']}"}
    resp = client.patch(
        f"/rest/v1.0/projects/{isolation_fixture['project_b']}/rfis/{isolation_fixture['rfi_b']}/respond",
        json={"response_text": "nope", "manager_user_id": isolation_fixture["human_id"]},
        headers=headers,
    )
    assert resp.status_code == 404


# --- Project catalog ---------------------------------------------------------

def test_list_projects_requires_auth(isolation_fixture):
    resp = TestClient(app).get("/rest/v1.0/projects")
    assert resp.status_code == 401


def test_list_projects_only_exposes_own_project_for_integration(isolation_fixture):
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {isolation_fixture['token_a']}"}
    resp = client.get("/rest/v1.0/projects", headers=headers)
    assert resp.status_code == 200
    names = [p["name"] for p in resp.json()]
    assert names == ["Isolation Project A"]


def test_get_project_cross_project_is_404(isolation_fixture):
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {isolation_fixture['token_a']}"}
    resp = client.get(f"/rest/v1.0/projects/{isolation_fixture['project_b']}", headers=headers)
    assert resp.status_code == 404

# --- Activity feed auth -----------------------------------------------------

def test_activity_requires_auth(isolation_fixture):
    resp = TestClient(app).get(f"/rest/v1.0/projects/{isolation_fixture['project_a']}/activity")
    assert resp.status_code == 401


def test_activity_same_project_full_scope_succeeds(isolation_fixture):
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {isolation_fixture['token_a']}"}
    resp = client.get(
        f"/rest/v1.0/projects/{isolation_fixture['project_a']}/activity", headers=headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert any(entry["resource_name"] == "rfis" for entry in body)


def test_activity_cross_project_is_404(isolation_fixture):
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {isolation_fixture['token_a']}"}
    resp = client.get(
        f"/rest/v1.0/projects/{isolation_fixture['project_b']}/activity", headers=headers
    )
    assert resp.status_code == 404


def test_activity_under_scoped_integration_cannot_retrieve(isolation_fixture):
    """A client scoped to rfis (no 'activity' visibility) gets an empty list
    even for its own project — it cannot read the activity feed."""
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {isolation_fixture['token_a_partial']}"}
    resp = client.get(
        f"/rest/v1.0/projects/{isolation_fixture['project_a']}/activity", headers=headers
    )
    assert resp.status_code == 200
    assert resp.json() == []

