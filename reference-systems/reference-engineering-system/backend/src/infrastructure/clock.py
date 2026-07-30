from __future__ import annotations

from datetime import datetime, timezone

from application.ports import ClockPort


class SystemClock(ClockPort):
    def now(self) -> datetime:
        return datetime.now(timezone.utc)
