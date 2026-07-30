from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from application.ports import ClockPort
from domain.entities import RFI
from domain.repositories import RFIRepository


class FakeClock(ClockPort):
    def __init__(self, fixed: datetime | None = None) -> None:
        self._fixed = fixed or datetime(2026, 7, 28, 9, 14, 3, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self._fixed


class InMemoryRFIRepository(RFIRepository):
    """Proves a use case is fully testable with zero database — the whole
    point of the repository-port split in Clean Architecture."""

    def __init__(self) -> None:
        self._rows: dict[int, RFI] = {}
        self._next_id = 1

    def get(self, rfi_id: int) -> RFI | None:
        return self._rows.get(rfi_id)

    def list_by_project(self, project_id: int) -> list[RFI]:
        return [r for r in self._rows.values() if r.project_id == project_id]

    def add(self, rfi: RFI) -> RFI:
        rfi = replace(rfi, id=self._next_id)
        self._rows[rfi.id] = rfi
        self._next_id += 1
        return rfi

    def update(self, rfi: RFI) -> RFI:
        self._rows[rfi.id] = rfi
        return rfi
