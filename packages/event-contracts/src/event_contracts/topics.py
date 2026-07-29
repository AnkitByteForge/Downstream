"""Event Bus topic name constants.

The ten topics this scope requires, per
docs/07_Downstream_Implementation_Blueprint.md §8 ("All ten are the
complete topic list this scope requires") — a deliberately narrower list
than docs/03_Downstream_Systems_Architecture.md §3's eleven-entry canonical
topics table, which additionally names `graph.updated`. `graph.updated` is
real, frozen-architecture surface for a later milestone (the Graph Layer as
an independently-updated component the Reasoning Pipeline subscribes to);
it is intentionally not given a schema here because docs/07 §8 explicitly
scopes this package's topic list down to the ten Milestone-1 topics and
says so in as many words.

Every topic is partitioned by `project_id`, ordered at-least-once within
that partition (docs/03 §3).
"""

from __future__ import annotations

TRIGGER_DETECTED = "trigger.detected"
KEYS_RESOLVED = "keys.resolved"
EVENT_CREATED = "event.created"
IMPACT_TIERED = "impact.tiered"
SEVERITY_COMPUTED = "severity.computed"
ACTION_DRAFTED = "action.drafted"
ACTION_APPROVED = "action.approved"
ACTION_DISPATCHED = "action.dispatched"
ACTION_CONFIRMED = "action.confirmed"
EVENT_CLOSED = "event.closed"

ALL_TOPICS = (
    TRIGGER_DETECTED,
    KEYS_RESOLVED,
    EVENT_CREATED,
    IMPACT_TIERED,
    SEVERITY_COMPUTED,
    ACTION_DRAFTED,
    ACTION_APPROVED,
    ACTION_DISPATCHED,
    ACTION_CONFIRMED,
    EVENT_CLOSED,
)

# The partition key every topic above is ordered by (docs/03 §3).
PARTITION_KEY_FIELD = "project_id"
