from __future__ import annotations

from application.exceptions import NotFound
from application.ports import ClockPort
from domain.entities import RFI
from domain.repositories import RFIRepository
from domain.state_machines import rfi_transitions


class ListRFIs:
    def __init__(self, rfi_repo: RFIRepository) -> None:
        self._rfi_repo = rfi_repo

    def execute(self, project_id: int) -> list[RFI]:
        return self._rfi_repo.list_by_project(project_id)


class GetRFI:
    def __init__(self, rfi_repo: RFIRepository) -> None:
        self._rfi_repo = rfi_repo

    def execute(self, rfi_id: int) -> RFI:
        rfi = self._rfi_repo.get(rfi_id)
        if rfi is None:
            raise NotFound("RFI", rfi_id)
        return rfi


class RespondToRFI:
    def __init__(self, rfi_repo: RFIRepository) -> None:
        self._rfi_repo = rfi_repo

    def execute(self, rfi_id: int, response_text: str, manager_user_id: int) -> RFI:
        rfi = self._rfi_repo.get(rfi_id)
        if rfi is None:
            raise NotFound("RFI", rfi_id)
        updated = rfi_transitions.respond_to_rfi(rfi, response_text, manager_user_id)
        return self._rfi_repo.update(updated)


class CloseRFI:
    """Fires the webhook-worthy transition the whole Reference Execution Trace
    starts from (Phase 0). Webhook dispatch itself is out of scope for RES-1
    (RES-2) — this use case only performs the state transition and persists it.
    """

    def __init__(self, rfi_repo: RFIRepository, clock: ClockPort) -> None:
        self._rfi_repo = rfi_repo
        self._clock = clock

    def execute(self, rfi_id: int, response_text: str | None = None) -> RFI:
        rfi = self._rfi_repo.get(rfi_id)
        if rfi is None:
            raise NotFound("RFI", rfi_id)
        updated = rfi_transitions.close_rfi(rfi, self._clock.now(), response_text)
        return self._rfi_repo.update(updated)
