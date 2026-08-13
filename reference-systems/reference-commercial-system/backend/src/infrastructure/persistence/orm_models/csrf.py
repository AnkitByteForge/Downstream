from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CsrfTokenModel(Base):
    """Backs the CSRF ceremony (docs/04, docs/05 Phase 12.2: a `GET` request
    carrying `X-CSRF-Token: fetch` must issue a token the following write
    echoes back). Not a domain repository — the CSRF ceremony is a
    protocol-level concern of this system's own HTTP surface, mirroring how
    RES keeps rate limiting out of domain/application entirely."""

    __tablename__ = "csrf_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_key: Mapped[str] = mapped_column(String(64), index=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
