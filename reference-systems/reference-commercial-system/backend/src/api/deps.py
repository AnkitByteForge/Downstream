from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from fastapi import Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from application.exceptions import Unauthorized
from application.ports import ClockPort, PasswordHasherPort, SessionTokenServicePort
from application.use_cases.auth_use_cases import LoginUser
from application.use_cases.commitment_use_cases import (
    CancelCommitment,
    CreateCommitment,
    GetCommitment,
    ListCommitments,
    RelieveCommitment,
)
from application.use_cases.contract_use_cases import CreateContract, GetContract, ListContracts
from application.use_cases.cost_code_use_cases import CreateCostCode, GetCostCode, ListCostCodes
from application.use_cases.oauth_use_cases import IssueTokenFromClientCredentials
from application.use_cases.po_line_use_cases import (
    CreatePOLine,
    GetPOLine,
    InstallPOLine,
    IssuePOLine,
    ListPOLines,
    ShipPOLine,
    StartFabricationPOLine,
)
from application.use_cases.po_schedule_line_use_cases import (
    CreatePOScheduleLine,
    GetPOScheduleLine,
    ListPOScheduleLines,
)
from application.use_cases.purchase_order_use_cases import (
    AcknowledgePurchaseOrder,
    AmendPurchaseOrder,
    ApprovePurchaseOrder,
    ApprovePurchaseOrderAmendment,
    CancelPurchaseOrder,
    ClosePurchaseOrder,
    CreatePurchaseOrder,
    FinallyClosePurchaseOrder,
    GetPurchaseOrder,
    GetPurchaseOrderByNumber,
    HoldPurchaseOrder,
    ListPurchaseOrders,
    ReleaseHoldPurchaseOrder,
    RejectPurchaseOrder,
    SubmitPurchaseOrderForApproval,
    WithdrawPurchaseOrder,
)
from application.use_cases.vendor_use_cases import (
    AddVendorScopeView,
    ApproveVendor,
    BlacklistVendor,
    CreateVendor,
    GetVendor,
    ListVendors,
    ListVendorScopeViews,
    PrequalifyVendor,
    SuspendVendor,
)
from domain.value_objects import PermissionScope
from infrastructure.auth.jwt_service import JwtSessionTokenService
from infrastructure.auth.opaque_token_service import SecureOpaqueTokenService
from infrastructure.auth.password_hashing import Pbkdf2PasswordHasher
from infrastructure.clock import SystemClock
from infrastructure.config import Settings, settings
from infrastructure.csrf.store import CsrfTokenStore
from infrastructure.persistence.db import get_session
from infrastructure.persistence.repositories.sqlalchemy_commitment_repository import (
    SqlAlchemyCommitmentRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_contract_repository import (
    SqlAlchemyContractRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_cost_code_repository import (
    SqlAlchemyCostCodeRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_purchase_order_repository import (
    SqlAlchemyPOLineRepository,
    SqlAlchemyPOScheduleLineRepository,
    SqlAlchemyPurchaseOrderRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SqlAlchemyOAuthClientRepository,
    SqlAlchemyOAuthTokenRepository,
    SqlAlchemyUserRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_vendor_repository import (
    SqlAlchemyVendorRepository,
    SqlAlchemyVendorScopeViewRepository,
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


def get_clock() -> ClockPort:
    return _clock


def get_settings() -> Settings:
    return settings


# ---------------------------------------------------------------------------
# Repository providers
# ---------------------------------------------------------------------------


def _repo_provider(repo_cls):
    def provider(session: Session = Depends(get_db_session)):
        return repo_cls(session)

    return provider


get_vendor_repo = _repo_provider(SqlAlchemyVendorRepository)
get_vendor_scope_view_repo = _repo_provider(SqlAlchemyVendorScopeViewRepository)
get_cost_code_repo = _repo_provider(SqlAlchemyCostCodeRepository)
get_contract_repo = _repo_provider(SqlAlchemyContractRepository)
get_commitment_repo = _repo_provider(SqlAlchemyCommitmentRepository)
get_purchase_order_repo = _repo_provider(SqlAlchemyPurchaseOrderRepository)
get_po_line_repo = _repo_provider(SqlAlchemyPOLineRepository)
get_po_schedule_line_repo = _repo_provider(SqlAlchemyPOScheduleLineRepository)
get_user_repo = _repo_provider(SqlAlchemyUserRepository)
get_oauth_client_repo = _repo_provider(SqlAlchemyOAuthClientRepository)
get_oauth_token_repo = _repo_provider(SqlAlchemyOAuthTokenRepository)
get_csrf_store = _repo_provider(CsrfTokenStore)


# ---------------------------------------------------------------------------
# Use case providers
# ---------------------------------------------------------------------------

# --- Vendor ---


def get_create_vendor(repo=Depends(get_vendor_repo)) -> CreateVendor:
    return CreateVendor(repo)


def get_list_vendors(repo=Depends(get_vendor_repo)) -> ListVendors:
    return ListVendors(repo)


def get_get_vendor(repo=Depends(get_vendor_repo)) -> GetVendor:
    return GetVendor(repo)


def get_prequalify_vendor(repo=Depends(get_vendor_repo)) -> PrequalifyVendor:
    return PrequalifyVendor(repo)


def get_approve_vendor(repo=Depends(get_vendor_repo)) -> ApproveVendor:
    return ApproveVendor(repo)


def get_suspend_vendor(repo=Depends(get_vendor_repo)) -> SuspendVendor:
    return SuspendVendor(repo)


def get_blacklist_vendor(repo=Depends(get_vendor_repo)) -> BlacklistVendor:
    return BlacklistVendor(repo)


def get_add_vendor_scope_view(repo=Depends(get_vendor_scope_view_repo)) -> AddVendorScopeView:
    return AddVendorScopeView(repo)


def get_list_vendor_scope_views(repo=Depends(get_vendor_scope_view_repo)) -> ListVendorScopeViews:
    return ListVendorScopeViews(repo)


# --- CostCode ---


def get_create_cost_code(repo=Depends(get_cost_code_repo)) -> CreateCostCode:
    return CreateCostCode(repo)


def get_list_cost_codes(repo=Depends(get_cost_code_repo)) -> ListCostCodes:
    return ListCostCodes(repo)


def get_get_cost_code(repo=Depends(get_cost_code_repo)) -> GetCostCode:
    return GetCostCode(repo)


# --- Contract ---


def get_create_contract(repo=Depends(get_contract_repo)) -> CreateContract:
    return CreateContract(repo)


def get_list_contracts(repo=Depends(get_contract_repo)) -> ListContracts:
    return ListContracts(repo)


def get_get_contract(repo=Depends(get_contract_repo)) -> GetContract:
    return GetContract(repo)


# --- Commitment ---


def get_create_commitment(repo=Depends(get_commitment_repo)) -> CreateCommitment:
    return CreateCommitment(repo)


def get_list_commitments(repo=Depends(get_commitment_repo)) -> ListCommitments:
    return ListCommitments(repo)


def get_get_commitment(repo=Depends(get_commitment_repo)) -> GetCommitment:
    return GetCommitment(repo)


def get_relieve_commitment(repo=Depends(get_commitment_repo)) -> RelieveCommitment:
    return RelieveCommitment(repo)


def get_cancel_commitment(repo=Depends(get_commitment_repo)) -> CancelCommitment:
    return CancelCommitment(repo)

# --- PurchaseOrder ---


def get_create_purchase_order(repo=Depends(get_purchase_order_repo)) -> CreatePurchaseOrder:
    return CreatePurchaseOrder(repo)


def get_list_purchase_orders(repo=Depends(get_purchase_order_repo)) -> ListPurchaseOrders:
    return ListPurchaseOrders(repo)


def get_get_purchase_order(repo=Depends(get_purchase_order_repo)) -> GetPurchaseOrder:
    return GetPurchaseOrder(repo)


def get_get_purchase_order_by_number(repo=Depends(get_purchase_order_repo)) -> GetPurchaseOrderByNumber:
    return GetPurchaseOrderByNumber(repo)


def get_submit_po_for_approval(
    repo=Depends(get_purchase_order_repo), clock=Depends(get_clock)
) -> SubmitPurchaseOrderForApproval:
    return SubmitPurchaseOrderForApproval(repo, clock)


def get_approve_po(repo=Depends(get_purchase_order_repo), clock=Depends(get_clock)) -> ApprovePurchaseOrder:
    return ApprovePurchaseOrder(repo, clock)


def get_reject_po(repo=Depends(get_purchase_order_repo), clock=Depends(get_clock)) -> RejectPurchaseOrder:
    return RejectPurchaseOrder(repo, clock)


def get_withdraw_po(repo=Depends(get_purchase_order_repo), clock=Depends(get_clock)) -> WithdrawPurchaseOrder:
    return WithdrawPurchaseOrder(repo, clock)


def get_cancel_po(repo=Depends(get_purchase_order_repo), clock=Depends(get_clock)) -> CancelPurchaseOrder:
    return CancelPurchaseOrder(repo, clock)


def get_hold_po(repo=Depends(get_purchase_order_repo), clock=Depends(get_clock)) -> HoldPurchaseOrder:
    return HoldPurchaseOrder(repo, clock)


def get_release_hold_po(
    repo=Depends(get_purchase_order_repo), clock=Depends(get_clock)
) -> ReleaseHoldPurchaseOrder:
    return ReleaseHoldPurchaseOrder(repo, clock)


def get_amend_po(repo=Depends(get_purchase_order_repo), clock=Depends(get_clock)) -> AmendPurchaseOrder:
    return AmendPurchaseOrder(repo, clock)


def get_approve_po_amendment(
    repo=Depends(get_purchase_order_repo), clock=Depends(get_clock)
) -> ApprovePurchaseOrderAmendment:
    return ApprovePurchaseOrderAmendment(repo, clock)


def get_close_po(repo=Depends(get_purchase_order_repo), clock=Depends(get_clock)) -> ClosePurchaseOrder:
    return ClosePurchaseOrder(repo, clock)


def get_finally_close_po(
    repo=Depends(get_purchase_order_repo), clock=Depends(get_clock)
) -> FinallyClosePurchaseOrder:
    return FinallyClosePurchaseOrder(repo, clock)


def get_acknowledge_po(
    repo=Depends(get_purchase_order_repo), clock=Depends(get_clock)
) -> AcknowledgePurchaseOrder:
    return AcknowledgePurchaseOrder(repo, clock)


# --- POLine ---


def get_create_po_line(repo=Depends(get_po_line_repo)) -> CreatePOLine:
    return CreatePOLine(repo)


def get_list_po_lines(repo=Depends(get_po_line_repo)) -> ListPOLines:
    return ListPOLines(repo)


def get_get_po_line(repo=Depends(get_po_line_repo)) -> GetPOLine:
    return GetPOLine(repo)


def get_issue_po_line(repo=Depends(get_po_line_repo)) -> IssuePOLine:
    return IssuePOLine(repo)


def get_start_fabrication_po_line(repo=Depends(get_po_line_repo)) -> StartFabricationPOLine:
    return StartFabricationPOLine(repo)


def get_ship_po_line(repo=Depends(get_po_line_repo)) -> ShipPOLine:
    return ShipPOLine(repo)


def get_install_po_line(repo=Depends(get_po_line_repo)) -> InstallPOLine:
    return InstallPOLine(repo)


# --- POScheduleLine ---


def get_create_po_schedule_line(repo=Depends(get_po_schedule_line_repo)) -> CreatePOScheduleLine:
    return CreatePOScheduleLine(repo)


def get_list_po_schedule_lines(repo=Depends(get_po_schedule_line_repo)) -> ListPOScheduleLines:
    return ListPOScheduleLines(repo)


def get_get_po_schedule_line(repo=Depends(get_po_schedule_line_repo)) -> GetPOScheduleLine:
    return GetPOScheduleLine(repo)


# --- Auth / OAuth ---


def get_login_user(
    user_repo=Depends(get_user_repo),
    hasher=Depends(get_password_hasher),
    session_tokens=Depends(get_session_token_service),
) -> LoginUser:
    return LoginUser(user_repo, hasher, session_tokens)


def get_issue_token_from_client_credentials(
    client_repo=Depends(get_oauth_client_repo),
    token_repo=Depends(get_oauth_token_repo),
    opaque_tokens=Depends(get_opaque_token_service),
    hasher=Depends(get_password_hasher),
    clock=Depends(get_clock),
    cfg=Depends(get_settings),
) -> IssueTokenFromClientCredentials:
    return IssueTokenFromClientCredentials(
        client_repo,
        token_repo,
        opaque_tokens,
        hasher,
        clock,
        timedelta(minutes=cfg.oauth_access_token_expire_minutes),
    )


# ---------------------------------------------------------------------------
# Acting-context resolution — the one place HTTP auth becomes a domain fact.
# Unlike the Reference Engineering System's project_id-scoped ActingContext,
# this system has no Project entity: a human session sees across every
# OrgScope (a real procurement manager's cross-plant oversight of one
# project), and only OAuth2 integration clients are scoped — to exactly one
# company_code plus a PermissionScope — per ADR-012/the approved plan §9.
# ---------------------------------------------------------------------------

_bearer_scheme = HTTPBearer(auto_error=False)
SESSION_COOKIE_NAME = "cs_session"


@dataclass(frozen=True)
class ActingContext:
    kind: str  # "human" | "integration"
    actor_key: str  # CSRF-token binding key: "human:<user_id>" | "integration:<client_id>"
    user_id: int | None = None
    role: str | None = None
    company_code: str | None = None  # integration only
    permission_scope: PermissionScope | None = None  # integration only

    def can_see(self, resource_type: str) -> bool:
        if self.kind == "human":
            return True
        assert self.permission_scope is not None
        return self.permission_scope.grants(resource_type)

    def require_scope(self, resource_type: str) -> None:
        """Matching real Procore/SAP behavior (docs/04): an under-scoped
        credential gets a 404, not a 403 — it simply doesn't see the
        resource exists."""
        if not self.can_see(resource_type):
            raise HTTPException(status.HTTP_404_NOT_FOUND)

    def require_company_code(self, company_code: str | None) -> None:
        """Org-scope isolation (ADR-012): an integration client scoped to
        one company_code can never reach another company_code's resource
        through its own credential, even if it knows the resource id.
        Human sessions are never scoped — a real procurement manager sees
        every plant on their one project."""
        if self.kind == "human":
            return
        if self.company_code != company_code:
            raise HTTPException(status.HTTP_404_NOT_FOUND)


def get_acting_context(
    cs_session: str | None = Cookie(default=None),
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    session_tokens: SessionTokenServicePort = Depends(get_session_token_service),
    token_repo: SqlAlchemyOAuthTokenRepository = Depends(get_oauth_token_repo),
    client_repo: SqlAlchemyOAuthClientRepository = Depends(get_oauth_client_repo),
    clock: ClockPort = Depends(get_clock),
) -> ActingContext:
    if cs_session is not None:
        try:
            claims = session_tokens.verify(cs_session)
        except Unauthorized as exc:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
        return ActingContext(
            kind="human", actor_key=f"human:{claims.user_id}", user_id=claims.user_id, role=claims.role
        )

    if credentials is not None:
        token = token_repo.get_by_access_token(credentials.credentials)
        if token is None or token.expires_at < clock.now():
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired access token")
        client = client_repo.get_by_client_id(token.client_id)
        assert client is not None
        return ActingContext(
            kind="integration",
            actor_key=f"integration:{client.client_id}",
            company_code=client.company_code,
            permission_scope=client.permission_scope,
        )

    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No session cookie or bearer token provided")


# ---------------------------------------------------------------------------
# CSRF ceremony (docs/04, docs/05 Phase 12.2). Applied uniformly across the
# whole /rest/v1 surface: `issue_csrf_if_requested` fires only when a
# caller sends `X-CSRF-Token: fetch` on a GET (real SAP behavior — issuing
# is harmless on any route, it simply does nothing unless asked); every
# mutating route separately depends on `require_csrf_token`.
# ---------------------------------------------------------------------------


def issue_csrf_if_requested(
    request: Request,
    response: Response,
    ctx: ActingContext = Depends(get_acting_context),
    csrf_store: CsrfTokenStore = Depends(get_csrf_store),
    clock: ClockPort = Depends(get_clock),
    cfg: Settings = Depends(get_settings),
) -> None:
    if request.headers.get("X-CSRF-Token") == "fetch":
        token = csrf_store.issue(
            ctx.actor_key, clock.now(), timedelta(minutes=cfg.csrf_token_expire_minutes)
        )
        response.headers["X-CSRF-Token"] = token


def require_csrf_token(
    request: Request,
    ctx: ActingContext = Depends(get_acting_context),
    csrf_store: CsrfTokenStore = Depends(get_csrf_store),
    clock: ClockPort = Depends(get_clock),
) -> None:
    token = request.headers.get("X-CSRF-Token")
    if not token or not csrf_store.validate_and_consume(ctx.actor_key, token, clock.now()):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Missing or invalid X-CSRF-Token")
