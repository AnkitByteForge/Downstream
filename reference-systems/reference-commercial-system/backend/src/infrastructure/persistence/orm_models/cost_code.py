from __future__ import annotations

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CostCodeModel(Base):
    __tablename__ = "cost_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    native_code: Mapped[str] = mapped_column(String(32))
    cost_code_format: Mapped[str] = mapped_column(String(32))
    standard_ref: Mapped[str | None] = mapped_column(String(32), nullable=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("cost_codes.id"), nullable=True)
    company_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    plant: Mapped[str | None] = mapped_column(String(16), nullable=True)
    purchasing_org: Mapped[str | None] = mapped_column(String(16), nullable=True)
    business_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)
    budget_baseline: Mapped[float | None] = mapped_column(Numeric(16, 2), nullable=True)
    budget_current: Mapped[float | None] = mapped_column(Numeric(16, 2), nullable=True)
    committed: Mapped[float | None] = mapped_column(Numeric(16, 2), nullable=True)
    actual: Mapped[float | None] = mapped_column(Numeric(16, 2), nullable=True)
    etc: Mapped[float | None] = mapped_column(Numeric(16, 2), nullable=True)
    eac: Mapped[float | None] = mapped_column(Numeric(16, 2), nullable=True)
