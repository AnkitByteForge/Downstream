from __future__ import annotations

from dataclasses import dataclass

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from application.exceptions import Unauthorized
from application.ports import PasswordHasherPort, SessionTokenServicePort
from application.use_cases.auth_use_cases import LoginUser
from application.use_cases.drawing_use_cases import (
    GetDrawing,
    GetDrawingVersion,
    ListDrawings,
    ListDrawingVersions,
)
from application.use_cases.location_use_cases import ListLocations
from application.use_cases.oauth_use_cases import IssueTokenFromAuthorizationCode, RefreshOAuthToken
from application.use_cases.project_use_cases import GetProject, ListProjects
from application.use_cases.rfi_use_cases import CloseRFI, GetRFI, ListRFIs, RespondToRFI
from application.use_cases.spec_use_cases import ListSpecDivisions, ListSpecSections
from domain.value_objects import PermissionScope
from infrastructure.auth.jwt_service import JwtSessionTokenService
from infrastructure.auth.opaque_token_service import SecureOpaqueTokenService
from infrastructure.auth.password_hashing import Pbkdf2PasswordHasher
from infrastructure.clock import SystemClock
from infrastructure.config import settings
from infrastructure.persistence.db import get_session
from infrastructure.persistence.repositories.sqlalchemy_drawing_repository import (
    SqlAlchemyDrawingRepository,
    SqlAlchemyDrawingVersionRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_location_repository import (
    SqlAlchemyLocationRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_project_repository import (
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
    SqlAlchemyOAuthTokenRepository,
    SqlAlchemyUserRepository,
)

# ---------------------------------------------------------------------------
# Infrastructure singletons (stateless adapters — safe to share across requests)
# ---------------------------------------------------------------------------

_password_hasher = Pbkdf2PasswordHasher()
_session_token_service = JwtSessionTokenService(settings)
_opaque_token_service = SecureOpaqueTokenService()
_clock = SystemClock()


def get_db_session(session: Session = Depends(get_session)) -> Session:
    return session


def get_password_hasher() -> PasswordHasherPort:
    return _password_hasher


def get_session_token_service() -> SessionTokenServicePort:
    return _session_token_service


def get_opaque_token_service() -> SecureOpaqueTokenService:
    return _opaque_token_service


def get_clock() -> SystemClock:
    return _clock


# ---------------------------------------------------------------------------
# Repository providers — the only place a use case's dependencies are wired
# to a concrete SQLAlchemy implementation
# ---------------------------------------------------------------------------


def get_project_repo(session: Session = Depends(get_db_session)) -> SqlAlchemyProjectRepository:
    return SqlAlchemyProjectRepository(session)


def get_location_repo(session: Session = Depends(get_db_session)) -> SqlAlchemyLocationRepository:
    return SqlAlchemyLocationRepository(session)


def get_spec_division_repo(
    session: Session = Depends(get_db_session),
) -> SqlAlchemySpecDivisionRepository:
    return SqlAlchemySpecDivisionRepository(session)


def get_spec_section_repo(
    session: Session = Depends(get_db_session),
) -> SqlAlchemySpecSectionRepository:
    return SqlAlchemySpecSectionRepository(session)


def get_drawing_repo(session: Session = Depends(get_db_session)) -> SqlAlchemyDrawingRepository:
    return SqlAlchemyDrawingRepository(session)


def get_drawing_version_repo(
    session: Session = Depends(get_db_session),
) -> SqlAlchemyDrawingVersionRepository:
    return SqlAlchemyDrawingVersionRepository(session)


def get_rfi_repo(session: Session = Depends(get_db_session)) -> SqlAlchemyRFIRepository:
    return SqlAlchemyRFIRepository(session)


def get_user_repo(session: Session = Depends(get_db_session)) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session)


def get_integration_user_repo(
    session: Session = Depends(get_db_session),
) -> SqlAlchemyIntegrationUserRepository:
    return SqlAlchemyIntegrationUserRepository(session)


def get_oauth_client_repo(
    session: Session = Depends(get_db_session),
) -> SqlAlchemyOAuthClientRepository:
    return SqlAlchemyOAuthClientRepository(session)


def get_oauth_token_repo(
    session: Session = Depends(get_db_session),
) -> SqlAlchemyOAuthTokenRepository:
    return SqlAlchemyOAuthTokenRepository(session)


# ---------------------------------------------------------------------------
# Use case providers
# ---------------------------------------------------------------------------


def get_list_projects(repo=Depends(get_project_repo)) -> ListProjects:
    return ListProjects(repo)


def get_get_project(repo=Depends(get_project_repo)) -> GetProject:
    return GetProject(repo)


def get_list_locations(repo=Depends(get_location_repo)) -> ListLocations:
    return ListLocations(repo)


def get_list_spec_divisions(repo=Depends(get_spec_division_repo)) -> ListSpecDivisions:
    return ListSpecDivisions(repo)


def get_list_spec_sections(repo=Depends(get_spec_section_repo)) -> ListSpecSections:
    return ListSpecSections(repo)


def get_list_drawings(repo=Depends(get_drawing_repo)) -> ListDrawings:
    return ListDrawings(repo)


def get_get_drawing(repo=Depends(get_drawing_repo)) -> GetDrawing:
    return GetDrawing(repo)


def get_list_drawing_versions(repo=Depends(get_drawing_version_repo)) -> ListDrawingVersions:
    return ListDrawingVersions(repo)


def get_get_drawing_version(repo=Depends(get_drawing_version_repo)) -> GetDrawingVersion:
    return GetDrawingVersion(repo)


def get_list_rfis(repo=Depends(get_rfi_repo)) -> ListRFIs:
    return ListRFIs(repo)


def get_get_rfi(repo=Depends(get_rfi_repo)) -> GetRFI:
    return GetRFI(repo)


def get_respond_to_rfi(repo=Depends(get_rfi_repo)) -> RespondToRFI:
    return RespondToRFI(repo)


def get_close_rfi(repo=Depends(get_rfi_repo), clock=Depends(get_clock)) -> CloseRFI:
    return CloseRFI(repo, clock)


def get_login_user(
    user_repo=Depends(get_user_repo),
    hasher=Depends(get_password_hasher),
    session_tokens=Depends(get_session_token_service),
) -> LoginUser:
    return LoginUser(user_repo, hasher, session_tokens)


def get_issue_token_from_code(
    client_repo=Depends(get_oauth_client_repo),
    token_repo=Depends(get_oauth_token_repo),
    opaque_tokens=Depends(get_opaque_token_service),
    hasher=Depends(get_password_hasher),
    clock=Depends(get_clock),
) -> IssueTokenFromAuthorizationCode:
    return IssueTokenFromAuthorizationCode(client_repo, token_repo, opaque_tokens, hasher, clock)


def get_refresh_oauth_token(
    client_repo=Depends(get_oauth_client_repo),
    token_repo=Depends(get_oauth_token_repo),
    opaque_tokens=Depends(get_opaque_token_service),
    hasher=Depends(get_password_hasher),
    clock=Depends(get_clock),
) -> RefreshOAuthToken:
    return RefreshOAuthToken(client_repo, token_repo, opaque_tokens, hasher, clock)


# ---------------------------------------------------------------------------
# Acting-context resolution — the one place HTTP auth becomes a domain fact
# ---------------------------------------------------------------------------

_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class ActingContext:
    """Whoever is making this request — a human (full access to their own
    project, gated by role) or an integration client (gated by its stored
    PermissionScope). Kept as one union type so every router asks exactly one
    question ("can this actor see this resource type?") regardless of which
    of the two auth surfaces answered it.
    """

    kind: str  # "human" | "integration"
    project_id: int
    user_id: int | None = None
    role: str | None = None
    permission_scope: PermissionScope | None = None

    def can_see(self, resource_type: str) -> bool:
        if self.kind == "human":
            return True
        assert self.permission_scope is not None
        return self.permission_scope.grants(resource_type)


def get_acting_context(
    res_session: str | None = Cookie(default=None),
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    session_tokens: SessionTokenServicePort = Depends(get_session_token_service),
    token_repo: SqlAlchemyOAuthTokenRepository = Depends(get_oauth_token_repo),
    client_repo: SqlAlchemyOAuthClientRepository = Depends(get_oauth_client_repo),
    integration_repo: SqlAlchemyIntegrationUserRepository = Depends(get_integration_user_repo),
    clock: SystemClock = Depends(get_clock),
) -> ActingContext:
    if res_session is not None:
        try:
            claims = session_tokens.verify(res_session)
        except Unauthorized as exc:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
        return ActingContext(
            kind="human", project_id=claims.project_id, user_id=claims.user_id, role=claims.role
        )

    if credentials is not None:
        token = token_repo.get_by_access_token(credentials.credentials)
        if token is None or token.expires_at < clock.now():
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired access token")
        client = client_repo.get(token.client_id)
        integration_user = integration_repo.get(client.integration_user_id)
        return ActingContext(
            kind="integration",
            project_id=integration_user.project_id,
            permission_scope=integration_user.permission_scope,
        )

    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No session cookie or bearer token provided")
