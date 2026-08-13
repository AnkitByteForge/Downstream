from __future__ import annotations

from dataclasses import dataclass, field

from domain.exceptions import DomainRuleViolation

# Closed vocabulary — The Reference Commercial System.md §M item 6:
# Prospective -> Prequalified -> Approved -> Suspended/Blacklisted.
VENDOR_QUALIFICATION_STATUSES = (
    "PROSPECTIVE",
    "PREQUALIFIED",
    "APPROVED",
    "SUSPENDED",
    "BLACKLISTED",
)


@dataclass
class Vendor:
    id: int | None
    name: str
    qualification_status: str = "PROSPECTIVE"
    performance_score: float | None = None

    def __post_init__(self) -> None:
        if self.qualification_status not in VENDOR_QUALIFICATION_STATUSES:
            raise DomainRuleViolation(
                f"Vendor.qualification_status must be one of {VENDOR_QUALIFICATION_STATUSES}, "
                f"got {self.qualification_status!r}"
            )


@dataclass
class VendorScopeView:
    """A vendor's per-org-scope master-data view (The Reference Commercial
    System.md §D: "vendor data is maintained at three independent
    levels... a vendor may be usable for purchasing in one org scope but
    blocked in another"). One Vendor has many VendorScopeViews."""

    id: int | None
    vendor_id: int
    company_code: str | None = None
    purchasing_org: str | None = None
    blocked: bool = False
    purchasing_terms: dict = field(default_factory=dict)
