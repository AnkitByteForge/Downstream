from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Table
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class SubmittalPackageModel(Base):
    __tablename__ = "submittal_packages"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)


class SubmittalReviewStatusModel(Base):
    __tablename__ = "submittal_review_statuses"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    code: Mapped[str] = mapped_column(String(40))
    label: Mapped[str] = mapped_column(String(100))
    gates_procurement: Mapped[bool] = mapped_column(Boolean)
    is_terminal: Mapped[bool] = mapped_column(Boolean)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class SubmittalRequirementModel(Base):
    __tablename__ = "submittal_requirements"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    spec_section_id: Mapped[int] = mapped_column(ForeignKey("spec_sections.id"))
    submittal_type: Mapped[str] = mapped_column(String(40))
    category: Mapped[str] = mapped_column(String(24))


class SubmittalModel(Base):
    __tablename__ = "submittals"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    number: Mapped[str] = mapped_column(String(24))
    spec_section_id: Mapped[int] = mapped_column(ForeignKey("spec_sections.id"))
    package_id: Mapped[int | None] = mapped_column(
        ForeignKey("submittal_packages.id"), nullable=True
    )
    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("vendors.id"), nullable=True)
    commitment_id: Mapped[int | None] = mapped_column(ForeignKey("commitments.id"), nullable=True)
    submittal_type: Mapped[str] = mapped_column(String(40), default="shop_drawing")
    category: Mapped[str] = mapped_column(String(24), default="action")
    lead_time_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    required_on_site_date: Mapped[date | None] = mapped_column(Date, nullable=True)


submittal_drawing_refs = Table(
    "submittal_drawing_refs",
    Base.metadata,
    Column("submittal_revision_id", ForeignKey("submittal_revisions.id"), primary_key=True),
    Column("drawing_version_id", ForeignKey("drawing_versions.id"), primary_key=True),
)

submittal_location_refs = Table(
    "submittal_location_refs",
    Base.metadata,
    Column("submittal_revision_id", ForeignKey("submittal_revisions.id"), primary_key=True),
    Column("location_id", ForeignKey("locations.id"), primary_key=True),
)


class SubmittalRevisionModel(Base):
    __tablename__ = "submittal_revisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    submittal_id: Mapped[int] = mapped_column(ForeignKey("submittals.id"), index=True)
    rev_label: Mapped[str] = mapped_column(String(24))
    review_status_id: Mapped[int] = mapped_column(ForeignKey("submittal_review_statuses.id"))
    ball_in_court_role: Mapped[str] = mapped_column(String(24), default="submitter")
    ball_in_court_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    equipment_tag: Mapped[str | None] = mapped_column(String(40), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(120), nullable=True)
    model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    capacity_value: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    capacity_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fla_value: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    fla_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    disposed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    disposition_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
