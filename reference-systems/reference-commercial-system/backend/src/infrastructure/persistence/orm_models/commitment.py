from __future__ import annotations

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CommitmentModel(Base):
    __tablename__ = "commitments"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_type: Mapped[str] = mapped_column(String(16))
    cost_code_id: Mapped[int] = mapped_column(ForeignKey("cost_codes.id"), index=True)
    po_id: Mapped[int | None] = mapped_column(ForeignKey("purchase_orders.id"), nullable=True)
    committed_amount: Mapped[float] = mapped_column(Numeric(16, 2))
    relieved_amount: Mapped[float] = mapped_column(Numeric(16, 2), default=0)
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(24), default="OPEN")
    company_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    plant: Mapped[str | None] = mapped_column(String(16), nullable=True)
    purchasing_org: Mapped[str | None] = mapped_column(String(16), nullable=True)
    business_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)
