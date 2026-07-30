from __future__ import annotations


class ApplicationError(Exception):
    """Base class for errors raised by the application layer (use cases)."""


class NotFound(ApplicationError):
    def __init__(self, entity: str, identifier: object) -> None:
        self.entity = entity
        self.identifier = identifier
        super().__init__(f"{entity} not found: {identifier!r}")


class InvalidCredentials(ApplicationError):
    pass


class Unauthorized(ApplicationError):
    pass
