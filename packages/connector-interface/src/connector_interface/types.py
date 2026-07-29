"""Support types for the Connector Interface's `pushAction` and
`healthCheck` operations.

Only the two envelope types (EngineeringEventEnvelope,
CommercialArtifactSnapshot) are given a full field-by-field spec anywhere in
the frozen docs. The three types below — ActionPayload, DispatchReceipt,
ConnectionHealth — are named only by the shape of their use:

- `pushAction(action: ActionPayload) -> DispatchReceipt` — docs/03
  §1 and docs/07 §7. Doc03 §1: "always returns a receipt, never assumes
  success."
- `healthCheck() -> ConnectionHealth` — docs/03 §1, described only as
  "scope granted, last successful sync, error state."

Their fields below are the minimal, literal translation of exactly what the
Reference Execution Trace's two dispatch calls (Phases 11.3, 12.2) and the
email delivery-confirmation contract (docs/07 §7) actually carry, generalized
to a single cross-connector shape — never inventing a connector-specific
field (e.g. an email "to" address or a SAP OData field name) that belongs
inside one adapter's own mapper layer, not this shared package.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from domain_models.action import ActionType

# docs/07_Downstream_Implementation_Blueprint.md §7's email delivery
# confirmation contract: `status: SENT|DELIVERED|FAILED`.
DispatchStatus = Literal["SENT", "DELIVERED", "FAILED"]


class ActionPayload(BaseModel):
    """What `pushAction` sends to a Connector adapter for one approved
    Action.

    Deliberately generic: an adapter's own `mapper/` layer is responsible for
    turning this into whatever the target system actually needs (an email's
    to/subject/body, or a SAP OData PATCH body) — this shared type only
    carries what every connector needs regardless of target system, per the
    Reference Trace's own two dispatch calls (Phases 11.3 and 12.2), which
    share exactly this much: which action, what was drafted, which artifact
    it's for, and an idempotency key.
    """

    model_config = ConfigDict(frozen=True)

    action_id: str = Field(min_length=1)
    action_type: ActionType
    drafted_content: str = Field(min_length=1)
    target_artifact_ref: str = Field(
        min_length=1,
        description="Which Commercial Artifact this dispatch is for; the adapter resolves this to the target system's real identifier via the artifact identity map.",
    )
    idempotency_key: str = Field(
        min_length=1,
        description="docs/03 §10: 'every dispatch carries an idempotency key so a retried send can never double-notify a vendor or double-write an ERP hold.'",
    )


class DispatchReceipt(BaseModel):
    """What `pushAction` always returns — never assumes success (docs/03 §1)."""

    model_config = ConfigDict(frozen=True)

    dispatch_id: str = Field(min_length=1)
    status: DispatchStatus
    detail: str | None = Field(
        default=None,
        description="Optional human-readable detail, e.g. an error message when status is FAILED.",
    )


class ConnectionHealth(BaseModel):
    """What `healthCheck` returns: scope granted, last successful sync,
    error state (docs/03 §1, verbatim)."""

    model_config = ConfigDict(frozen=True)

    source_system: str = Field(min_length=1)
    scope_granted: str = Field(
        min_length=1,
        description="e.g. 'partial:[rfis,submittals,documents]' or 'full' — mirrors acting_credential_scope's format.",
    )
    last_successful_sync: datetime | None = None
    error_state: str | None = Field(
        default=None,
        description="None means healthy; otherwise a free-text description of what's wrong.",
    )
