"""Schema for the `trigger.detected` topic.

Emitted by: Ingestion & Normalization Service. Consumed by: Key Resolution
Service. Exact shape per Phase 2.4 of
docs/05_Downstream_Reference_Execution_Trace.md.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TriggerDetected(BaseModel):
    model_config = ConfigDict(frozen=True)

    trigger_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    occurred_at: datetime
