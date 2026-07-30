from __future__ import annotations


class DomainError(Exception):
    """Base class for every error the domain layer itself raises."""


class InvalidTransition(DomainError):
    def __init__(self, entity: str, from_status: str, to_status: str) -> None:
        self.entity = entity
        self.from_status = from_status
        self.to_status = to_status
        super().__init__(
            f"{entity}: illegal transition from {from_status!r} to {to_status!r}"
        )


class DomainRuleViolation(DomainError):
    """Raised when an operation is structurally allowed but violates a stated
    business rule (e.g. closing an RFI with no response recorded)."""
