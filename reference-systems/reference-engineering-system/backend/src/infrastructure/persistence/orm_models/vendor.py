from __future__ import annotations

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class VendorModel(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))


class CommitmentModel(Base):
    __tablename__ = "commitments"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"))
    cost_code: Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(String(300))
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    spec_section_id: Mapped[int | None] = mapped_column(
        ForeignKey("spec_sections.id"), nullable=True
    )
