from __future__ import annotations

from domain.entities.project import Discipline, Project
from domain.entities.spec import SpecDivision, SpecSection
from domain.entities.submittal import Submittal, SubmittalReviewStatus, SubmittalRevision
from domain.value_objects import BallInCourt
from infrastructure.persistence.repositories.sqlalchemy_project_repository import (
    SqlAlchemyDisciplineRepository,
    SqlAlchemyProjectRepository,
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


def _seed_project_and_spec_section(session):
    SqlAlchemyDisciplineRepository(session).add(Discipline(code="IT", name="Integration Test Discipline"))
    project = SqlAlchemyProjectRepository(session).add(Project(id=None, name="Integration Test Project", spec_format="MF2020"))
    SqlAlchemySpecDivisionRepository(session).add(SpecDivision(number="99", title="Integration Test Division"))
    section = SqlAlchemySpecSectionRepository(session).add(
        SpecSection(id=None, project_id=project.id, division_number="99", number="99 00 00", title="Test Section")
    )
    return project, section


def test_submittal_revision_round_trip_including_gates_procurement(db_session):
    project, section = _seed_project_and_spec_section(db_session)
    status_repo = SqlAlchemySubmittalReviewStatusRepository(db_session)
    net = status_repo.add(
        SubmittalReviewStatus(
            id=None,
            project_id=project.id,
            code="NO_EXCEPTIONS_TAKEN",
            label="No Exceptions Taken",
            gates_procurement=True,
            is_terminal=True,
        )
    )

    submittal_repo = SqlAlchemySubmittalRepository(db_session)
    submittal = submittal_repo.add(
        Submittal(id=None, project_id=project.id, number="1", spec_section_id=section.id)
    )

    revision_repo = SqlAlchemySubmittalRevisionRepository(db_session)
    revision = revision_repo.add(
        SubmittalRevision(
            id=None,
            submittal_id=submittal.id,
            rev_label="Rev 0",
            review_status_id=net.id,
            ball_in_court=BallInCourt("closed", None),
            equipment_tag="TEST-1",
        )
    )

    fetched = revision_repo.get(revision.id)
    assert fetched.equipment_tag == "TEST-1"
    assert fetched.review_status_id == net.id

    fetched_status = status_repo.get_by_code(project.id, "NO_EXCEPTIONS_TAKEN")
    assert fetched_status.gates_procurement is True

    revisions_for_submittal = revision_repo.list_by_submittal(submittal.id)
    assert len(revisions_for_submittal) == 1
