from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.deps import (
    ActingContext,
    ensure_resource_in_project,
    get_acting_context,
    get_close_rfi,
    get_get_rfi,
    get_list_rfis,
    get_respond_to_rfi,
)
from api.pagination import PageParams, paginate
from api.schemas.rfi import CloseRFIIn, RFIOut, RespondToRFIIn
from application.exceptions import NotFound
from application.use_cases.rfi_use_cases import CloseRFI, GetRFI, ListRFIs, RespondToRFI
from domain.entities import RFI
from domain.exceptions import DomainRuleViolation, InvalidTransition

router = APIRouter(tags=["rfis"])


def _rfi_out(rfi: RFI) -> RFIOut:
    return RFIOut(
        id=rfi.id,
        project_id=rfi.project_id,
        number=rfi.number,
        display_number=rfi.display_number,
        subject=rfi.subject,
        question=rfi.question,
        response=rfi.response,
        status=rfi.status,
        ball_in_court=str(rfi.ball_in_court),
        cost_impact_flag=rfi.cost_impact_flag,
        cost_code=rfi.cost_code,
        discipline_code=rfi.discipline_code,
        spawned_change_id=rfi.spawned_change_id,
        raw_document_ref=rfi.raw_document_ref,
        drawing_version_ids=rfi.drawing_version_ids,
        spec_section_ids=rfi.spec_section_ids,
        location_ids=rfi.location_ids,
        closed_at=rfi.closed_at,
    )


@router.get("/projects/{project_id}/rfis", response_model=list[RFIOut])
def list_rfis(
    project_id: int,
    response: Response,
    use_case: ListRFIs = Depends(get_list_rfis),
    ctx: ActingContext = Depends(get_acting_context),
    page_params: PageParams = Depends(),
) -> list[RFIOut]:
    ctx.require_project(project_id)
    if not ctx.can_see("rfis"):
        response.headers["X-Total"] = "0"
        return []
    page, total = paginate(use_case.execute(project_id), page_params)
    response.headers["X-Total"] = str(total)
    return [_rfi_out(r) for r in page]


@router.get("/projects/{project_id}/rfis/{rfi_id}", response_model=RFIOut)
def get_rfi(
    project_id: int,
    rfi_id: int,
    use_case: GetRFI = Depends(get_get_rfi),
    ctx: ActingContext = Depends(get_acting_context),
) -> RFIOut:
    ctx.require_project(project_id)
    ctx.require_scope("rfis")
    try:
        rfi = use_case.execute(rfi_id)
        ensure_resource_in_project(rfi.project_id, project_id)
        return _rfi_out(rfi)
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.patch("/projects/{project_id}/rfis/{rfi_id}/respond", response_model=RFIOut)
def respond_to_rfi(
    project_id: int,
    rfi_id: int,
    body: RespondToRFIIn,
    use_case: RespondToRFI = Depends(get_respond_to_rfi),
    get_use_case: GetRFI = Depends(get_get_rfi),
    ctx: ActingContext = Depends(get_acting_context),
) -> RFIOut:
    ctx.require_project(project_id)
    ctx.require_scope("rfis")
    try:
        # Confirm the RFI belongs to the requested project before mutating it,
        # so a caller can never change another project's record via their own
        # project path.
        existing = get_use_case.execute(rfi_id)
        ensure_resource_in_project(existing.project_id, project_id)
        return _rfi_out(use_case.execute(rfi_id, body.response_text, body.manager_user_id))
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except (InvalidTransition, DomainRuleViolation) as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.patch("/projects/{project_id}/rfis/{rfi_id}/close", response_model=RFIOut)
def close_rfi(
    project_id: int,
    rfi_id: int,
    body: CloseRFIIn,
    use_case: CloseRFI = Depends(get_close_rfi),
    get_use_case: GetRFI = Depends(get_get_rfi),
    ctx: ActingContext = Depends(get_acting_context),
) -> RFIOut:
    """The transition the entire Reference Execution Trace begins from
    (Phase 0). Thin webhook dispatch on this transition is RES-2 scope."""
    ctx.require_project(project_id)
    ctx.require_scope("rfis")
    try:
        existing = get_use_case.execute(rfi_id)
        ensure_resource_in_project(existing.project_id, project_id)
        return _rfi_out(use_case.execute(rfi_id, body.response_text))
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except (InvalidTransition, DomainRuleViolation) as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
