from __future__ import annotations

from pydantic import BaseModel


class ModelObjectOut(BaseModel):
    id: int
    project_id: int
    discipline_code: str
    appearance_profile: str
    location_id: int | None
    resource_link_id: int | None
