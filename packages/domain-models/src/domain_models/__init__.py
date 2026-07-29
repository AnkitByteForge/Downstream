"""Shared domain object model: Trigger, CommercialEvent, Impact, Action,
Approval — per packages/domain-models' scope in
docs/07_Downstream_Implementation_Blueprint.md §2.

These are the five objects named for this package by the blueprint. Other
entities described in docs/02_Downstream_Product_Design.md Part 5
(Organization, Project, User, Commercial Artifact, Integration, Ledger
entry, Graph/KeyIndex) belong to the services that own them and are
deliberately not modeled here — adding them would be scope invented ahead
of what this package is specified to hold.
"""

from domain_models.action import Action, ActionStatus, ActionType
from domain_models.approval import Approval, ApprovalDecision
from domain_models.commercial_event import (
    MAX_SEVERITY,
    MIN_SEVERITY,
    CommercialEvent,
    CommercialEventStatus,
)
from domain_models.impact import ConfidenceTier, Impact, ImpactStatus
from domain_models.trigger import TRIGGER_STATUS_PENDING_RESOLUTION, Trigger

__all__ = [
    "MAX_SEVERITY",
    "MIN_SEVERITY",
    "TRIGGER_STATUS_PENDING_RESOLUTION",
    "Action",
    "ActionStatus",
    "ActionType",
    "Approval",
    "ApprovalDecision",
    "CommercialEvent",
    "CommercialEventStatus",
    "ConfidenceTier",
    "Impact",
    "ImpactStatus",
    "Trigger",
]
