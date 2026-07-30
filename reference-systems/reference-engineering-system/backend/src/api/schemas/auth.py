from __future__ import annotations

from pydantic import BaseModel


class LoginIn(BaseModel):
    email: str
    password: str


class SessionOut(BaseModel):
    user_id: int
    project_id: int
    role: str
