from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.deps import (
    ActingContext,
    get_acting_context,
    get_cancel_commitment,
    get_create_commitment,
    get_get_commitment,
    get_list_commitments,
    get_relieve_commitment,
    require_csrf_token,
)
from api.pagination import PageParams, paginate
from api.schemas.commitment import CommitmentOut, CreateCommitmentRequest, RelieveCommitmentRequest
from api.schemas.org_scope import OrgScopeOut
from application.exceptions import NotFound
from application.use_cases.commitment_use_cases import (
    CancelCommitment,
    CreateCommitment,
    GetCommitment,
    ListCommitments,
    RelieveCommitment,
)
from domain.exceptions import DomainRuleViolation, InvalidTransition
from domain.value_objects import OrgScope

router = APIRouter(prefix="/commitments", tags=["commitments"])


def _out(c) -> CommitmentOut:
    return CommitmentOut(
        id=c.id,
        source_type=c.source_type,
        cost_code_id=c.cost_code_id,
        po_id=c.po_id,
        committed_amount=c.committed_amount,
        relieved_amount=c.relieved_amount,
        open_amount=c.open_amount,
        currency=c.currency,
        status=c.status,
        org_scope=OrgScopeOut(**vars(c.org_scope)),
    )


@router.get("", response_model=list[CommitmentOut])
def list_commitments(
    response: Response,
    use_case: ListCommitments = Depends(get_list_commitments),
    ctx: ActingContext = Depends(get_acting_context),
    page_params: PageParams = Depends(),
) -> list[CommitmentOut]:
    if not ctx.can_see("commitments"):
        response.headers["X-Total"] = "0"
        return []
    page, total = paginate(use_case.execute(), page_params)
    response.headers["X-Total"] = str(total)
    return [_out(c) for c in page]


@router.get("/{commitment_id}", response_model=CommitmentOut)
def get_commitment(
    commitment_id: int,
    use_case: GetCommitment = Depends(get_get_commitment),
    ctx: ActingContext = Depends(get_acting_context),
) -> CommitmentOut:
    ctx.require_scope("commitments")
    try:
        return _out(use_case.execute(commitment_id))
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.post("", response_model=CommitmentOut, status_code=status.HTTP_201_CREATED)
def create_commitment(
    body: CreateCommitmentRequest,
    use_case: CreateCommitment = Depends(get_create_commitment),
    ctx: ActingContext = Depends(get_acting_context),
    _csrf: None = Depends(require_csrf_token),
) -> CommitmentOut:
    ctx.require_scope("commitments")
    return _out(
        use_case.execute(
            source_type=body.source_type,
            cost_code_id=body.cost_code_id,
            committed_amount=body.committed_amount,
            currency=body.currency,
            po_id=body.po_id,
            org_scope=OrgScope(company_code=body.company_code, plant=body.plant),
        )
    )


@router.patch("/{commitment_id}/relieve", response_model=CommitmentOut)
def relieve_commitment(
    commitment_id: int,
    body: RelieveCommitmentRequest,
    use_case: RelieveCommitment = Depends(get_relieve_commitment),
    ctx: ActingContext = Depends(get_acting_context),
    _csrf: None = Depends(require_csrf_token),
) -> CommitmentOut:
    ctx.require_scope("commitments")
    try:
        return _out(use_case.execute(commitment_id, body.amount))
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except (InvalidTransition, DomainRuleViolation) as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.patch("/{commitment_id}/cancel", response_model=CommitmentOut)
def cancel_commitment(
    commitment_id: int,
    use_case: CancelCommitment = Depends(get_cancel_commitment),
    ctx: ActingContext = Depends(get_acting_context),
    _csrf: None = Depends(require_csrf_token),
) -> CommitmentOut:
    ctx.require_scope("commitments")
    try:
        return _out(use_case.execute(commitment_id))
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidTransition as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
