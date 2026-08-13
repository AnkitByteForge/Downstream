"""E.7 support script -- seeds (idempotently) the throwaway project and
OAuth2 client_credentials integration client the DIP -> RES real-E0.4
promotion golden test authenticates as.

Not part of RES's own application code and not imported by anything in
src/ -- a standalone, idempotent setup script for one specific
cross-system golden test (tests/golden/test_e07_real_e04_promotion.py in
the DIP package), invoked as a subprocess from DIP's own Python
environment (which has no RES/Postgres dependencies at all -- see that
test's own docstring for why this runs as a separate process instead of
an in-process import).

Prints one JSON object to stdout: {"project_id": ..., "client_id": ...,
"client_secret": ...}. The client_secret is a fixed, test-only value
(same convention as every other tests/contract/conftest.py fixture in
this codebase, e.g. "contract-test-secret") -- never a real credential.
"""

from __future__ import annotations

import json

from domain.entities import Discipline, IntegrationUser, OAuthClient, Project
from domain.value_objects import PermissionScope
from infrastructure.auth.password_hashing import Pbkdf2PasswordHasher
from infrastructure.persistence.db import SessionLocal
from infrastructure.persistence.repositories.sqlalchemy_project_repository import (
    SqlAlchemyDisciplineRepository,
    SqlAlchemyProjectRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SqlAlchemyIntegrationUserRepository,
    SqlAlchemyOAuthClientRepository,
)

PROJECT_NAME = "DIP E0.4 Promotion Golden Test"
CLIENT_ID = "dip-e04-golden-test-client"
CLIENT_SECRET = "dip-e04-golden-test-secret"


def main() -> None:
    session = SessionLocal()
    try:
        discipline_repo = SqlAlchemyDisciplineRepository(session)
        project_repo = SqlAlchemyProjectRepository(session)
        integration_repo = SqlAlchemyIntegrationUserRepository(session)
        client_repo = SqlAlchemyOAuthClientRepository(session)
        hasher = Pbkdf2PasswordHasher()

        if discipline_repo.get("E") is None:
            discipline_repo.add(Discipline(code="E", name="Electrical"))

        existing_client = client_repo.get(CLIENT_ID)
        if existing_client is not None:
            # IntegrationUser doesn't expose a get(); re-derive project_id
            # from the existing project by name instead of a second lookup
            # path -- simplest at this scale (one throwaway project, never
            # more than one match).
            project = next(p for p in project_repo.list() if p.name == PROJECT_NAME)
            print(json.dumps({"project_id": project.id, "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}))
            return

        project = next((p for p in project_repo.list() if p.name == PROJECT_NAME), None)
        if project is None:
            project = project_repo.add(Project(id=None, name=PROJECT_NAME, spec_format="MF2020"))

        integration_user = integration_repo.add(
            IntegrationUser(
                id=None,
                project_id=project.id,
                name="DIP E0.4 Promotion Golden Test Client",
                permission_scope=PermissionScope.partial("documents"),
            )
        )
        client_repo.add(
            OAuthClient(
                client_id=CLIENT_ID,
                client_secret_hash=hasher.hash(CLIENT_SECRET),
                integration_user_id=integration_user.id,
            )
        )
        session.commit()

        print(json.dumps({"project_id": project.id, "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}))
    finally:
        session.close()


if __name__ == "__main__":
    main()
