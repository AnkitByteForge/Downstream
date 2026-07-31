from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from infrastructure.persistence.orm_models import RateLimitStateModel


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    retry_after_seconds: int


class RateLimitStore:
    """A fixed-window, per-client_id request budget, backed by a durable
    table rather than an in-process dict — matching docs/04's requirement
    for a real, configurable per-client_id budget (Procore's real 3,600/hour
    ceiling is the pattern; the exact number is configurable via Settings).
    Not a domain repository: rate limiting is a protocol-level concern of
    exposing this system as an API, not part of its engineering domain.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def check_and_record(
        self, client_id: str, now: datetime, window: timedelta, max_requests: int
    ) -> RateLimitResult:
        row = self._session.get(RateLimitStateModel, client_id)
        if row is None or now - row.window_start >= window:
            if row is None:
                row = RateLimitStateModel(client_id=client_id, window_start=now, request_count=1)
                self._session.add(row)
            else:
                row.window_start = now
                row.request_count = 1
            self._session.flush()
            return RateLimitResult(allowed=True, retry_after_seconds=0)

        if row.request_count < max_requests:
            row.request_count += 1
            self._session.flush()
            return RateLimitResult(allowed=True, retry_after_seconds=0)

        retry_after = int((row.window_start + window - now).total_seconds())
        return RateLimitResult(allowed=False, retry_after_seconds=max(retry_after, 1))
