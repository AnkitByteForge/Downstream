from __future__ import annotations

from dataclasses import dataclass

from datetime import timedelta

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from application.exceptions import Unauthorized
from application.ports import PasswordHasherPort, SessionTokenServicePort, WebhookDispatcherPort
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
from application.use_cases.webhook_use_cases import (
    ListActivity,
    ListWebhookSubscriptions,
    RegisterWebhookSubscription,
)
from domain.value_objects import PermissionScope
from infrastructure.auth.jwt_service import JwtSessionTokenService
from infrastructure.auth.opaque_token_service import SecureOpaqueTokenService
from infrastructure.auth.password_hashing import Pbkdf2PasswordHasher
from infrastructure.clock import SystemClock
from infrastructure.config import Settings, settings
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
from infrastructure.persistence.repositories.sqlalchemy_webhook_repository import (
    SqlAlchemyWebhookDeliveryRepository,
    SqlAlchemyWebhookSubscriptionRepository,
)
from infrastructure.rate_limit.store import RateLimitStore
from infrastructure.webhooks.dispatcher import HttpWebhookDispatcher

# ---------------------------------------------------------------------------
# Infrastructure singletons (stateless adapters — safe to share across requests)
# ---------------------------------------------------------------------------

_password_hasher = Pbkdf2PasswordHasher()
_session_token_service = JwtSessionTokenService(settings)
_opaque_token_service = SecureOpaqueTokenService()
_clock = SystemClock()
_webhook_dispatcher = HttpWebhookDispatcher(timeout_seconds=settings.webhook_timeout_seconds)


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


def get_webhook_dispatcher() -> WebhookDispatcherPort:
    return _webhook_dispatcher


def get_settings() -> Settings:
    return settings


# ---------------------------------------------------------------------------
# Repository providers — the only place a use case's dependencies are wired
# to a concrete SQLAlchemy implementation. Built from one factory so adding
# a repository is a one-liner instead of a five-line copy-paste.
# ---------------------------------------------------------------------------


def _repo_provider(repo_cls):
    def provider(session: Session = Depends(get_db_session)):
        return repo_cls(session)

    return provider


get_project_repo = _repo_provider(SqlAlchemyProjectRepository)
get_location_repo = _repo_provider(SqlAlchemyLocationRepository)
get_spec_division_repo = _repo_provider(SqlAlchemySpecDivisionRepository)
get_spec_section_repo = _repo_provider(SqlAlchemySpecSectionRepository)
get_drawing_repo = _repo_provider(SqlAlchemyDrawingRepository)
get_drawing_version_repo = _repo_provider(SqlAlchemyDrawingVersionRepository)
get_rfi_repo = _repo_provider(SqlAlchemyRFIRepository)
get_user_repo = _repo_provider(SqlAlchemyUserRepository)
get_integration_user_repo = _repo_provider(SqlAlchemyIntegrationUserRepository)
get_oauth_client_repo = _repo_provider(SqlAlchemyOAuthClientRepository)
get_oauth_token_repo = _repo_provider(SqlAlchemyOAuthTokenRepository)
get_webhook_subscription_repo = _repo_provider(SqlAlchemyWebhookSubscriptionRepository)
get_webhook_delivery_repo = _repo_provider(SqlAlchemyWebhookDeliveryRepository)
get_rate_limit_store = _repo_provider(RateLimitStore)


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


def get_close_rfi(
    repo=Depends(get_rfi_repo),
    clock=Depends(get_clock),
    webhook_subscription_repo=Depends(get_webhook_subscription_repo),
    webhook_delivery_repo=Depends(get_webhook_delivery_repo),
    webhook_dispatcher=Depends(get_webhook_dispatcher),
) -> CloseRFI:
    return CloseRFI(repo, clock, webhook_subscription_repo, webhook_delivery_repo, webhook_dispatcher)


def get_register_webhook_subscription(
    repo=Depends(get_webhook_subscription_repo),
) -> RegisterWebhookSubscription:
    return RegisterWebhookSubscription(repo)


def get_list_webhook_subscriptions(
    repo=Depends(get_webhook_subscription_repo),
) -> ListWebhookSubscriptions:
    return ListWebhookSubscriptions(repo)


def get_list_activity(repo=Depends(get_webhook_delivery_repo)) -> ListActivity:
    return ListActivity(repo)


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

    def require_scope(self, resource_type: str) -> None:
        """For single-resource GETs: an under-scoped credential gets a 404,
        matching real Procore's behavior of simply not exposing the resource
        rather than confirming its existence with a 403 (docs/04)."""
        if not self.can_see(resource_type):
            raise HTTPException(status.HTTP_404_NOT_FOUND)


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


# ---------------------------------------------------------------------------
# Rate limiting — applies only to OAuth2 integration-client traffic
# (docs/04's per-client_id budget); human sessions are never throttled here.
# Deliberately independent of get_acting_context (a second, cheap token
# lookup) so it stays a swappable, separately-testable concern rather than
# entangled with authorization.
# ---------------------------------------------------------------------------


def enforce_rate_limit(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    token_repo: SqlAlchemyOAuthTokenRepository = Depends(get_oauth_token_repo),
    store: RateLimitStore = Depends(get_rate_limit_store),
    clock: SystemClock = Depends(get_clock),
    cfg: Settings = Depends(get_settings),
) -> None:
    if credentials is None:
        return

    token = token_repo.get_by_access_token(credentials.credentials)
    if token is None:
        return  # an invalid/unknown token is get_acting_context's problem, not rate limiting's

    result = store.check_and_record(
        client_id=token.client_id,
        now=clock.now(),
        window=timedelta(seconds=cfg.rate_limit_window_seconds),
        max_requests=cfg.rate_limit_max_requests,
    )
    if not result.allowed:
        # Headers must go through HTTPException's own `headers` param — a
        # Response object mutated inside a dependency is discarded once an
        # exception is raised, FastAPI builds the error response from scratch.
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Rate limit exceeded",
            headers={"Retry-After": str(result.retry_after_seconds)},
        )
