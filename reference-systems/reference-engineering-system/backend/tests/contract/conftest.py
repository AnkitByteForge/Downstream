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
    User,
    WebhookSubscription,
)
from domain.entities.spec import SpecDivision, SpecSection
from domain.entities.submittal import Submittal, SubmittalReviewStatus, SubmittalRevision
from domain.value_objects import BallInCourt, PermissionScope
from infrastructure.auth.password_hashing import Pbkdf2PasswordHasher
from infrastructure.persistence.db import SessionLocal
from infrastructure.persistence.repositories.sqlalchemy_project_repository import (
    SqlAlchemyDisciplineRepository,
    SqlAlchemyProjectRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_rfi_repository import SqlAlchemyRFIRepository
from infrastructure.persistence.repositories.sqlalchemy_spec_repository import (
    SqlAlchemySpecDivisionRepository,
    SqlAlchemySpecSectionRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_submittal_repository import (
    SqlAlchemySubmittalRepository,
    SqlAlchemySubmittalReviewStatusRepository,
    SqlAlchemySubmittalRevisionRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SqlAlchemyIntegrationUserRepository,
    SqlAlchemyOAuthClientRepository,
    SqlAlchemyOAuthTokenRepository,
    SqlAlchemyUserRepository,
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
    SpecDivisionModel,
    SpecSectionModel,
    SubmittalModel,
    SubmittalRevisionModel,
    SubmittalReviewStatusModel,
    UserModel,
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


@pytest.fixture()
def submittal_contract_fixture():
    """Real, committed rows for the Submittal contract tests — separate from
    contract_fixture so the two test files never share mutable state."""
    session = SessionLocal()
    hasher = Pbkdf2PasswordHasher()
    try:
        project_repo = SqlAlchemyProjectRepository(session)
        division_repo = SqlAlchemySpecDivisionRepository(session)
        section_repo = SqlAlchemySpecSectionRepository(session)
        status_repo = SqlAlchemySubmittalReviewStatusRepository(session)
        submittal_repo = SqlAlchemySubmittalRepository(session)
        revision_repo = SqlAlchemySubmittalRevisionRepository(session)
        subscription_repo = SqlAlchemyWebhookSubscriptionRepository(session)
        integration_repo = SqlAlchemyIntegrationUserRepository(session)
        client_repo = SqlAlchemyOAuthClientRepository(session)
        token_repo = SqlAlchemyOAuthTokenRepository(session)
        user_repo = SqlAlchemyUserRepository(session)

        project = project_repo.add(
            Project(id=None, name="Submittal Contract Test Project", spec_format="MF2020")
        )
        disposer = user_repo.add(
            User(
                id=None,
                project_id=project.id,
                name="Contract Test Reviewer",
                email="contract-test-reviewer@example.test",
                role="ARCHITECT_ENGINEER_OF_RECORD",
                password_hash=hasher.hash("unused"),
            )
        )
        division_repo.add(SpecDivision(number="98", title="Submittal Contract Test Division"))
        section = section_repo.add(
            SpecSection(
                id=None,
                project_id=project.id,
                division_number="98",
                number="98 00 00",
                title="Submittal Contract Test Section",
            )
        )
        pending = status_repo.add(
            SubmittalReviewStatus(
                id=None,
                project_id=project.id,
                code="PENDING",
                label="Pending",
                gates_procurement=False,
                is_terminal=False,
            )
        )
        status_repo.add(
            SubmittalReviewStatus(
                id=None,
                project_id=project.id,
                code="NO_EXCEPTIONS_TAKEN",
                label="No Exceptions Taken",
                gates_procurement=True,
                is_terminal=True,
            )
        )
        status_repo.add(
            SubmittalReviewStatus(
                id=None,
                project_id=project.id,
                code="REVISE_AND_RESUBMIT",
                label="Revise and Resubmit",
                gates_procurement=False,
                is_terminal=True,
            )
        )
        submittal = submittal_repo.add(
            Submittal(id=None, project_id=project.id, number="1", spec_section_id=section.id)
        )
        revision = revision_repo.add(
            SubmittalRevision(
                id=None,
                submittal_id=submittal.id,
                rev_label="Rev 0",
                review_status_id=pending.id,
                ball_in_court=BallInCourt("submitter", None),
            )
        )
        subscription = subscription_repo.add(
            WebhookSubscription(
                id=None,
                project_id=project.id,
                resource_name="submittals",
                event_type="update",
                target_url="http://127.0.0.1:9/unreachable",
                secret="contract-test-secret",
            )
        )
        integration_user = integration_repo.add(
            IntegrationUser(
                id=None,
                project_id=project.id,
                name="Submittal Contract Test Client",
                permission_scope=PermissionScope.full(),
            )
        )
        client = client_repo.add(
            OAuthClient(
                client_id="submittal-contract-test-client",
                client_secret_hash=hasher.hash("contract-test-secret"),
                integration_user_id=integration_user.id,
            )
        )
        token = token_repo.add(
            OAuthToken(
                access_token="submittal-contract-test-access-token",
                refresh_token="submittal-contract-test-refresh-token",
                client_id=client.client_id,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )
        session.commit()

        yield {
            "project_id": project.id,
            "submittal_id": submittal.id,
            "revision_id": revision.id,
            "subscription_id": subscription.id,
            "access_token": token.access_token,
            "client_id": client.client_id,
            "disposed_by_user_id": disposer.id,
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
        session.execute(
            SubmittalRevisionModel.__table__.delete().where(
                SubmittalRevisionModel.submittal_id == submittal.id
            )
        )
        session.execute(UserModel.__table__.delete().where(UserModel.id == disposer.id))
        session.execute(SubmittalModel.__table__.delete().where(SubmittalModel.project_id == project.id))
        session.execute(
            SubmittalReviewStatusModel.__table__.delete().where(
                SubmittalReviewStatusModel.project_id == project.id
            )
        )
        session.execute(
            SpecSectionModel.__table__.delete().where(SpecSectionModel.project_id == project.id)
        )
        session.execute(SpecDivisionModel.__table__.delete().where(SpecDivisionModel.number == "98"))
        session.execute(ProjectModel.__table__.delete().where(ProjectModel.id == project.id))
        session.commit()
        session.close()
