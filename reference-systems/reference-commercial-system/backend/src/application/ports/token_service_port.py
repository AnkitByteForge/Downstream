from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class SessionClaims:
    user_id: int
    role: str


class SessionTokenServicePort(ABC):
    """Human-user session auth (JWT), distinct from OAuth2 client_credentials
    integration tokens (OpaqueTokenServicePort) — kept separate so a machine
    credential's scope and a human login can never be conflated."""

    @abstractmethod
    def issue(self, claims: SessionClaims) -> str: ...

    @abstractmethod
    def verify(self, token: str) -> SessionClaims: ...


class OpaqueTokenServicePort(ABC):
    @abstractmethod
    def generate(self) -> str: ...
