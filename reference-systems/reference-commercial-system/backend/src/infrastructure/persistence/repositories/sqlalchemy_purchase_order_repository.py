from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.entities.purchase_order import POLine, POScheduleLine, PurchaseOrder
from domain.repositories.purchase_order_repository import (
    POLineRepository,
    POScheduleLineRepository,
    PurchaseOrderRepository,
)
from domain.value_objects import OrgScope
from infrastructure.persistence.orm_models import POLineModel, POScheduleLineModel, PurchaseOrderModel


def _po_to_domain(row: PurchaseOrderModel) -> PurchaseOrder:
    return PurchaseOrder(
        id=row.id,
        po_number=row.po_number,
        vendor_id=row.vendor_id,
        currency=row.currency,
        org_scope=OrgScope(
            company_code=row.company_code,
            plant=row.plant,
            purchasing_org=row.purchasing_org,
            business_unit=row.business_unit,
        ),
        contract_id=row.contract_id,
        payment_terms=row.payment_terms,
        status=row.status,
        acknowledged=row.acknowledged,
        acknowledged_at=row.acknowledged_at,
        delivery_completed=row.delivery_completed,
        final_invoice=row.final_invoice,
        changed_at=row.changed_at,
    )


def _line_to_domain(row: POLineModel) -> POLine:
    return POLine(
        id=row.id,
        po_id=row.po_id,
        line_no=row.line_no,
        description=row.description,
        quantity=float(row.quantity),
        uom=row.uom,
        unit_price=float(row.unit_price),
        value=float(row.value),
        cost_code_id=row.cost_code_id,
        spec_section_refs=list(row.spec_section_refs or []),
        lifecycle_position=row.lifecycle_position,
    )


def _schedule_line_to_domain(row: POScheduleLineModel) -> POScheduleLine:
    return POScheduleLine(
        id=row.id,
        po_line_id=row.po_line_id,
        schedule_no=row.schedule_no,
        quantity=float(row.quantity),
        required_on_site_date=row.required_on_site_date,
        promised_date=row.promised_date,
        linked_schedule_activity_ref=row.linked_schedule_activity_ref,
        delivery_status=row.delivery_status,
    )


class SqlAlchemyPurchaseOrderRepository(PurchaseOrderRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, po: PurchaseOrder) -> PurchaseOrder:
        row = PurchaseOrderModel(
            po_number=po.po_number,
            vendor_id=po.vendor_id,
            contract_id=po.contract_id,
            currency=po.currency,
            payment_terms=po.payment_terms,
            status=po.status,
            acknowledged=po.acknowledged,
            acknowledged_at=po.acknowledged_at,
            delivery_completed=po.delivery_completed,
            final_invoice=po.final_invoice,
            changed_at=po.changed_at,
            company_code=po.org_scope.company_code,
            plant=po.org_scope.plant,
            purchasing_org=po.org_scope.purchasing_org,
            business_unit=po.org_scope.business_unit,
        )
        self._session.add(row)
        self._session.flush()
        return _po_to_domain(row)

    def get(self, po_id: int) -> PurchaseOrder | None:
        row = self._session.get(PurchaseOrderModel, po_id)
        return _po_to_domain(row) if row else None

    def get_by_po_number(self, po_number: str) -> PurchaseOrder | None:
        row = self._session.execute(
            select(PurchaseOrderModel).where(PurchaseOrderModel.po_number == po_number)
        ).scalar_one_or_none()
        return _po_to_domain(row) if row else None

    def list_all(self) -> list[PurchaseOrder]:
        rows = self._session.execute(select(PurchaseOrderModel)).scalars().all()
        return [_po_to_domain(r) for r in rows]

    def list_changed_since(self, since: datetime) -> list[PurchaseOrder]:
        rows = (
            self._session.execute(
                select(PurchaseOrderModel).where(PurchaseOrderModel.changed_at >= since)
            )
            .scalars()
            .all()
        )
        return [_po_to_domain(r) for r in rows]

    def update(self, po: PurchaseOrder) -> PurchaseOrder:
        row = self._session.get(PurchaseOrderModel, po.id)
        assert row is not None
        row.po_number = po.po_number
        row.contract_id = po.contract_id
        row.payment_terms = po.payment_terms
        row.status = po.status
        row.acknowledged = po.acknowledged
        row.acknowledged_at = po.acknowledged_at
        row.delivery_completed = po.delivery_completed
        row.final_invoice = po.final_invoice
        row.changed_at = po.changed_at
        self._session.flush()
        return _po_to_domain(row)


class SqlAlchemyPOLineRepository(POLineRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, line: POLine) -> POLine:
        row = POLineModel(
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
        self._session.add(row)
        self._session.flush()
        return _line_to_domain(row)

    def get(self, line_id: int) -> POLine | None:
        row = self._session.get(POLineModel, line_id)
        return _line_to_domain(row) if row else None

    def list_by_po(self, po_id: int) -> list[POLine]:
        rows = (
            self._session.execute(select(POLineModel).where(POLineModel.po_id == po_id))
            .scalars()
            .all()
        )
        return [_line_to_domain(r) for r in rows]

    def update(self, line: POLine) -> POLine:
        row = self._session.get(POLineModel, line.id)
        assert row is not None
        row.lifecycle_position = line.lifecycle_position
        self._session.flush()
        return _line_to_domain(row)


class SqlAlchemyPOScheduleLineRepository(POScheduleLineRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, schedule_line: POScheduleLine) -> POScheduleLine:
        row = POScheduleLineModel(
            po_line_id=schedule_line.po_line_id,
            schedule_no=schedule_line.schedule_no,
            quantity=schedule_line.quantity,
            required_on_site_date=schedule_line.required_on_site_date,
            promised_date=schedule_line.promised_date,
            linked_schedule_activity_ref=schedule_line.linked_schedule_activity_ref,
            delivery_status=schedule_line.delivery_status,
        )
        self._session.add(row)
        self._session.flush()
        return _schedule_line_to_domain(row)

    def get(self, schedule_line_id: int) -> POScheduleLine | None:
        row = self._session.get(POScheduleLineModel, schedule_line_id)
        return _schedule_line_to_domain(row) if row else None

    def list_by_po_line(self, po_line_id: int) -> list[POScheduleLine]:
        rows = (
            self._session.execute(
                select(POScheduleLineModel).where(POScheduleLineModel.po_line_id == po_line_id)
            )
            .scalars()
            .all()
        )
        return [_schedule_line_to_domain(r) for r in rows]
