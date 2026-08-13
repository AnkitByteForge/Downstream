from __future__ import annotations

from datetime import date

from sqlalchemy import Column, Date, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

drawing_version_locations = Table(
    "drawing_version_locations",
    Base.metadata,
    Column("version_id", ForeignKey("drawing_versions.id"), primary_key=True),
    Column("location_id", ForeignKey("locations.id"), primary_key=True),
)


class DrawingModel(Base):
    __tablename__ = "drawings"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    sheet_number: Mapped[str] = mapped_column(String(24))
    title: Mapped[str] = mapped_column(String(200))
    discipline_code: Mapped[str] = mapped_column(ForeignKey("disciplines.code"))
    current_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("drawing_versions.id", use_alter=True), nullable=True
    )


class DrawingVersionModel(Base):
    __tablename__ = "drawing_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    drawing_id: Mapped[int] = mapped_column(ForeignKey("drawings.id"), index=True)
    revision_label: Mapped[str] = mapped_column(String(24))
    issuance_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(16), default="DRAFT")
    discipline_code: Mapped[str] = mapped_column(ForeignKey("disciplines.code"))
    superseded_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("drawing_versions.id"), nullable=True
    )


class RevisionCloudModel(Base):
    __tablename__ = "drawing_version_revision_clouds"

    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("drawing_versions.id"), index=True)
    area: Mapped[str] = mapped_column(String(100))
    delta_number: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(String(400))
    source_evidence_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
