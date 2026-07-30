from __future__ import annotations

import pytest

from application.exceptions import NotFound
from application.use_cases.rfi_use_cases import CloseRFI, GetRFI, ListRFIs, RespondToRFI
from domain.entities import RFI
from domain.value_objects import BallInCourt

from .fakes import FakeClock, InMemoryRFIRepository


def _seed_rfi(repo: InMemoryRFIRepository, status: str = "OPEN") -> RFI:
    return repo.add(
        RFI(
            id=None,
            project_id=1,
            number="214",
            display_number="RFI-214",
            subject="Duct routing conflict",
            ball_in_court=BallInCourt("assignee", 42),
            status=status,
        )
    )


def test_get_rfi_raises_not_found_for_unknown_id():
    with pytest.raises(NotFound):
        GetRFI(InMemoryRFIRepository()).execute(999)


def test_list_rfis_filters_by_project():
    repo = InMemoryRFIRepository()
    _seed_rfi(repo)
    use_case = ListRFIs(repo)
    assert len(use_case.execute(1)) == 1
    assert use_case.execute(2) == []


def test_respond_to_rfi_persists_the_transition():
    repo = InMemoryRFIRepository()
    rfi = _seed_rfi(repo, status="OPEN")
    updated = RespondToRFI(repo).execute(rfi.id, "Reroute per SK-14.", manager_user_id=7)
    assert updated.status == "RESPONDED"
    assert repo.get(rfi.id).status == "RESPONDED"


def test_close_rfi_uses_injected_clock_for_closed_at():
    repo = InMemoryRFIRepository()
    rfi = _seed_rfi(repo, status="OPEN")
    clock = FakeClock()
    closed = CloseRFI(repo, clock).execute(rfi.id, response_text="Reroute per SK-14.")
    assert closed.status == "CLOSED"
    assert closed.closed_at == clock.now()
