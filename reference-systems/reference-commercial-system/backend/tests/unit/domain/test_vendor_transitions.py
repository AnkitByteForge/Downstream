from __future__ import annotations

import pytest

from domain.entities.vendor import Vendor
from domain.exceptions import InvalidTransition
from domain.state_machines import vendor_transitions


def _vendor(status: str) -> Vendor:
    return Vendor(id=1, name="Test Vendor", qualification_status=status)


def test_prequalify_from_prospective() -> None:
    v = vendor_transitions.prequalify(_vendor("PROSPECTIVE"))
    assert v.qualification_status == "PREQUALIFIED"


def test_prequalify_rejects_non_prospective() -> None:
    with pytest.raises(InvalidTransition):
        vendor_transitions.prequalify(_vendor("APPROVED"))


def test_approve_from_prequalified() -> None:
    v = vendor_transitions.approve(_vendor("PREQUALIFIED"))
    assert v.qualification_status == "APPROVED"


def test_approve_from_suspended_reinstates() -> None:
    v = vendor_transitions.approve(_vendor("SUSPENDED"))
    assert v.qualification_status == "APPROVED"


def test_approve_rejects_prospective() -> None:
    with pytest.raises(InvalidTransition):
        vendor_transitions.approve(_vendor("PROSPECTIVE"))


def test_suspend_from_approved() -> None:
    v = vendor_transitions.suspend(_vendor("APPROVED"))
    assert v.qualification_status == "SUSPENDED"


def test_suspend_rejects_prequalified() -> None:
    with pytest.raises(InvalidTransition):
        vendor_transitions.suspend(_vendor("PREQUALIFIED"))


@pytest.mark.parametrize("status", ["APPROVED", "SUSPENDED"])
def test_blacklist_from_approved_or_suspended(status: str) -> None:
    v = vendor_transitions.blacklist(_vendor(status))
    assert v.qualification_status == "BLACKLISTED"


def test_blacklist_rejects_prospective() -> None:
    with pytest.raises(InvalidTransition):
        vendor_transitions.blacklist(_vendor("PROSPECTIVE"))


def test_blacklist_is_terminal() -> None:
    with pytest.raises(InvalidTransition):
        vendor_transitions.approve(_vendor("BLACKLISTED"))
