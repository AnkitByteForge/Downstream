from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class DesignChangeModel(Base):
    __tablename__ = "design_changes"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    number: Mapped[str] = mapped_column(String(24))
    display_number: Mapped[str] = mapped_column(String(40))
    type: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(24), default="DRAFT")
    change_reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    discipline_code: Mapped[str | None] = mapped_column(String(4), nullable=True)
    source_rfi_id: Mapped[int | None] = mapped_column(ForeignKey("rfis.id"), nullable=True, index=True)
    ball_in_court_role: Mapped[str] = mapped_column(String(24), default="architect")
    ball_in_court_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    superseded_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("design_changes.id"), nullable=True
    )
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


design_change_drawing_version_refs = Table(
    "design_change_drawing_versions",
    Base.metadata,
    Column(
        "design_change_id", ForeignKey("design_changes.id"), primary_key=True
    ),
    Column("drawing_version_id", ForeignKey("drawing_versions.id"), primary_key=True),
)

design_change_spec_section_refs = Table(
    "design_change_spec_sections",
    Base.metadata,
    Column("design_change_id", ForeignKey("design_changes.id"), primary_key=True),
    Column("spec_section_id", ForeignKey("spec_sections.id"), primary_key=True),
)

design_change_location_refs = Table(
    "design_change_locations",
    Base.metadata,
    Column("design_change_id", ForeignKey("design_changes.id"), primary_key=True),
    Column("location_id", ForeignKey("locations.id"), primary_key=True),
)
