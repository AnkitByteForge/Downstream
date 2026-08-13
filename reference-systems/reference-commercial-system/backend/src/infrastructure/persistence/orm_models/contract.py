from __future__ import annotations

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ContractModel(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), index=True)
    type: Mapped[str] = mapped_column(String(24))
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    value: Mapped[float | None] = mapped_column(Numeric(16, 2), nullable=True)
    retention_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    company_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    plant: Mapped[str | None] = mapped_column(String(16), nullable=True)
    purchasing_org: Mapped[str | None] = mapped_column(String(16), nullable=True)
    business_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)
