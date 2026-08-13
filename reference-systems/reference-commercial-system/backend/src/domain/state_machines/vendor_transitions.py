from __future__ import annotations

from dataclasses import replace

from domain.entities.vendor import Vendor
from domain.exceptions import InvalidTransition

# The Reference Commercial System.md §M item 6:
# Prospective -> Prequalified -> Approved -> Suspended/Blacklisted (terminal),
# with Suspended -> Approved reinstatement.


def prequalify(vendor: Vendor) -> Vendor:
    if vendor.qualification_status != "PROSPECTIVE":
        raise InvalidTransition("Vendor", vendor.qualification_status, "PREQUALIFIED")
    return replace(vendor, qualification_status="PREQUALIFIED")


def approve(vendor: Vendor) -> Vendor:
    if vendor.qualification_status not in ("PREQUALIFIED", "SUSPENDED"):
        raise InvalidTransition("Vendor", vendor.qualification_status, "APPROVED")
    return replace(vendor, qualification_status="APPROVED")


def suspend(vendor: Vendor) -> Vendor:
    if vendor.qualification_status != "APPROVED":
        raise InvalidTransition("Vendor", vendor.qualification_status, "SUSPENDED")
    return replace(vendor, qualification_status="SUSPENDED")


def blacklist(vendor: Vendor) -> Vendor:
    if vendor.qualification_status not in ("APPROVED", "SUSPENDED"):
        raise InvalidTransition("Vendor", vendor.qualification_status, "BLACKLISTED")
    return replace(vendor, qualification_status="BLACKLISTED")
