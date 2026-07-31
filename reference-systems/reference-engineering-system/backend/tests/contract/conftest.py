from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from domain.entities import (
    Discipline,
    IntegrationUser,
    OAuthClient,
    OAuthToken,
    Project,
    RFI,
    WebhookSubscription,
)
from domain.value_objects import BallInCourt, PermissionScope
from infrastructure.auth.password_hashing import Pbkdf2PasswordHasher
from infrastructure.persistence.db import SessionLocal
from infrastructure.persistence.repositories.sqlalchemy_project_repository import (
    SqlAlchemyDisciplineRepository,
    SqlAlchemyProjectRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_rfi_repository import SqlAlchemyRFIRepository
from infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SqlAlchemyIntegrationUserRepository,
    SqlAlchemyOAuthClientRepository,
    SqlAlchemyOAuthTokenRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_webhook_repository import (
    SqlAlchemyWebhookSubscriptionRepository,
)
from infrastructure.persistence.orm_models import (
    DisciplineModel,
    IntegrationUserModel,
    OAuthClientModel,
    OAuthTokenModel,
    ProjectModel,
    RateLimitStateModel,
    RFIModel,
    WebhookDeliveryModel,
    WebhookSubscriptionModel,
)


@pytest.fixture()
def contract_fixture():
    """Real, committed rows in a throwaway project — contract tests exercise
    the full app (real DB, real HTTP client) so nothing here can be an
    in-process rollback trick; teardown deletes everything it created."""
    session = SessionLocal()
    hasher = Pbkdf2PasswordHasher()
    try:
        discipline_repo = SqlAlchemyDisciplineRepository(session)
        project_repo = SqlAlchemyProjectRepository(session)
        rfi_repo = SqlAlchemyRFIRepository(session)
        subscription_repo = SqlAlchemyWebhookSubscriptionRepository(session)
        integration_repo = SqlAlchemyIntegrationUserRepository(session)
        client_repo = SqlAlchemyOAuthClientRepository(session)
        token_repo = SqlAlchemyOAuthTokenRepository(session)

        discipline = discipline_repo.add(Discipline(code="CT", name="Contract Test Discipline"))
        project = project_repo.add(Project(id=None, name="Contract Test Project", spec_format="MF2020"))
        rfi = rfi_repo.add(
            RFI(
                id=None,
                project_id=project.id,
                number="1",
                display_number="RFI-1",
                subject="Contract test RFI",
                ball_in_court=BallInCourt("assignee", None),
                status="OPEN",
                discipline_code=discipline.code,
            )
        )
        subscription = subscription_repo.add(
            WebhookSubscription(
                id=None,
                project_id=project.id,
                resource_name="rfis",
                event_type="update",
                target_url="http://127.0.0.1:9/unreachable",
                secret="contract-test-secret",
            )
        )
        integration_user = integration_repo.add(
            IntegrationUser(
                id=None, project_id=project.id, name="Contract Test Client", permission_scope=PermissionScope.full()
            )
        )
        client = client_repo.add(
            OAuthClient(
                client_id="contract-test-client",
                client_secret_hash=hasher.hash("contract-test-secret"),
                integration_user_id=integration_user.id,
            )
        )
        token = token_repo.add(
            OAuthToken(
                access_token="contract-test-access-token",
                refresh_token="contract-test-refresh-token",
                client_id=client.client_id,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )
        session.commit()

        yield {
            "project_id": project.id,
            "rfi_id": rfi.id,
            "subscription_id": subscription.id,
            "access_token": token.access_token,
            "client_id": client.client_id,
        }
    finally:
        session.execute(
            RateLimitStateModel.__table__.delete().where(
                RateLimitStateModel.client_id == client.client_id
            )
        )
        session.execute(
            WebhookDeliveryModel.__table__.delete().where(
                WebhookDeliveryModel.project_id == project.id
            )
        )
        session.execute(
            OAuthTokenModel.__table__.delete().where(OAuthTokenModel.client_id == client.client_id)
        )
        session.execute(
            OAuthClientModel.__table__.delete().where(OAuthClientModel.client_id == client.client_id)
        )
        session.execute(
            IntegrationUserModel.__table__.delete().where(
                IntegrationUserModel.id == integration_user.id
            )
        )
        session.execute(
            WebhookSubscriptionModel.__table__.delete().where(
                WebhookSubscriptionModel.project_id == project.id
            )
        )
        session.execute(RFIModel.__table__.delete().where(RFIModel.project_id == project.id))
        session.execute(ProjectModel.__table__.delete().where(ProjectModel.id == project.id))
        session.execute(DisciplineModel.__table__.delete().where(DisciplineModel.code == "CT"))
        session.commit()
        session.close()
