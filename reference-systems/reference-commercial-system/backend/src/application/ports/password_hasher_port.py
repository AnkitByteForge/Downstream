from __future__ import annotations

from abc import ABC, abstractmethod


class PasswordHasherPort(ABC):
    @abstractmethod
    def hash(self, plain_text: str) -> str: ...

    @abstractmethod
    def verify(self, plain_text: str, hashed: str) -> bool: ...
