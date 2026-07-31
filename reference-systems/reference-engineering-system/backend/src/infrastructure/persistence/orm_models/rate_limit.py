from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class RateLimitStateModel(Base):
    __tablename__ = "rate_limit_state"

    client_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    request_count: Mapped[int] = mapped_column(Integer, default=0)
