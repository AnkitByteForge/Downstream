"""Schema for the `severity.computed` topic.

Emitted by: Reasoning Pipeline (Severity Computation sub-stage). Consumed
by: Commercial Event Service, Notification Service, Ledger, Realtime
Gateway. Exact shape per Phase 6 of
docs/05_Downstream_Reference_Execution_Trace.md
(`severity.computed { event_id: evt_7731, severity: 1 }`).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from domain_models.commercial_event import MAX_SEVERITY, MIN_SEVERITY


class SeverityComputed(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: str = Field(min_length=1)
    severity: int = Field(ge=MIN_SEVERITY, le=MAX_SEVERITY)
