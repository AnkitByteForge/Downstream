"""One versioned schema per Event Bus topic — per packages/event-contracts'
scope in docs/07_Downstream_Implementation_Blueprint.md §2 and the exact
ten-topic list in §8.
"""

from event_contracts.action_approved import ActionApproved
from event_contracts.action_confirmed import ActionConfirmed
from event_contracts.action_dispatched import ActionDispatched
from event_contracts.action_drafted import ActionDrafted
from event_contracts.event_closed import EventClosed
from event_contracts.event_created import EventCreated
from event_contracts.impact_tiered import ImpactTiered
from event_contracts.keys_resolved import KeyCandidate, KeysResolved
from event_contracts.severity_computed import SeverityComputed
from event_contracts.topics import (
    ACTION_APPROVED,
    ACTION_CONFIRMED,
    ACTION_DISPATCHED,
    ACTION_DRAFTED,
    ALL_TOPICS,
    EVENT_CLOSED,
    EVENT_CREATED,
    IMPACT_TIERED,
    KEYS_RESOLVED,
    PARTITION_KEY_FIELD,
    SEVERITY_COMPUTED,
    TRIGGER_DETECTED,
)
from event_contracts.trigger_detected import TriggerDetected

# Maps each topic name constant to the Pydantic model that validates its
# payload — the one place a consumer/publisher needs to look up "what shape
# does this topic carry."
TOPIC_SCHEMAS: dict[str, type] = {
    TRIGGER_DETECTED: TriggerDetected,
    KEYS_RESOLVED: KeysResolved,
    EVENT_CREATED: EventCreated,
    IMPACT_TIERED: ImpactTiered,
    SEVERITY_COMPUTED: SeverityComputed,
    ACTION_DRAFTED: ActionDrafted,
    ACTION_APPROVED: ActionApproved,
    ACTION_DISPATCHED: ActionDispatched,
    ACTION_CONFIRMED: ActionConfirmed,
    EVENT_CLOSED: EventClosed,
}

__all__ = [
    "ACTION_APPROVED",
    "ACTION_CONFIRMED",
    "ACTION_DISPATCHED",
    "ACTION_DRAFTED",
    "ALL_TOPICS",
    "EVENT_CLOSED",
    "EVENT_CREATED",
    "KEYS_RESOLVED",
    "PARTITION_KEY_FIELD",
    "SEVERITY_COMPUTED",
    "TOPIC_SCHEMAS",
    "TRIGGER_DETECTED",
    "ActionApproved",
    "ActionConfirmed",
    "ActionDispatched",
    "ActionDrafted",
    "EventClosed",
    "EventCreated",
    "ImpactTiered",
    "KeyCandidate",
    "KeysResolved",
    "SeverityComputed",
    "TriggerDetected",
]
