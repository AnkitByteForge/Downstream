"""Short, prefixed ID conventions.

The one explicit, cross-service convention named anywhere in the frozen
docs for shared runtime configuration is the ID format itself —
docs/07_Downstream_Implementation_Blueprint.md §6: "IDs use short, prefixed
identifiers (matching the Reference Trace's own style — trg_…, evt_…)
rather than raw UUIDs, purely for human legibility in logs and demos."

No other shared runtime configuration schema (service ports, env var names,
connection strings, ...) is specified anywhere in the frozen documents, so
this package is deliberately scoped to just this one convention rather than
inventing configuration surface no document calls for. Milestone 0 is
shared contracts only — actual env-driven settings belong to the services
that need them, when they're built.
"""

from __future__ import annotations

import uuid
from typing import Literal

EntityName = Literal["trigger", "commercial_event", "impact", "action", "approval"]

# Prefixes are taken directly from the Reference Execution Trace's own IDs:
# trg_2f9a1c, evt_7731, imp_001, act_001, apr_001.
ID_PREFIXES: dict[EntityName, str] = {
    "trigger": "trg",
    "commercial_event": "evt",
    "impact": "imp",
    "action": "act",
    "approval": "apr",
}


def generate_id(entity: EntityName, *, suffix_length: int = 8) -> str:
    """Generate a new short, prefixed ID for the given entity type.

    e.g. generate_id("commercial_event") -> "evt_3f9a1c2b"
    """
    if entity not in ID_PREFIXES:
        raise ValueError(f"Unknown entity name: {entity!r}. Known entities: {sorted(ID_PREFIXES)}")
    if suffix_length < 1:
        raise ValueError("suffix_length must be at least 1")

    prefix = ID_PREFIXES[entity]
    suffix = uuid.uuid4().hex[:suffix_length]
    return f"{prefix}_{suffix}"


def is_valid_id(entity: EntityName, value: str) -> bool:
    """Whether `value` is a syntactically valid ID for `entity` — i.e. it
    carries that entity's documented prefix followed by a non-empty suffix.

    This checks *shape*, not existence — it does not query any store.
    """
    if entity not in ID_PREFIXES:
        raise ValueError(f"Unknown entity name: {entity!r}. Known entities: {sorted(ID_PREFIXES)}")

    prefix = ID_PREFIXES[entity]
    expected_start = f"{prefix}_"
    return value.startswith(expected_start) and len(value) > len(expected_start)
