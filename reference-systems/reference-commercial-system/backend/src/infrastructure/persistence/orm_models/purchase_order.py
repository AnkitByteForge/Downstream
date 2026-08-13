from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class PurchaseOrderModel(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    po_number: Mapped[str | None] = mapped_column(String(32), nullable=True, unique=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), index=True)
    contract_id: Mapped[int | None] = mapped_column(ForeignKey("contracts.id"), nullable=True)
    currency: Mapped[str] = mapped_column(String(3))
    payment_terms: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="DRAFT")
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    final_invoice: Mapped[bool] = mapped_column(Boolean, default=False)
    changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    company_code: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    plant: Mapped[str | None] = mapped_column(String(16), nullable=True)
    purchasing_org: Mapped[str | None] = mapped_column(String(16), nullable=True)
    business_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)


class POLineModel(Base):
    __tablename__ = "po_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    po_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), index=True)
    line_no: Mapped[int] = mapped_column()
    description: Mapped[str] = mapped_column(String(300))
    quantity: Mapped[float] = mapped_column(Numeric(14, 3))
    uom: Mapped[str] = mapped_column(String(16))
    unit_price: Mapped[float] = mapped_column(Numeric(16, 2))
    value: Mapped[float] = mapped_column(Numeric(16, 2))
    cost_code_id: Mapped[int | None] = mapped_column(ForeignKey("cost_codes.id"), nullable=True)
    spec_section_refs: Mapped[list] = mapped_column(JSON, default=list)
    lifecycle_position: Mapped[str] = mapped_column(String(16), default="draft")


class POScheduleLineModel(Base):
    __tablename__ = "po_schedule_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    po_line_id: Mapped[int] = mapped_column(ForeignKey("po_lines.id"), index=True)
    schedule_no: Mapped[int] = mapped_column()
    quantity: Mapped[float] = mapped_column(Numeric(14, 3))
    required_on_site_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    promised_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    linked_schedule_activity_ref: Mapped[str | None] = mapped_column(String(32), nullable=True)
    delivery_status: Mapped[str] = mapped_column(String(24), default="SCHEDULED")
