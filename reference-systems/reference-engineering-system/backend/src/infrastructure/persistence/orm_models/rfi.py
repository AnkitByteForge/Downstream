from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

rfi_drawing_refs = Table(
    "rfi_drawing_refs",
    Base.metadata,
    Column("rfi_id", ForeignKey("rfis.id"), primary_key=True),
    Column("version_id", ForeignKey("drawing_versions.id"), primary_key=True),
)

rfi_spec_section_refs = Table(
    "rfi_spec_section_refs",
    Base.metadata,
    Column("rfi_id", ForeignKey("rfis.id"), primary_key=True),
    Column("spec_section_id", ForeignKey("spec_sections.id"), primary_key=True),
)

rfi_location_refs = Table(
    "rfi_location_refs",
    Base.metadata,
    Column("rfi_id", ForeignKey("rfis.id"), primary_key=True),
    Column("location_id", ForeignKey("locations.id"), primary_key=True),
)


class RFIModel(Base):
    __tablename__ = "rfis"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    number: Mapped[str] = mapped_column(String(16))
    display_number: Mapped[str] = mapped_column(String(32))
    subject: Mapped[str] = mapped_column(String(300))
    question: Mapped[str | None] = mapped_column(Text, nullable=True)
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="DRAFT")
    ball_in_court_role: Mapped[str] = mapped_column(String(24), default="assignee")
    ball_in_court_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    cost_impact_flag: Mapped[str | None] = mapped_column(String(16), nullable=True)
    cost_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    discipline_code: Mapped[str | None] = mapped_column(
        ForeignKey("disciplines.code"), nullable=True
    )
    spawned_change_id: Mapped[int | None] = mapped_column(nullable=True)
    raw_document_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
