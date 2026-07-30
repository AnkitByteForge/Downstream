from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities import IntegrationUser, OAuthClient, OAuthToken, User


class UserRepository(ABC):
    @abstractmethod
    def get(self, user_id: int) -> User | None: ...

    @abstractmethod
    def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    def list_by_project(self, project_id: int) -> list[User]: ...

    @abstractmethod
    def add(self, user: User) -> User: ...


class IntegrationUserRepository(ABC):
    @abstractmethod
    def get(self, integration_user_id: int) -> IntegrationUser | None: ...

    @abstractmethod
    def add(self, integration_user: IntegrationUser) -> IntegrationUser: ...


class OAuthClientRepository(ABC):
    @abstractmethod
    def get(self, client_id: str) -> OAuthClient | None: ...

    @abstractmethod
    def get_by_authorization_code(self, code: str) -> OAuthClient | None: ...

    @abstractmethod
    def add(self, client: OAuthClient) -> OAuthClient: ...

    @abstractmethod
    def consume_authorization_code(self, client_id: str) -> None: ...


class OAuthTokenRepository(ABC):
    @abstractmethod
    def get_by_access_token(self, access_token: str) -> OAuthToken | None: ...

    @abstractmethod
    def get_by_refresh_token(self, refresh_token: str) -> OAuthToken | None: ...

    @abstractmethod
    def add(self, token: OAuthToken) -> OAuthToken: ...

    @abstractmethod
    def delete(self, access_token: str) -> None: ...
