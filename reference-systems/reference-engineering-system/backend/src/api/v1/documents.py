from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.deps import (
    ActingContext,
    get_acting_context,
    get_get_drawing,
    get_get_drawing_version,
    get_list_drawing_versions,
    get_list_drawings,
)
from api.pagination import PageParams, paginate
from api.schemas.drawing import DrawingOut, DrawingVersionOut, RevisionCloudOut
from application.exceptions import NotFound
from application.use_cases.drawing_use_cases import (
    GetDrawing,
    GetDrawingVersion,
    ListDrawings,
    ListDrawingVersions,
)

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
    if not ctx.can_see("documents"):
        response.headers["X-Total"] = "0"
        return []
    page, total = paginate(use_case.execute(project_id), page_params)
    response.headers["X-Total"] = str(total)
    return [DrawingOut(**vars(d)) for d in page]


@router.get("/projects/{project_id}/documents/{drawing_id}", response_model=DrawingOut)
def get_document(
    project_id: int,
    drawing_id: int,
    use_case: GetDrawing = Depends(get_get_drawing),
    ctx: ActingContext = Depends(get_acting_context),
) -> DrawingOut:
    ctx.require_scope("documents")
    try:
        return DrawingOut(**vars(use_case.execute(drawing_id)))
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
    ctx: ActingContext = Depends(get_acting_context),
) -> list[DrawingVersionOut]:
    if not ctx.can_see("documents"):
        return []
    return [_version_out(v) for v in use_case.execute(drawing_id)]


@router.get(
    "/projects/{project_id}/documents/versions/{version_id}",
    response_model=DrawingVersionOut,
)
def get_document_version(
    project_id: int,
    version_id: int,
    use_case: GetDrawingVersion = Depends(get_get_drawing_version),
    ctx: ActingContext = Depends(get_acting_context),
) -> DrawingVersionOut:
    """Resolves a single version by its own id — needed because RFIs and other
    referencing entities cite a DrawingVersion directly, not its parent Drawing."""
    ctx.require_scope("documents")
    try:
        return _version_out(use_case.execute(version_id))
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
