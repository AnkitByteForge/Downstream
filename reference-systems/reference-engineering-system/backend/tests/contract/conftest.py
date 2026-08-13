from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from domain.entities import (
    Drawing,
    DrawingVersion,
    DesignChange,
    Discipline,
    IntegrationUser,
    ModelObject,
    OAuthClient,
    OAuthToken,
    Project,
    RFI,
    ScheduleActivity,
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
from infrastructure.persistence.repositories.sqlalchemy_design_change_repository import (
    SqlAlchemyDesignChangeRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_drawing_repository import (
    SqlAlchemyDrawingRepository,
    SqlAlchemyDrawingVersionRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_model_object_repository import (
    SqlAlchemyModelObjectRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_schedule_activity_repository import (
    SqlAlchemyScheduleActivityRepository,
)
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
    DesignChangeModel,
    DisciplineModel,
    DrawingModel,
    DrawingVersionModel,
    RevisionCloudModel as RevisionCloudOrmModel,
    IntegrationUserModel,
    ModelObjectModel,
    OAuthClientModel,
    OAuthTokenModel,
    ProjectModel,
    RateLimitStateModel,
    RFIModel,
    ScheduleActivityModel,
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
                capacity_value=240,
                capacity_unit="A_MCA",
                fla_value=200,
                fla_unit="A_FLA",
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


@pytest.fixture()
def design_change_contract_fixture():
    """Real, committed rows for the DesignChange contract tests — two
    isolated projects, each owning a DRAFT DesignChange tied to a source RFI,
    a design_changes/update webhook subscription (project A only), plus full-
    and partial-scope integration credentials. Teardown deletes everything it
    created, in FK-safe order."""
    session = SessionLocal()
    hasher = Pbkdf2PasswordHasher()
    grade = {"tokens": [], "clients": [], "integration_users": []}
    project_a = project_b = None
    try:
        project_repo = SqlAlchemyProjectRepository(session)
        rfi_repo = SqlAlchemyRFIRepository(session)
        design_change_repo = SqlAlchemyDesignChangeRepository(session)
        subscription_repo = SqlAlchemyWebhookSubscriptionRepository(session)
        integration_repo = SqlAlchemyIntegrationUserRepository(session)
        client_repo = SqlAlchemyOAuthClientRepository(session)
        token_repo = SqlAlchemyOAuthTokenRepository(session)

        project_a = project_repo.add(
            Project(id=None, name="Design Change Contract Project A", spec_format="MF2020")
        )
        project_b = project_repo.add(
            Project(id=None, name="Design Change Contract Project B", spec_format="MF2020")
        )
        rfi_a = rfi_repo.add(
            RFI(
                id=None,
                project_id=project_a.id,
                number="214",
                display_number="RFI-214",
                subject="Contract test RFI for ASI",
                ball_in_court=BallInCourt("assignee", None),
                status="OPEN",
            )
        )
        rfi_b = rfi_repo.add(
            RFI(
                id=None,
                project_id=project_b.id,
                number="1",
                display_number="RFI-B1",
                subject="Contract test RFI B",
                ball_in_court=BallInCourt("assignee", None),
                status="OPEN",
            )
        )
        dc_a = design_change_repo.add(
            DesignChange(
                id=None,
                project_id=project_a.id,
                number="1",
                display_number="ASI-1",
                type="ASI",
                status="DRAFT",
                change_reason="Contract test ASI",
                discipline_code="E",
                source_rfi_id=rfi_a.id,
                ball_in_court=BallInCourt("architect", None),
            )
        )
        dc_b = design_change_repo.add(
            DesignChange(
                id=None,
                project_id=project_b.id,
                number="2",
                display_number="CCD-2",
                type="CCD",
                status="DRAFT",
                change_reason="Contract test CCD",
                discipline_code="E",
                source_rfi_id=rfi_b.id,
                ball_in_court=BallInCourt("architect", None),
            )
        )
        subscription_a = subscription_repo.add(
            WebhookSubscription(
                id=None,
                project_id=project_a.id,
                resource_name="design_changes",
                event_type="update",
                target_url="http://127.0.0.1:9/unreachable",
                secret="contract-test-secret",
            )
        )

        def _credential(client_prefix, scope):
            integration_user = integration_repo.add(
                IntegrationUser(
                    id=None,
                    project_id=project_a.id,
                    name=f"DC Contract {client_prefix}",
                    permission_scope=scope,
                )
            )
            client = client_repo.add(
                OAuthClient(
                    client_id=client_prefix,
                    client_secret_hash=hasher.hash("contract-test-secret"),
                    integration_user_id=integration_user.id,
                )
            )
            token = token_repo.add(
                OAuthToken(
                    access_token=f"{client_prefix}-access",
                    refresh_token=f"{client_prefix}-refresh",
                    client_id=client.client_id,
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                )
            )
            grade["tokens"].append(token)
            grade["clients"].append(client)
            grade["integration_users"].append(integration_user.id)
            return token.access_token

        token_a_full = _credential("dc-contract-full-a", PermissionScope.full())
        token_a_partial = _credential("dc-contract-partial-a", PermissionScope.partial("rfis"))

        integration_user_b = integration_repo.add(
            IntegrationUser(
                id=None,
                project_id=project_b.id,
                name="DC Contract Full B",
                permission_scope=PermissionScope.full(),
            )
        )
        client_b = client_repo.add(
            OAuthClient(
                client_id="dc-contract-full-b",
                client_secret_hash=hasher.hash("contract-test-secret"),
                integration_user_id=integration_user_b.id,
            )
        )
        token_b = token_repo.add(
            OAuthToken(
                access_token="dc-contract-full-b-access",
                refresh_token="dc-contract-full-b-refresh",
                client_id=client_b.client_id,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )
        grade["tokens"].append(token_b)
        grade["clients"].append(client_b)
        grade["integration_users"].append(integration_user_b.id)

        session.commit()

        yield {
            "project_a": project_a.id,
            "project_b": project_b.id,
            "rfi_a": rfi_a.id,
            "rfi_b": rfi_b.id,
            "design_change_a": dc_a.id,
            "design_change_b": dc_b.id,
            "subscription_a_id": subscription_a.id,
            "token_a_full": token_a_full,
            "token_a_partial": token_a_partial,
            "token_b": token_b.access_token,
        }
    finally:
        client_ids = [c.client_id for c in grade["clients"]]
        session.execute(
            RateLimitStateModel.__table__.delete().where(
                RateLimitStateModel.client_id.in_(client_ids)
            )
        )
        session.execute(
            WebhookDeliveryModel.__table__.delete().where(
                WebhookDeliveryModel.project_id.in_(
                    [oa.id for oa in (project_a, project_b) if oa is not None]
                )
            )
        )
        for tok in grade["tokens"]:
            session.execute(
                OAuthTokenModel.__table__.delete().where(OAuthTokenModel.client_id == tok.client_id)
            )
        for client in grade["clients"]:
            session.execute(
                OAuthClientModel.__table__.delete().where(OAuthClientModel.client_id == client.client_id)
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
        session.execute(
            DesignChangeModel.__table__.delete().where(
                DesignChangeModel.project_id.in_(
                    [oa.id for oa in (project_a, project_b) if oa is not None]
                )
            )
        )
        session.execute(
            RFIModel.__table__.delete().where(
                RFIModel.project_id.in_([oa.id for oa in (project_a, project_b) if oa is not None])
            )
        )
        for oa in (project_a, project_b):
            if oa is not None:
                session.execute(
                    ProjectModel.__table__.delete().where(ProjectModel.id == oa.id)
                )
        session.commit()
        session.close()


@pytest.fixture()
def drawing_creation_contract_fixture():
    """Real, committed rows for the E.4 Drawing/DrawingVersion creation
    contract tests (ADR-009) -- two isolated projects (cross-project
    isolation), project A pre-seeded with one existing Drawing +
    DrawingVersion (regression coverage for the existing GET routes, and a
    natural-key collision target for the duplicate-creation tests), full-
    and partial-scope credentials on project A, and a full-scope credential
    on project B. Mirrors design_change_contract_fixture's shape."""
    session = SessionLocal()
    hasher = Pbkdf2PasswordHasher()
    grade = {"tokens": [], "clients": [], "integration_users": []}
    project_a = project_b = None
    try:
        discipline_repo = SqlAlchemyDisciplineRepository(session)
        project_repo = SqlAlchemyProjectRepository(session)
        drawing_repo = SqlAlchemyDrawingRepository(session)
        version_repo = SqlAlchemyDrawingVersionRepository(session)
        integration_repo = SqlAlchemyIntegrationUserRepository(session)
        client_repo = SqlAlchemyOAuthClientRepository(session)
        token_repo = SqlAlchemyOAuthTokenRepository(session)

        discipline_repo.add(Discipline(code="DC", name="Drawing Creation Contract Discipline"))
        project_a = project_repo.add(
            Project(id=None, name="Drawing Creation Contract Project A", spec_format="MF2020")
        )
        project_b = project_repo.add(
            Project(id=None, name="Drawing Creation Contract Project B", spec_format="MF2020")
        )

        existing_drawing = drawing_repo.add(
            Drawing(
                id=None,
                project_id=project_a.id,
                sheet_number="E0.4",
                title="Existing Seeded Drawing",
                discipline_code="DC",
            )
        )
        existing_version = version_repo.add(
            DrawingVersion(
                id=None,
                drawing_id=existing_drawing.id,
                revision_label="Rev A",
                issuance_date=date(2026, 6, 1),
                status="DRAFT",
                discipline_code="DC",
            )
        )

        def _credential(client_prefix, project_id, scope):
            integration_user = integration_repo.add(
                IntegrationUser(
                    id=None,
                    project_id=project_id,
                    name=f"Drawing Creation Contract {client_prefix}",
                    permission_scope=scope,
                )
            )
            client = client_repo.add(
                OAuthClient(
                    client_id=client_prefix,
                    client_secret_hash=hasher.hash("contract-test-secret"),
                    integration_user_id=integration_user.id,
                )
            )
            token = token_repo.add(
                OAuthToken(
                    access_token=f"{client_prefix}-access",
                    refresh_token=f"{client_prefix}-refresh",
                    client_id=client.client_id,
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                )
            )
            grade["tokens"].append(token)
            grade["clients"].append(client)
            grade["integration_users"].append(integration_user.id)
            return token.access_token

        token_a_full = _credential("drawing-contract-full-a", project_a.id, PermissionScope.full())
        token_a_partial = _credential(
            "drawing-contract-partial-a", project_a.id, PermissionScope.partial("rfis")
        )
        token_b_full = _credential("drawing-contract-full-b", project_b.id, PermissionScope.full())

        session.commit()

        yield {
            "project_a": project_a.id,
            "project_b": project_b.id,
            "existing_drawing_id": existing_drawing.id,
            "existing_version_id": existing_version.id,
            "token_a_full": token_a_full,
            "token_a_partial": token_a_partial,
            "token_b_full": token_b_full,
        }
    finally:
        client_ids = [c.client_id for c in grade["clients"]]
        session.execute(
            RateLimitStateModel.__table__.delete().where(
                RateLimitStateModel.client_id.in_(client_ids)
            )
        )
        for tok in grade["tokens"]:
            session.execute(
                OAuthTokenModel.__table__.delete().where(OAuthTokenModel.client_id == tok.client_id)
            )
        for client in grade["clients"]:
            session.execute(
                OAuthClientModel.__table__.delete().where(OAuthClientModel.client_id == client.client_id)
            )
        for iu_id in grade["integration_users"]:
            session.execute(
                IntegrationUserModel.__table__.delete().where(IntegrationUserModel.id == iu_id)
            )
        project_ids = [oa.id for oa in (project_a, project_b) if oa is not None]
        # Every DrawingVersion (seeded + any the tests themselves created)
        # under either project's Drawings must be cleared, in FK order:
        # revision clouds -> versions -> drawings.
        drawing_ids = [
            row[0]
            for row in session.execute(
                DrawingModel.__table__.select().with_only_columns(DrawingModel.id).where(
                    DrawingModel.project_id.in_(project_ids)
                )
            )
        ]
        if drawing_ids:
            version_ids = [
                row[0]
                for row in session.execute(
                    DrawingVersionModel.__table__.select()
                    .with_only_columns(DrawingVersionModel.id)
                    .where(DrawingVersionModel.drawing_id.in_(drawing_ids))
                )
            ]
            if version_ids:
                session.execute(
                    RevisionCloudOrmModel.__table__.delete().where(
                        RevisionCloudOrmModel.version_id.in_(version_ids)
                    )
                )
            session.execute(
                DrawingVersionModel.__table__.update()
                .where(DrawingVersionModel.drawing_id.in_(drawing_ids))
                .values(superseded_by_id=None)
            )
            session.execute(
                DrawingModel.__table__.update()
                .where(DrawingModel.id.in_(drawing_ids))
                .values(current_version_id=None)
            )
            session.execute(
                DrawingVersionModel.__table__.delete().where(
                    DrawingVersionModel.drawing_id.in_(drawing_ids)
                )
            )
            session.execute(DrawingModel.__table__.delete().where(DrawingModel.id.in_(drawing_ids)))
        for oa in (project_a, project_b):
            if oa is not None:
                session.execute(ProjectModel.__table__.delete().where(ProjectModel.id == oa.id))
        session.execute(DisciplineModel.__table__.delete().where(DisciplineModel.code == "DC"))
        session.commit()
        session.close()


@pytest.fixture()
def res5_contract_fixture():
    """Real, committed rows for the ScheduleActivity/ModelObject contract
    tests (RES-5E) — two isolated projects, each owning one ScheduleActivity
    and one ModelObject, plus full- and partial-scope integration credentials
    on project A and a full-scope credential on project B. Mirrors
    ``design_change_contract_fixture``'s shape for a read-only surface (no
    webhook subscription — neither entity dispatches one, ADR-008)."""
    session = SessionLocal()
    hasher = Pbkdf2PasswordHasher()
    grade = {"tokens": [], "clients": [], "integration_users": []}
    project_a = project_b = None
    try:
        project_repo = SqlAlchemyProjectRepository(session)
        schedule_activity_repo = SqlAlchemyScheduleActivityRepository(session)
        model_object_repo = SqlAlchemyModelObjectRepository(session)
        integration_repo = SqlAlchemyIntegrationUserRepository(session)
        client_repo = SqlAlchemyOAuthClientRepository(session)
        token_repo = SqlAlchemyOAuthTokenRepository(session)

        project_a = project_repo.add(
            Project(id=None, name="RES-5 Contract Project A", spec_format="MF2020")
        )
        project_b = project_repo.add(
            Project(id=None, name="RES-5 Contract Project B", spec_format="MF2020")
        )
        activity_a = schedule_activity_repo.add(
            ScheduleActivity(id=None, project_id=project_a.id, activity_code="A-1", type="TASK")
        )
        activity_b = schedule_activity_repo.add(
            ScheduleActivity(id=None, project_id=project_b.id, activity_code="B-1", type="TASK")
        )
        model_object_a = model_object_repo.add(
            ModelObject(
                id=None,
                project_id=project_a.id,
                discipline_code="E",
                appearance_profile="INSTALL",
                resource_link_id=activity_a.id,
            )
        )
        model_object_b = model_object_repo.add(
            ModelObject(
                id=None, project_id=project_b.id, discipline_code="M", appearance_profile="REMOVE"
            )
        )

        def _credential(client_prefix, project_id, scope):
            integration_user = integration_repo.add(
                IntegrationUser(
                    id=None, project_id=project_id, name=f"RES-5 Contract {client_prefix}", permission_scope=scope
                )
            )
            client = client_repo.add(
                OAuthClient(
                    client_id=client_prefix,
                    client_secret_hash=hasher.hash("contract-test-secret"),
                    integration_user_id=integration_user.id,
                )
            )
            token = token_repo.add(
                OAuthToken(
                    access_token=f"{client_prefix}-access",
                    refresh_token=f"{client_prefix}-refresh",
                    client_id=client.client_id,
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                )
            )
            grade["tokens"].append(token)
            grade["clients"].append(client)
            grade["integration_users"].append(integration_user.id)
            return token.access_token

        token_a_full = _credential("res5-contract-full-a", project_a.id, PermissionScope.full())
        token_a_partial = _credential(
            "res5-contract-partial-a", project_a.id, PermissionScope.partial("rfis")
        )
        token_b_full = _credential("res5-contract-full-b", project_b.id, PermissionScope.full())

        session.commit()

        yield {
            "project_a": project_a.id,
            "project_b": project_b.id,
            "schedule_activity_a": activity_a.id,
            "schedule_activity_b": activity_b.id,
            "model_object_a": model_object_a.id,
            "model_object_b": model_object_b.id,
            "token_a_full": token_a_full,
            "token_a_partial": token_a_partial,
            "token_b_full": token_b_full,
        }
    finally:
        client_ids = [c.client_id for c in grade["clients"]]
        session.execute(
            RateLimitStateModel.__table__.delete().where(
                RateLimitStateModel.client_id.in_(client_ids)
            )
        )
        for tok in grade["tokens"]:
            session.execute(
                OAuthTokenModel.__table__.delete().where(OAuthTokenModel.client_id == tok.client_id)
            )
        for client in grade["clients"]:
            session.execute(
                OAuthClientModel.__table__.delete().where(OAuthClientModel.client_id == client.client_id)
            )
        for iu_id in grade["integration_users"]:
            session.execute(
                IntegrationUserModel.__table__.delete().where(IntegrationUserModel.id == iu_id)
            )
        session.execute(
            ModelObjectModel.__table__.delete().where(
                ModelObjectModel.project_id.in_(
                    [oa.id for oa in (project_a, project_b) if oa is not None]
                )
            )
        )
        session.execute(
            ScheduleActivityModel.__table__.delete().where(
                ScheduleActivityModel.project_id.in_(
                    [oa.id for oa in (project_a, project_b) if oa is not None]
                )
            )
        )
        for oa in (project_a, project_b):
            if oa is not None:
                session.execute(
                    ProjectModel.__table__.delete().where(ProjectModel.id == oa.id)
                )
        session.commit()
        session.close()
