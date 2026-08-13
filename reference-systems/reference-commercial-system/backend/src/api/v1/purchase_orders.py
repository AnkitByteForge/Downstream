from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.deps import (
    ActingContext,
    get_acknowledge_po,
    get_acting_context,
    get_amend_po,
    get_approve_po,
    get_approve_po_amendment,
    get_cancel_po,
    get_close_po,
    get_create_po_line,
    get_create_po_schedule_line,
    get_create_purchase_order,
    get_finally_close_po,
    get_get_purchase_order_by_number,
    get_hold_po,
    get_install_po_line,
    get_issue_po_line,
    get_list_po_lines,
    get_list_po_schedule_lines,
    get_list_purchase_orders,
    get_reject_po,
    get_release_hold_po,
    get_ship_po_line,
    get_start_fabrication_po_line,
    get_submit_po_for_approval,
    get_withdraw_po,
    issue_csrf_if_requested,
    require_csrf_token,
)
from api.pagination import PageParams, paginate
from api.schemas.org_scope import OrgScopeOut
from api.schemas.purchase_order import (
    CreatePOLineRequest,
    CreatePOScheduleLineRequest,
    CreatePurchaseOrderRequest,
    POLineOut,
    POScheduleLineOut,
    PurchaseOrderOut,
)
from application.exceptions import NotFound
from application.use_cases.po_line_use_cases import (
    CreatePOLine,
    InstallPOLine,
    IssuePOLine,
    ListPOLines,
    ShipPOLine,
    StartFabricationPOLine,
)
from application.use_cases.po_schedule_line_use_cases import CreatePOScheduleLine, ListPOScheduleLines
from application.use_cases.purchase_order_use_cases import (
    CreatePurchaseOrder,
    GetPurchaseOrderByNumber,
    ListPurchaseOrders,
)
from domain.exceptions import DomainRuleViolation, InvalidTransition
from domain.value_objects import OrgScope

router = APIRouter(prefix="/purchase_orders", tags=["purchase_orders"])


def _po_out(po) -> PurchaseOrderOut:
    return PurchaseOrderOut(
        id=po.id,
        po_number=po.po_number,
        vendor_id=po.vendor_id,
        currency=po.currency,
        org_scope=OrgScopeOut(**vars(po.org_scope)),
        contract_id=po.contract_id,
        payment_terms=po.payment_terms,
        status=po.status,
        acknowledged=po.acknowledged,
        acknowledged_at=po.acknowledged_at,
        delivery_completed=po.delivery_completed,
        final_invoice=po.final_invoice,
        changed_at=po.changed_at,
    )


def _line_out(line) -> POLineOut:
    return POLineOut(
        id=line.id,
        po_id=line.po_id,
        line_no=line.line_no,
        description=line.description,
        quantity=line.quantity,
        uom=line.uom,
        unit_price=line.unit_price,
        value=line.value,
        cost_code_id=line.cost_code_id,
        spec_section_refs=line.spec_section_refs,
        lifecycle_position=line.lifecycle_position,
    )


def _schedule_line_out(sl) -> POScheduleLineOut:
    return POScheduleLineOut(
        id=sl.id,
        po_line_id=sl.po_line_id,
        schedule_no=sl.schedule_no,
        quantity=sl.quantity,
        required_on_site_date=sl.required_on_site_date,
        promised_date=sl.promised_date,
        linked_schedule_activity_ref=sl.linked_schedule_activity_ref,
        delivery_status=sl.delivery_status,
    )


def _get_po_or_404(use_case: GetPurchaseOrderByNumber, po_number: str, ctx: ActingContext):
    try:
        po = use_case.execute(po_number)
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    ctx.require_company_code(po.org_scope.company_code)
    return po


def _find_line_or_404(lines_use_case: ListPOLines, po_id: int, line_no: int):
    for line in lines_use_case.execute(po_id):
        if line.line_no == line_no:
            return line
    raise HTTPException(status.HTTP_404_NOT_FOUND, f"POLine line_no={line_no} not found on this PO")


@router.get("", response_model=list[PurchaseOrderOut])
def list_purchase_orders(
    response: Response,
    use_case: ListPurchaseOrders = Depends(get_list_purchase_orders),
    ctx: ActingContext = Depends(get_acting_context),
    page_params: PageParams = Depends(),
    changed_since: datetime | None = None,
) -> list[PurchaseOrderOut]:
    if not ctx.can_see("purchase_orders"):
        response.headers["X-Total"] = "0"
        return []
    items = use_case.execute(changed_since=changed_since)
    if ctx.kind == "integration":
        # Org-scope isolation (ADR-012): an integration client scoped to one
        # company_code never sees another company_code's POs, even in a list.
        items = [po for po in items if po.org_scope.company_code == ctx.company_code]
    page, total = paginate(items, page_params)
    response.headers["X-Total"] = str(total)
    return [_po_out(po) for po in page]


@router.get("/{po_number}", response_model=PurchaseOrderOut)
def get_purchase_order(
    po_number: str,
    use_case: GetPurchaseOrderByNumber = Depends(get_get_purchase_order_by_number),
    ctx: ActingContext = Depends(get_acting_context),
    _csrf_issue: None = Depends(issue_csrf_if_requested),
) -> PurchaseOrderOut:
    ctx.require_scope("purchase_orders")
    po = _get_po_or_404(use_case, po_number, ctx)
    return _po_out(po)


@router.post("", response_model=PurchaseOrderOut, status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    body: CreatePurchaseOrderRequest,
    use_case: CreatePurchaseOrder = Depends(get_create_purchase_order),
    ctx: ActingContext = Depends(get_acting_context),
    _csrf: None = Depends(require_csrf_token),
) -> PurchaseOrderOut:
    ctx.require_scope("purchase_orders")
    po = use_case.execute(
        vendor_id=body.vendor_id,
        currency=body.currency,
        po_number=body.po_number,
        contract_id=body.contract_id,
        payment_terms=body.payment_terms,
        org_scope=OrgScope(
            company_code=body.company_code, plant=body.plant, purchasing_org=body.purchasing_org
        ),
    )
    return _po_out(po)


def _transition_route(use_case, po_number: str, get_use_case: GetPurchaseOrderByNumber, ctx: ActingContext):
    # Confirms org-scope isolation before mutating, then applies the transition.
    _get_po_or_404(get_use_case, po_number, ctx)
    try:
        return _po_out(use_case.execute(po_number))
    except NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except (InvalidTransition, DomainRuleViolation) as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


_TRANSITIONS = [
    ("submit", get_submit_po_for_approval),
    ("approve", get_approve_po),
    ("reject", get_reject_po),
    ("withdraw", get_withdraw_po),
    ("cancel", get_cancel_po),
    ("acknowledge", get_acknowledge_po),
    ("hold", get_hold_po),
    ("release_hold", get_release_hold_po),
    ("amend", get_amend_po),
    ("approve_amendment", get_approve_po_amendment),
    ("close", get_close_po),
    ("finally_close", get_finally_close_po),
]


def _make_transition_endpoint(path: str, use_case_dep):
    def endpoint(
        po_number: str,
        use_case=Depends(use_case_dep),
        get_use_case: GetPurchaseOrderByNumber = Depends(get_get_purchase_order_by_number),
        ctx: ActingContext = Depends(get_acting_context),
        _csrf: None = Depends(require_csrf_token),
    ) -> PurchaseOrderOut:
        ctx.require_scope("purchase_orders")
        return _transition_route(use_case, po_number, get_use_case, ctx)

    router.add_api_route(
        f"/{{po_number}}/{path}",
        endpoint,
        methods=["PATCH"],
        response_model=PurchaseOrderOut,
        name=f"purchase_order_{path}",
    )


for _path, _dep in _TRANSITIONS:
    _make_transition_endpoint(_path, _dep)


# --- POLine ---


@router.get("/{po_number}/lines", response_model=list[POLineOut])
def list_po_lines(
    po_number: str,
    get_po: GetPurchaseOrderByNumber = Depends(get_get_purchase_order_by_number),
    use_case: ListPOLines = Depends(get_list_po_lines),
    ctx: ActingContext = Depends(get_acting_context),
) -> list[POLineOut]:
    ctx.require_scope("purchase_orders")
    po = _get_po_or_404(get_po, po_number, ctx)
    return [_line_out(line) for line in use_case.execute(po.id)]


@router.get("/{po_number}/lines/{line_no}", response_model=POLineOut)
def get_po_line(
    po_number: str,
    line_no: int,
    get_po: GetPurchaseOrderByNumber = Depends(get_get_purchase_order_by_number),
    use_case: ListPOLines = Depends(get_list_po_lines),
    ctx: ActingContext = Depends(get_acting_context),
) -> POLineOut:
    ctx.require_scope("purchase_orders")
    po = _get_po_or_404(get_po, po_number, ctx)
    return _line_out(_find_line_or_404(use_case, po.id, line_no))


@router.post("/{po_number}/lines", response_model=POLineOut, status_code=status.HTTP_201_CREATED)
def create_po_line(
    po_number: str,
    body: CreatePOLineRequest,
    get_po: GetPurchaseOrderByNumber = Depends(get_get_purchase_order_by_number),
    use_case: CreatePOLine = Depends(get_create_po_line),
    ctx: ActingContext = Depends(get_acting_context),
    _csrf: None = Depends(require_csrf_token),
) -> POLineOut:
    ctx.require_scope("purchase_orders")
    po = _get_po_or_404(get_po, po_number, ctx)
    line = use_case.execute(
        po_id=po.id,
        line_no=body.line_no,
        description=body.description,
        quantity=body.quantity,
        uom=body.uom,
        unit_price=body.unit_price,
        value=body.value,
        cost_code_id=body.cost_code_id,
        spec_section_refs=body.spec_section_refs,
        lifecycle_position=body.lifecycle_position,
    )
    return _line_out(line)


def _make_line_transition_endpoint(path: str, use_case_dep):
    def endpoint(
        po_number: str,
        line_no: int,
        get_po: GetPurchaseOrderByNumber = Depends(get_get_purchase_order_by_number),
        lines_use_case: ListPOLines = Depends(get_list_po_lines),
        use_case=Depends(use_case_dep),
        ctx: ActingContext = Depends(get_acting_context),
        _csrf: None = Depends(require_csrf_token),
    ) -> POLineOut:
        ctx.require_scope("purchase_orders")
        po = _get_po_or_404(get_po, po_number, ctx)
        line = _find_line_or_404(lines_use_case, po.id, line_no)
        try:
            return _line_out(use_case.execute(line.id))
        except InvalidTransition as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    router.add_api_route(
        f"/{{po_number}}/lines/{{line_no}}/{path}",
        endpoint,
        methods=["PATCH"],
        response_model=POLineOut,
        name=f"po_line_{path}",
    )


for _path, _dep in [
    ("issue", get_issue_po_line),
    ("start_fabrication", get_start_fabrication_po_line),
    ("ship", get_ship_po_line),
    ("install", get_install_po_line),
]:
    _make_line_transition_endpoint(_path, _dep)


# --- POScheduleLine ---


@router.get("/{po_number}/lines/{line_no}/schedule_lines", response_model=list[POScheduleLineOut])
def list_po_schedule_lines(
    po_number: str,
    line_no: int,
    get_po: GetPurchaseOrderByNumber = Depends(get_get_purchase_order_by_number),
    lines_use_case: ListPOLines = Depends(get_list_po_lines),
    use_case: ListPOScheduleLines = Depends(get_list_po_schedule_lines),
    ctx: ActingContext = Depends(get_acting_context),
) -> list[POScheduleLineOut]:
    ctx.require_scope("purchase_orders")
    po = _get_po_or_404(get_po, po_number, ctx)
    line = _find_line_or_404(lines_use_case, po.id, line_no)
    return [_schedule_line_out(sl) for sl in use_case.execute(line.id)]


@router.post(
    "/{po_number}/lines/{line_no}/schedule_lines",
    response_model=POScheduleLineOut,
    status_code=status.HTTP_201_CREATED,
)
def create_po_schedule_line(
    po_number: str,
    line_no: int,
    body: CreatePOScheduleLineRequest,
    get_po: GetPurchaseOrderByNumber = Depends(get_get_purchase_order_by_number),
    lines_use_case: ListPOLines = Depends(get_list_po_lines),
    use_case: CreatePOScheduleLine = Depends(get_create_po_schedule_line),
    ctx: ActingContext = Depends(get_acting_context),
    _csrf: None = Depends(require_csrf_token),
) -> POScheduleLineOut:
    ctx.require_scope("purchase_orders")
    po = _get_po_or_404(get_po, po_number, ctx)
    line = _find_line_or_404(lines_use_case, po.id, line_no)
    sl = use_case.execute(
        po_line_id=line.id,
        schedule_no=body.schedule_no,
        quantity=body.quantity,
        required_on_site_date=body.required_on_site_date,
        promised_date=body.promised_date,
        linked_schedule_activity_ref=body.linked_schedule_activity_ref,
        delivery_status=body.delivery_status,
    )
    return _schedule_line_out(sl)
