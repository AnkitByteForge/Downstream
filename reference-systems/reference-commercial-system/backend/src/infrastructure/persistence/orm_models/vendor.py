from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

# Closed vocabulary lengths sized generously; validation is a domain-layer
# concern (__post_init__), not a DB CHECK constraint, matching RES's own
# convention throughout.


class VendorModel(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    qualification_status: Mapped[str] = mapped_column(String(24), default="PROSPECTIVE")
    performance_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)


class VendorScopeViewModel(Base):
    __tablename__ = "vendor_scope_views"

    id: Mapped[int] = mapped_column(primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), index=True)
    company_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    purchasing_org: Mapped[str | None] = mapped_column(String(16), nullable=True)
    blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    purchasing_terms: Mapped[dict] = mapped_column(JSON, default=dict)
