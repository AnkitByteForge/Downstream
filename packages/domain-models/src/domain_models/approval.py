"""Approval — the immutable record of who decided what, when.

Deliberately a distinct object from Action, per
docs/02_Downstream_Product_Design.md Part 5: separated from the Action's own
(mutable-until-approved) content so the decision-audit-trail can never be
altered after the fact. Decision enum per
docs/07_Downstream_Implementation_Blueprint.md §6's `approvals` table
comment (APPROVED|REJECTED|ACKNOWLEDGED_NO_ACTION) — a superset of the two
decisions docs/07 §7's Milestone-1 approve endpoint currently accepts
(APPROVED|ACKNOWLEDGED_NO_ACTION), since REJECTED is a named, real decision
in the frozen domain even though its API/UI flow is deferred to Milestone 6
per docs/06_Downstream_Implementation_Backlog.md.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ApprovalDecision = Literal["APPROVED", "REJECTED", "ACKNOWLEDGED_NO_ACTION"]


class Approval(BaseModel):
    """Belongs to one Action. Immutable once written."""

    model_config = ConfigDict(frozen=True)

    approval_id: str = Field(min_length=1)
    action_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    decision: ApprovalDecision
    edited_content: str | None = Field(
        default=None,
        description="What (if anything) the user changed before approving.",
    )
    decided_at: datetime | None = Field(
        default=None,
        description="Set by the owning service at write time, not the caller.",
    )
