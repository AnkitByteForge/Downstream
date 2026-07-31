from __future__ import annotations

import os
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from domain.entities import (
    Discipline,
    Drawing,
    DrawingVersion,
    IntegrationUser,
    Location,
    OAuthClient,
    Project,
    RFI,
    SpecDivision,
    SpecSection,
    User,
    WebhookSubscription,
)
from domain.state_machines import drawing_version_transitions, rfi_transitions
from domain.value_objects import BallInCourt, PermissionScope, RevisionCloud
from infrastructure.auth.password_hashing import Pbkdf2PasswordHasher
from infrastructure.persistence.repositories.sqlalchemy_drawing_repository import (
    SqlAlchemyDrawingRepository,
    SqlAlchemyDrawingVersionRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_location_repository import (
    SqlAlchemyLocationRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_project_repository import (
    SqlAlchemyDisciplineRepository,
    SqlAlchemyProjectRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_rfi_repository import SqlAlchemyRFIRepository
from infrastructure.persistence.repositories.sqlalchemy_spec_repository import (
    SqlAlchemySpecDivisionRepository,
    SqlAlchemySpecSectionRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SqlAlchemyIntegrationUserRepository,
    SqlAlchemyOAuthClientRepository,
    SqlAlchemyUserRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_webhook_repository import (
    SqlAlchemyWebhookSubscriptionRepository,
)

# The exact scenario from 05_Downstream_Reference_Execution_Trace.md: Ananya Rao
# reviews RFI-214 on Meridian Tower, a duct reroute at Grid B-4 citing Spec
# 23 31 13 and Drawing M-2.1 Rev C. This seed reproduces every field the trace
# shows literally, so a later Connector-Procore build can be tested against
# this system and reproduce the same trace end to end.

RFI_CLOSED_AT = datetime(2026, 7, 28, 9, 14, 3, tzinfo=timezone.utc)
DEMO_PASSWORD = "downstream-demo"

# Seeded so closing an RFI has somewhere real to dispatch to. Overridable so
# a future Connector-Procore dev instance can subscribe its own inbound
# receiver here instead of the default no-op sink.
DEFAULT_WEBHOOK_TARGET_URL = os.environ.get(
    "RES_SEED_WEBHOOK_TARGET_URL", "http://localhost:9999/webhook-sink"
)
DEFAULT_WEBHOOK_SECRET = "seed-webhook-secret"


def seed(session: Session) -> dict:
    hasher = Pbkdf2PasswordHasher()

    discipline_repo = SqlAlchemyDisciplineRepository(session)
    project_repo = SqlAlchemyProjectRepository(session)
    division_repo = SqlAlchemySpecDivisionRepository(session)
    section_repo = SqlAlchemySpecSectionRepository(session)
    location_repo = SqlAlchemyLocationRepository(session)
    user_repo = SqlAlchemyUserRepository(session)
    drawing_repo = SqlAlchemyDrawingRepository(session)
    version_repo = SqlAlchemyDrawingVersionRepository(session)
    rfi_repo = SqlAlchemyRFIRepository(session)
    integration_repo = SqlAlchemyIntegrationUserRepository(session)
    oauth_client_repo = SqlAlchemyOAuthClientRepository(session)
    webhook_subscription_repo = SqlAlchemyWebhookSubscriptionRepository(session)

    discipline_repo.add(Discipline(code="M", name="Mechanical"))

    project = project_repo.add(Project(id=None, name="Meridian Tower", spec_format="MF2020"))

    division_repo.add(SpecDivision(number="23", title="Heating, Ventilating, and Air Conditioning (HVAC)"))
    spec_section = section_repo.add(
        SpecSection(
            id=None,
            project_id=project.id,
            division_number="23",
            number="23 31 13",
            title="HVAC Ducts",
        )
    )

    site = location_repo.add(
        Location(id=None, project_id=project.id, parent_id=None, tier_level=0, name="Meridian Tower Site", type="site")
    )
    building = location_repo.add(
        Location(id=None, project_id=project.id, parent_id=site.id, tier_level=1, name="Main Building", type="building")
    )
    level_4 = location_repo.add(
        Location(id=None, project_id=project.id, parent_id=building.id, tier_level=2, name="Level 4", type="level")
    )
    grid_b4 = location_repo.add(
        Location(id=None, project_id=project.id, parent_id=level_4.id, tier_level=3, name="Grid B-4", type="gridline")
    )

    ananya = user_repo.add(
        User(
            id=None,
            project_id=project.id,
            name="Ananya Rao",
            email="ananya.rao@meridiangc.example",
            role="PROJECT_MANAGER",
            password_hash=hasher.hash(DEMO_PASSWORD),
        )
    )
    site_engineer = user_repo.add(
        User(
            id=None,
            project_id=project.id,
            name="Kabir Mehta",
            email="kabir.mehta@meridiangc.example",
            role="PROJECT_ENGINEER",
            password_hash=hasher.hash(DEMO_PASSWORD),
        )
    )
    user_repo.add(
        User(
            id=None,
            project_id=project.id,
            name="Rhea Fernandes",
            email="rhea.fernandes@archstudio.example",
            role="ARCHITECT_ENGINEER_OF_RECORD",
            password_hash=hasher.hash(DEMO_PASSWORD),
        )
    )
    user_repo.add(
        User(
            id=None,
            project_id=project.id,
            name="Vikram Suresh",
            email="vikram.suresh@arjunsteelworks.example",
            role="SUBCONTRACTOR",
            password_hash=hasher.hash(DEMO_PASSWORD),
        )
    )
    user_repo.add(
        User(
            id=None,
            project_id=project.id,
            name="System Admin",
            email="admin@downstream.example",
            role="ADMIN",
            password_hash=hasher.hash(DEMO_PASSWORD),
        )
    )

    drawing = drawing_repo.add(
        Drawing(
            id=None,
            project_id=project.id,
            sheet_number="M-2.1",
            title="Mechanical Plan - Level 4",
            discipline_code="M",
        )
    )

    rev_b = version_repo.add(
        DrawingVersion(
            id=None,
            drawing_id=drawing.id,
            revision_label="Rev B",
            issuance_date=date(2026, 6, 2),
            status="DRAFT",
            discipline_code="M",
            location_ids=[grid_b4.id],
        )
    )
    rev_b = version_repo.update(drawing_version_transitions.issue_version(rev_b))

    rev_c = version_repo.add(
        DrawingVersion(
            id=None,
            drawing_id=drawing.id,
            revision_label="Rev C",
            issuance_date=date(2026, 7, 28),
            status="DRAFT",
            discipline_code="M",
            location_ids=[grid_b4.id],
        )
    )
    rev_c = version_repo.update(drawing_version_transitions.issue_version(rev_c))
    rev_c = version_repo.update(
        drawing_version_transitions.mark_revised(
            rev_c,
            [
                RevisionCloud(
                    area="Grid B-4",
                    delta_number=1,
                    description="Duct DN200 rerouted 0.6m south of Beam B-14",
                )
            ],
        )
    )

    rev_b = version_repo.update(drawing_version_transitions.supersede(rev_b, rev_c.id))
    drawing.current_version_id = rev_c.id
    drawing_repo.update(drawing)

    rfi = rfi_repo.add(
        RFI(
            id=None,
            project_id=project.id,
            number="214",
            display_number="RFI-214",
            subject="Duct routing conflict at Grid B-4 vs. structural beam",
            ball_in_court=BallInCourt("assignee", site_engineer.id),
            discipline_code="M",
            raw_document_ref="engineering://attachments/SK-14_reroute.pdf",
            drawing_version_ids=[rev_c.id],
            spec_section_ids=[spec_section.id],
            location_ids=[grid_b4.id],
        )
    )
    rfi = rfi_repo.update(rfi_transitions.open_rfi(rfi, site_engineer.id))
    rfi = rfi_repo.update(
        rfi_transitions.respond_to_rfi(
            rfi,
            "Reroute duct per attached SK-14. Duct now runs south of beam, see "
            "revised Spec 23 31 13 clause 2.3 and Drawing M-2.1 Rev C.",
            ananya.id,
        )
    )
    rfi = rfi_repo.update(rfi_transitions.close_rfi(rfi, RFI_CLOSED_AT))

    full_scope_integration = integration_repo.add(
        IntegrationUser(
            id=None, project_id=project.id, name="Downstream (full scope)", permission_scope=PermissionScope.full()
        )
    )
    partial_scope_integration = integration_repo.add(
        IntegrationUser(
            id=None,
            project_id=project.id,
            name="Downstream (partial scope)",
            permission_scope=PermissionScope.partial("rfis", "submittals", "documents"),
        )
    )

    oauth_client_repo.add(
        OAuthClient(
            client_id="downstream-full",
            client_secret_hash=hasher.hash("full-scope-secret"),
            integration_user_id=full_scope_integration.id,
            authorization_code="seed-auth-code-full",
        )
    )
    oauth_client_repo.add(
        OAuthClient(
            client_id="downstream-partial",
            client_secret_hash=hasher.hash("partial-scope-secret"),
            integration_user_id=partial_scope_integration.id,
            authorization_code="seed-auth-code-partial",
        )
    )

    webhook_subscription_repo.add(
        WebhookSubscription(
            id=None,
            project_id=project.id,
            resource_name="rfis",
            event_type="update",
            target_url=DEFAULT_WEBHOOK_TARGET_URL,
            secret=DEFAULT_WEBHOOK_SECRET,
        )
    )

    return {
        "project_id": project.id,
        "rfi_id": rfi.id,
        "drawing_id": drawing.id,
        "current_version_id": rev_c.id,
        "ananya_user_id": ananya.id,
        "demo_password": DEMO_PASSWORD,
    }
