from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ModelObjectModel(Base):
    __tablename__ = "model_objects"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    discipline_code: Mapped[str] = mapped_column(String(4))
    appearance_profile: Mapped[str] = mapped_column(String(16))
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    resource_link_id: Mapped[int | None] = mapped_column(
        ForeignKey("schedule_activities.id"), nullable=True
    )
