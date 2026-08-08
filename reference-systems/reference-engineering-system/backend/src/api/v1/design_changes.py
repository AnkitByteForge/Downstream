from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.deps import (
    ActingContext,
    ensure_resource_in_project,
    get_acting_context,
    get_acknowledge_design_change,
    get_get_design_change,
    get_issue_design_change,
    get_list_design_changes,
    get_void_design_change,
)
from api.pagination import PageParams, paginate
from api.schemas.design_change import DesignChangeOut
from application.exceptions import NotFound
from application.use_cases.design_change_use_cases import (
    AcknowledgeDesignChange,
    GetDesignChange,
    IssueDesignChange,
    ListDesignChanges,
    VoidDesignChange,
)
from domain.entities.design_change import DesignChange
from domain.exceptions import DomainRuleViolation, InvalidTransition

router = APIRouter(tags=["design_changes"])


def _out(change: DesignChange) -> DesignChangeOut:
    return DesignChangeOut(
        id=change.id,
        project_id=change.project_id,
        number=change.number,
        display_number=change.display_number,
        type=change.type,
        status=change.status,
        change_reason=change.change_reason,
        discipline_code=change.discipline_code,
        source_rfi_id=change.source_rfi_id,
        ball_in_court=str(change.ball_in_court),
        affected_drawing_version_ids=change.affected_drawing_version_ids,
        affected_spec_section_ids=change.affected_spec_section_ids,
        location_ids=change.location_ids,
        superseded_by_id=change.superseded_by_id,
        issued_at=change.issued_at,
        acknowledged_at=change.acknowledged_at,
        voided_at=change.voided_at,
    )


@router.get("/projects/{project_id}/design_changes", response_model=list[DesignChangeOut])
def list_design_changes(
    project_id: int,
    response: Response,
    use_case: ListDesignChanges = Depends(get_list_design_changes),
    ctx: ActingContext = Depends(get_acting_context),
    page_params: PageParams = Depends(),
) -> list[DesignChangeOut]:
    ctx.require_project(project_id)
    if not ctx.can_see("design_changes"):
        response.headers["X-Total"] = "0"
        return []
    page, total = paginate(use_case.execute(project_id), page_params)
    response.headers["X-Total"] = str(total)
    return [_out(c) for c in page]


@router.get(
    "/projects/{project_id}/design_changes/{design_change_id}",
    response_model=DesignChangeOut,
)
def get_design_change(
    project_id: int,
    design_change_id: int,
    use_case: GetDesignChange = Depends(get_get_design_change),
    ctx: ActingContext = Depends(get_acting_context),
) -> DesignChangeOut:
    ctx.require_project(project_id)
    ctx.require_scope("design_changes")
    try:
        change = use_case.execute(design_change_id)
        ensure_resource_in_project(change.project_id, project_id)
        return _out(change)
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.patch(
    "/projects/{project_id}/design_changes/{design_change_id}/issue",
    response_model=DesignChangeOut,
)
def issue_design_change(
    project_id: int,
    design_change_id: int,
    use_case: IssueDesignChange = Depends(get_issue_design_change),
    get_use_case: GetDesignChange = Depends(get_get_design_change),
    ctx: ActingContext = Depends(get_acting_context),
) -> DesignChangeOut:
    ctx.require_project(project_id)
    ctx.require_scope("design_changes")
    try:
        existing = get_use_case.execute(design_change_id)
        ensure_resource_in_project(existing.project_id, project_id)
        return _out(use_case.execute(design_change_id))
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except (InvalidTransition, DomainRuleViolation) as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.patch(
    "/projects/{project_id}/design_changes/{design_change_id}/acknowledge",
    response_model=DesignChangeOut,
)
def acknowledge_design_change(
    project_id: int,
    design_change_id: int,
    use_case: AcknowledgeDesignChange = Depends(get_acknowledge_design_change),
    get_use_case: GetDesignChange = Depends(get_get_design_change),
    ctx: ActingContext = Depends(get_acting_context),
) -> DesignChangeOut:
    ctx.require_project(project_id)
    ctx.require_scope("design_changes")
    try:
        existing = get_use_case.execute(design_change_id)
        ensure_resource_in_project(existing.project_id, project_id)
        return _out(use_case.execute(design_change_id))
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except (InvalidTransition, DomainRuleViolation) as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.patch(
    "/projects/{project_id}/design_changes/{design_change_id}/void",
    response_model=DesignChangeOut,
)
def void_design_change(
    project_id: int,
    design_change_id: int,
    use_case: VoidDesignChange = Depends(get_void_design_change),
    get_use_case: GetDesignChange = Depends(get_get_design_change),
    ctx: ActingContext = Depends(get_acting_context),
) -> DesignChangeOut:
    ctx.require_project(project_id)
    ctx.require_scope("design_changes")
    try:
        existing = get_use_case.execute(design_change_id)
        ensure_resource_in_project(existing.project_id, project_id)
        return _out(use_case.execute(design_change_id))
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except (InvalidTransition, DomainRuleViolation) as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
