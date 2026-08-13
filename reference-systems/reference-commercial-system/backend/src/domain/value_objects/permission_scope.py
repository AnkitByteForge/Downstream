from __future__ import annotations

from dataclasses import dataclass

FULL_SCOPE_MARKER = "*"


@dataclass(frozen=True)
class PermissionScope:
    """What an OAuth2 client_credentials integration client can actually
    see, per docs/04's acting_credential_scope mechanic (independently
    reimplemented here — the Reference Commercial System shares no code
    with the Reference Engineering System, per ADR-014). A partially-scoped
    credential silently omits resource types outside its scope on list
    reads and 404s on direct get — never a 403 — reproducing real SAP/
    Oracle's behavior of a partially-scoped integration user returning
    incomplete data rather than erroring.
    """

    resource_types: frozenset[str]

    @classmethod
    def full(cls) -> "PermissionScope":
        return cls(frozenset({FULL_SCOPE_MARKER}))

    @classmethod
    def partial(cls, *resource_types: str) -> "PermissionScope":
        return cls(frozenset(resource_types))

    def is_full(self) -> bool:
        return FULL_SCOPE_MARKER in self.resource_types

    def grants(self, resource_type: str) -> bool:
        return self.is_full() or resource_type in self.resource_types

    def as_wire_value(self) -> str:
        if self.is_full():
            return "full"
        return "partial:[" + ",".join(sorted(self.resource_types)) + "]"
