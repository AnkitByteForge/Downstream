from __future__ import annotations

from pydantic import BaseModel


class LocationOut(BaseModel):
    id: int
    project_id: int
    parent_id: int | None
    tier_level: int
    name: str
    type: str
