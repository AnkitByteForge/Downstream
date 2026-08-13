from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities.user import OAuthClient, OAuthToken, User


class UserRepository(ABC):
    @abstractmethod
    def add(self, user: User) -> User: ...

    @abstractmethod
    def get(self, user_id: int) -> User | None: ...

    @abstractmethod
    def get_by_email(self, email: str) -> User | None: ...


class OAuthClientRepository(ABC):
    @abstractmethod
    def add(self, client: OAuthClient) -> OAuthClient: ...

    @abstractmethod
    def get_by_client_id(self, client_id: str) -> OAuthClient | None: ...


class OAuthTokenRepository(ABC):
    @abstractmethod
    def add(self, token: OAuthToken) -> OAuthToken: ...

    @abstractmethod
    def get_by_access_token(self, access_token: str) -> OAuthToken | None: ...
