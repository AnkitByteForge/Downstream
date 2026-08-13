from __future__ import annotations

import secrets
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.persistence.orm_models import CsrfTokenModel


class CsrfTokenStore:
    """Real SAP behavior (04_Downstream_Connector_Layer_Validation.md):
    "a GET on the Purchase Order resource with X-CSRF-Token: fetch returns
    a token; any POST/PATCH/DELETE without it is rejected with 403." Tokens
    are single-use and actor-bound (a human session or an OAuth2 client
    cannot consume a token issued to a different actor)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def issue(self, actor_key: str, now: datetime, ttl: timedelta) -> str:
        token = secrets.token_urlsafe(24)
        row = CsrfTokenModel(
            actor_key=actor_key, token=token, issued_at=now, expires_at=now + ttl
        )
        self._session.add(row)
        self._session.flush()
        return token

    def validate_and_consume(self, actor_key: str, token: str, now: datetime) -> bool:
        row = self._session.execute(
            select(CsrfTokenModel).where(CsrfTokenModel.token == token)
        ).scalar_one_or_none()
        if row is None:
            return False
        if row.actor_key != actor_key:
            return False
        if row.consumed_at is not None:
            return False
        if row.expires_at < now:
            return False
        row.consumed_at = now
        self._session.flush()
        return True
