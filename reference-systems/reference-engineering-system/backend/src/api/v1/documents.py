from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.deps import (
    ActingContext,
    ensure_resource_in_project,
    get_acting_context,
    get_create_drawing,
    get_create_drawing_version,
    get_get_drawing,
    get_get_drawing_version,
    get_issue_drawing_version,
    get_list_drawing_versions,
    get_list_drawings,
)
from api.pagination import PageParams, paginate
from api.schemas.drawing import (
    CreateDrawingIn,
    CreateDrawingVersionIn,
    DrawingOut,
    DrawingVersionOut,
    RevisionCloudOut,
)
from application.exceptions import NotFound
from application.use_cases.drawing_use_cases import (
    CreateDrawing,
    CreateDrawingVersion,
    GetDrawing,
    GetDrawingVersion,
    IssueDrawingVersion,
    ListDrawings,
    ListDrawingVersions,
)
from domain.exceptions import InvalidTransition
from domain.value_objects import RevisionCloud

router = APIRouter(tags=["documents"])


def _version_out(v) -> DrawingVersionOut:
    return DrawingVersionOut(
        id=v.id,
        drawing_id=v.drawing_id,
        revision_label=v.revision_label,
        issuance_date=v.issuance_date,
        status=v.status,
        discipline_code=v.discipline_code,
        superseded_by_id=v.superseded_by_id,
        revision_clouds=[RevisionCloudOut(**vars(c)) for c in v.revision_clouds],
        location_ids=v.location_ids,
    )


@router.get("/projects/{project_id}/documents", response_model=list[DrawingOut])
def list_documents(
    project_id: int,
    response: Response,
    use_case: ListDrawings = Depends(get_list_drawings),
    ctx: ActingContext = Depends(get_acting_context),
    page_params: PageParams = Depends(),
) -> list[DrawingOut]:
    ctx.require_project(project_id)
    if not ctx.can_see("documents"):
        response.headers["X-Total"] = "0"
        return []
    page, total = paginate(use_case.execute(project_id), page_params)
    response.headers["X-Total"] = str(total)
    return [DrawingOut(**vars(d)) for d in page]


@router.post("/projects/{project_id}/documents", response_model=DrawingOut)
def create_document(
    project_id: int,
    body: CreateDrawingIn,
    response: Response,
    use_case: CreateDrawing = Depends(get_create_drawing),
    ctx: ActingContext = Depends(get_acting_context),
) -> DrawingOut:
    """ADR-009/E.4: creates a Drawing in the given project, or returns the
    existing one if (project_id, sheet_number) already exists (idempotent
    retry -- 200, not a new 201). DIP is the first external, evidence-driven
    caller of this route; the human frontend and the seed script remain the
    other two ways a Drawing can exist."""
    ctx.require_project(project_id)
    ctx.require_scope("documents")
    drawing, created = use_case.execute(project_id, body.sheet_number, body.title, body.discipline_code)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return DrawingOut(**vars(drawing))


@router.get("/projects/{project_id}/documents/{drawing_id}", response_model=DrawingOut)
def get_document(
    project_id: int,
    drawing_id: int,
    use_case: GetDrawing = Depends(get_get_drawing),
    ctx: ActingContext = Depends(get_acting_context),
) -> DrawingOut:
    ctx.require_project(project_id)
    ctx.require_scope("documents")
    try:
        drawing = use_case.execute(drawing_id)
        ensure_resource_in_project(drawing.project_id, project_id)
        return DrawingOut(**vars(drawing))
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.get(
    "/projects/{project_id}/documents/{drawing_id}/versions",
    response_model=list[DrawingVersionOut],
)
def list_document_versions(
    project_id: int,
    drawing_id: int,
    use_case: ListDrawingVersions = Depends(get_list_drawing_versions),
    get_use_case: GetDrawing = Depends(get_get_drawing),
    ctx: ActingContext = Depends(get_acting_context),
) -> list[DrawingVersionOut]:
    ctx.require_project(project_id)
    if not ctx.can_see("documents"):
        return []
    try:
        # The versions use case lists by drawing_id, not project_id, so the
        # parent drawing must be proven to belong to this project.
        parent = get_use_case.execute(drawing_id)
        ensure_resource_in_project(parent.project_id, project_id)
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return [_version_out(v) for v in use_case.execute(drawing_id)]


@router.get(
    "/projects/{project_id}/documents/versions/{version_id}",
    response_model=DrawingVersionOut,
)
def get_document_version(
    project_id: int,
    version_id: int,
    use_case: GetDrawingVersion = Depends(get_get_drawing_version),
    get_use_case: GetDrawing = Depends(get_get_drawing),
    ctx: ActingContext = Depends(get_acting_context),
) -> DrawingVersionOut:
    """Resolves a single version by its own id — needed because RFIs and other
    referencing entities cite a DrawingVersion directly, not its parent Drawing."""
    ctx.require_project(project_id)
    ctx.require_scope("documents")
    try:
        version = use_case.execute(version_id)
        # DrawingVersion has no project of its own — resolve the parent
        # drawing and prove it belongs to this project.
        parent = get_use_case.execute(version.drawing_id)
        ensure_resource_in_project(parent.project_id, project_id)
        return _version_out(version)
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.post(
    "/projects/{project_id}/documents/{drawing_id}/versions",
    response_model=DrawingVersionOut,
)
def create_document_version(
    project_id: int,
    drawing_id: int,
    body: CreateDrawingVersionIn,
    response: Response,
    use_case: CreateDrawingVersion = Depends(get_create_drawing_version),
    get_drawing_use_case: GetDrawing = Depends(get_get_drawing),
    ctx: ActingContext = Depends(get_acting_context),
) -> DrawingVersionOut:
    """ADR-009/E.4: creates a DRAFT DrawingVersion under an existing
    Drawing, or returns the existing one if (drawing_id, revision_label)
    already exists (idempotent retry -- 200, not a new 201). Never issues
    the version and never dispatches a webhook -- issuance remains the
    existing, separate PATCH .../issue endpoint below, unmodified."""
    ctx.require_project(project_id)
    ctx.require_scope("documents")
    try:
        drawing = get_drawing_use_case.execute(drawing_id)
        ensure_resource_in_project(drawing.project_id, project_id)
        clouds = [
            RevisionCloud(
                area=c.area,
                delta_number=c.delta_number,
                description=c.description,
                source_evidence_ref=c.source_evidence_ref,
            )
            for c in body.revision_clouds
        ]
        version, created = use_case.execute(drawing_id, body.revision_label, body.discipline_code, clouds)
        response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return _version_out(version)
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.patch(
    "/projects/{project_id}/documents/versions/{version_id}/issue",
    response_model=DrawingVersionOut,
)
def issue_document_version(
    project_id: int,
    version_id: int,
    use_case: IssueDrawingVersion = Depends(get_issue_drawing_version),
    get_version_use_case: GetDrawingVersion = Depends(get_get_drawing_version),
    get_drawing_use_case: GetDrawing = Depends(get_get_drawing),
    ctx: ActingContext = Depends(get_acting_context),
) -> DrawingVersionOut:
    """Issues a DrawingVersion (DRAFT -> ISSUED), superseding the prior current
    revision and repointing the Drawing at the newly issued version. Verifies
    project ownership through the parent Drawing before mutating."""
    ctx.require_project(project_id)
    ctx.require_scope("documents")
    try:
        version = get_version_use_case.execute(version_id)
        drawing = get_drawing_use_case.execute(version.drawing_id)
        ensure_resource_in_project(drawing.project_id, project_id)
        issued = use_case.execute(version_id)
        return _version_out(issued)
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidTransition as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
