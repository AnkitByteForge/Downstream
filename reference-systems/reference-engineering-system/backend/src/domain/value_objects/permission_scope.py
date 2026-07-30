from __future__ import annotations

from dataclasses import dataclass

FULL_SCOPE_MARKER = "*"


@dataclass(frozen=True)
class PermissionScope:
    """What an integration credential can actually see, per docs/04's
    acting_credential_scope mechanic. A partially-scoped credential must cause
    reads to silently omit resource types outside its scope — never a 403 —
    reproducing real Procore's behavior of returning incomplete data rather
    than erroring on an under-provisioned integration user.
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
