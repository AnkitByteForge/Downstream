from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app
from domain.entities import IntegrationUser, OAuthClient, Project
from domain.value_objects import PermissionScope
from infrastructure.auth.password_hashing import Pbkdf2PasswordHasher
from infrastructure.persistence.db import SessionLocal
from infrastructure.persistence.orm_models import (
    IntegrationUserModel,
    OAuthClientModel,
    OAuthTokenModel,
    ProjectModel,
    RateLimitStateModel,
)
from infrastructure.persistence.repositories.sqlalchemy_project_repository import SqlAlchemyProjectRepository
from infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SqlAlchemyIntegrationUserRepository,
    SqlAlchemyOAuthClientRepository,
)

# ADR-009: the additive client_credentials grant DIP's promotion client
# (E.5) authenticates with. Contract-tested against the full app/real HTTP
# client, same convention as every other tests/contract file. No prior
# test file exercised /oauth/token at all -- this is new coverage for the
# grant this milestone adds, not a retrofit of the pre-existing
# authorization_code/refresh_token grants.

CLIENT_SECRET = "cc-contract-test-secret"


@pytest.fixture()
def oauth_client_credentials_fixture():
    session = SessionLocal()
    hasher = Pbkdf2PasswordHasher()
    try:
        project = SqlAlchemyProjectRepository(session).add(
            Project(id=None, name="OAuth CC Contract Project", spec_format="MF2020")
        )
        integration_user = SqlAlchemyIntegrationUserRepository(session).add(
            IntegrationUser(
                id=None,
                project_id=project.id,
                name="OAuth CC Contract Client",
                permission_scope=PermissionScope.partial("documents"),
            )
        )
        client = SqlAlchemyOAuthClientRepository(session).add(
            OAuthClient(
                client_id="cc-contract-client",
                client_secret_hash=hasher.hash(CLIENT_SECRET),
                integration_user_id=integration_user.id,
            )
        )
        session.commit()
        yield {"client_id": client.client_id, "project_id": project.id}
    finally:
        session.execute(
            RateLimitStateModel.__table__.delete().where(
                RateLimitStateModel.client_id == "cc-contract-client"
            )
        )
        session.execute(
            OAuthTokenModel.__table__.delete().where(
                OAuthTokenModel.client_id == "cc-contract-client"
            )
        )
        session.execute(
            OAuthClientModel.__table__.delete().where(
                OAuthClientModel.client_id == "cc-contract-client"
            )
        )
        session.execute(
            IntegrationUserModel.__table__.delete().where(
                IntegrationUserModel.name == "OAuth CC Contract Client"
            )
        )
        session.execute(
            ProjectModel.__table__.delete().where(ProjectModel.name == "OAuth CC Contract Project")
        )
        session.commit()
        session.close()


def test_client_credentials_grant_issues_a_usable_access_token(oauth_client_credentials_fixture):
    client = TestClient(app)
    resp = client.post(
        "/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": oauth_client_credentials_fixture["client_id"],
            "client_secret": CLIENT_SECRET,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["expires_in"] == 3600

    project_id = oauth_client_credentials_fixture["project_id"]
    authed = client.get(
        f"/rest/v1.0/projects/{project_id}/documents",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert authed.status_code == 200


def test_client_credentials_grant_rejects_wrong_secret(oauth_client_credentials_fixture):
    client = TestClient(app)
    resp = client.post(
        "/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": oauth_client_credentials_fixture["client_id"],
            "client_secret": "wrong-secret",
        },
    )
    assert resp.status_code == 401


def test_client_credentials_grant_rejects_unknown_client_id():
    client = TestClient(app)
    resp = client.post(
        "/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": "no-such-client",
            "client_secret": "irrelevant",
        },
    )
    assert resp.status_code == 401


def test_client_credentials_grant_does_not_require_a_code_or_refresh_token(oauth_client_credentials_fixture):
    """The whole point of this grant: no prior authorization_code exchange
    and no existing refresh_token are needed -- a fresh, unattended client
    can authenticate on its very first call."""
    client = TestClient(app)
    resp = client.post(
        "/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": oauth_client_credentials_fixture["client_id"],
            "client_secret": CLIENT_SECRET,
        },
    )
    assert resp.status_code == 200
