"""Action — the drafted, human-approvable containment step for one Impact.

Type enum and status progression per
docs/02_Downstream_Product_Design.md Part 5 ("Status (Drafted → Approved/
Rejected/Edited → Sent → Completed)") and the exact type values used
throughout docs/05_Downstream_Reference_Execution_Trace.md and named in
docs/07_Downstream_Implementation_Blueprint.md §6's `actions` table comment.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ActionType = Literal[
    "VENDOR_HOLD_NOTICE",
    "ERP_HOLD_FLAG",
    "ERP_RESCHEDULE",
    "FLAG_FOR_REVIEW",
]
ActionStatus = Literal["DRAFTED", "APPROVED", "REJECTED", "EDITED", "SENT", "COMPLETED"]


class Action(BaseModel):
    """Belongs to one Impact. Drafted by the Reasoning Pipeline's Grounded
    Drafting stage (docs/03 §6e) — retrieval-grounded, never introducing a
    fact the earlier stages didn't already establish.
    """

    model_config = ConfigDict(frozen=True)

    action_id: str = Field(min_length=1)
    impact_id: str = Field(min_length=1)
    type: ActionType
    drafted_content: str = Field(min_length=1)
    status: ActionStatus = "DRAFTED"
