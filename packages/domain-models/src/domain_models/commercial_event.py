"""CommercialEvent — the primary object of the whole product.

Shape per docs/03_Downstream_Systems_Architecture.md §7 and
docs/07_Downstream_Implementation_Blueprint.md §6. Status values and their
required progression (Detected → Triaged → Actioned → Contained → Closed)
per docs/02_Downstream_Product_Design.md Part 2 step 12 and Part 5.

The Commercial Event Service is the only writer of this object's state
(docs/03 §7); this model exists so every other service can validate the
shape of an Event it reads off the bus, not so any other service can
construct and persist one itself.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CommercialEventStatus = Literal["DETECTED", "TRIAGED", "ACTIONED", "CONTAINED", "CLOSED"]

# docs/03_Downstream_Systems_Architecture.md §6d: "a shipped, high-value,
# Certain impact is Severity 1; a draft, low-value, Possible impact is
# Severity 4" — severity is always in the closed range [1, 4].
MIN_SEVERITY = 1
MAX_SEVERITY = 4


class CommercialEvent(BaseModel):
    """The discrete, timestamped, owned record that an approved engineering
    change has occurred and has been evaluated against a project's live
    commercial commitments.

    Not a passive log entry: it carries a severity, a status that must reach
    a terminal state (CLOSED), and — via Impact — a blast radius that must
    each be resolved before the Event can close.
    """

    model_config = ConfigDict(frozen=True)

    event_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    trigger_id: str = Field(min_length=1)
    severity: int = Field(ge=MIN_SEVERITY, le=MAX_SEVERITY)
    status: CommercialEventStatus = "DETECTED"
    created_at: datetime | None = Field(
        default=None,
        description="When this Event was created; set by the owning service, not the caller.",
    )
    closed_at: datetime | None = Field(
        default=None,
        description="Set only once status reaches CLOSED.",
    )
