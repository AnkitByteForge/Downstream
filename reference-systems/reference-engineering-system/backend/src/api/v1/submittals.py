from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.deps import (
    ActingContext,
    get_acting_context,
    get_clock,
    get_get_submittal,
    get_get_submittal_revision,
    get_list_submittal_revisions,
    get_list_submittals,
    get_record_submittal_disposition,
    get_submittal_review_status_repo,
)
from api.pagination import PageParams, paginate
from api.schemas.submittal import (
    RecordSubmittalDispositionIn,
    SubmittalOut,
    SubmittalRevisionOut,
)
from application.exceptions import NotFound
from application.long_lead import is_long_lead
from application.use_cases.submittal_use_cases import (
    GetSubmittal,
    GetSubmittalRevision,
    ListSubmittalRevisions,
    ListSubmittals,
    RecordSubmittalDisposition,
)
from domain.entities.submittal import Submittal, SubmittalRevision
from domain.exceptions import DomainRuleViolation, InvalidTransition

router = APIRouter(tags=["submittals"])


def _submittal_out(s: Submittal, clock) -> SubmittalOut:
    today = clock.now().date()
    return SubmittalOut(
        id=s.id,
        project_id=s.project_id,
        number=s.number,
        spec_section_id=s.spec_section_id,
        package_id=s.package_id,
        vendor_id=s.vendor_id,
        commitment_id=s.commitment_id,
        submittal_type=s.submittal_type,
        category=s.category,
        lead_time_days=s.lead_time_days,
        required_on_site_date=s.required_on_site_date,
        is_long_lead=is_long_lead(s.lead_time_days, s.required_on_site_date, today),
    )


def _revision_out(r: SubmittalRevision, review_status_repo) -> SubmittalRevisionOut:
    status_row = review_status_repo.get(r.review_status_id)
    return SubmittalRevisionOut(
        id=r.id,
        submittal_id=r.submittal_id,
        rev_label=r.rev_label,
        review_status_id=r.review_status_id,
        review_status_code=status_row.code if status_row else "",
        review_status_label=status_row.label if status_row else "",
        gates_procurement=status_row.gates_procurement if status_row else False,
        ball_in_court=str(r.ball_in_court),
        equipment_tag=r.equipment_tag,
        manufacturer=r.manufacturer,
        model=r.model,
        capacity_value=r.capacity_value,
        capacity_unit=r.capacity_unit,
        submitted_at=r.submitted_at,
        disposed_by_user_id=r.disposed_by_user_id,
        disposition_at=r.disposition_at,
        drawing_version_ids=r.drawing_version_ids,
        location_ids=r.location_ids,
    )


@router.get("/projects/{project_id}/submittals", response_model=list[SubmittalOut])
def list_submittals(
    project_id: int,
    response: Response,
    use_case: ListSubmittals = Depends(get_list_submittals),
    ctx: ActingContext = Depends(get_acting_context),
    page_params: PageParams = Depends(),
    clock=Depends(get_clock),
) -> list[SubmittalOut]:
    if not ctx.can_see("submittals"):
        response.headers["X-Total"] = "0"
        return []
    page, total = paginate(use_case.execute(project_id), page_params)
    response.headers["X-Total"] = str(total)
    return [_submittal_out(s, clock) for s in page]


@router.get("/projects/{project_id}/submittals/{submittal_id}", response_model=SubmittalOut)
def get_submittal(
    project_id: int,
    submittal_id: int,
    use_case: GetSubmittal = Depends(get_get_submittal),
    ctx: ActingContext = Depends(get_acting_context),
    clock=Depends(get_clock),
) -> SubmittalOut:
    ctx.require_scope("submittals")
    try:
        return _submittal_out(use_case.execute(submittal_id), clock)
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.get(
    "/projects/{project_id}/submittals/{submittal_id}/revisions",
    response_model=list[SubmittalRevisionOut],
)
def list_submittal_revisions(
    project_id: int,
    submittal_id: int,
    use_case: ListSubmittalRevisions = Depends(get_list_submittal_revisions),
    ctx: ActingContext = Depends(get_acting_context),
    review_status_repo=Depends(get_submittal_review_status_repo),
) -> list[SubmittalRevisionOut]:
    if not ctx.can_see("submittals"):
        return []
    return [_revision_out(r, review_status_repo) for r in use_case.execute(submittal_id)]


@router.get(
    "/projects/{project_id}/submittals/revisions/{revision_id}",
    response_model=SubmittalRevisionOut,
)
def get_submittal_revision(
    project_id: int,
    revision_id: int,
    use_case: GetSubmittalRevision = Depends(get_get_submittal_revision),
    ctx: ActingContext = Depends(get_acting_context),
    review_status_repo=Depends(get_submittal_review_status_repo),
) -> SubmittalRevisionOut:
    ctx.require_scope("submittals")
    try:
        return _revision_out(use_case.execute(revision_id), review_status_repo)
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.patch(
    "/projects/{project_id}/submittals/{submittal_id}/revisions/{revision_id}/disposition",
    response_model=SubmittalRevisionOut,
)
def record_submittal_disposition(
    project_id: int,
    submittal_id: int,
    revision_id: int,
    body: RecordSubmittalDispositionIn,
    use_case: RecordSubmittalDisposition = Depends(get_record_submittal_disposition),
    ctx: ActingContext = Depends(get_acting_context),
    review_status_repo=Depends(get_submittal_review_status_repo),
) -> SubmittalRevisionOut:
    """Always fires a webhook (resource_name="submittals", event_type="update")
    on any disposition change — mirrors CloseRFI's dispatch pattern exactly."""
    ctx.require_scope("submittals")
    try:
        revision = use_case.execute(revision_id, body.review_status_code, body.disposed_by_user_id)
        return _revision_out(revision, review_status_repo)
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except (InvalidTransition, DomainRuleViolation) as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
