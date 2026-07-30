from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class SpecDivisionModel(Base):
    __tablename__ = "spec_divisions"

    number: Mapped[str] = mapped_column(String(4), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))


class SpecSectionModel(Base):
    __tablename__ = "spec_sections"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    division_number: Mapped[str] = mapped_column(ForeignKey("spec_divisions.number"))
    number: Mapped[str] = mapped_column(String(16))
    title: Mapped[str] = mapped_column(String(200))
    substitution_policy: Mapped[str | None] = mapped_column(String(400), nullable=True)
