from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.entities import IntegrationUser, OAuthClient, OAuthToken, User
from domain.repositories import (
    IntegrationUserRepository,
    OAuthClientRepository,
    OAuthTokenRepository,
    UserRepository,
)
from domain.value_objects import PermissionScope
from infrastructure.persistence.orm_models import (
    IntegrationUserModel,
    OAuthClientModel,
    OAuthTokenModel,
    UserModel,
)


def _user_to_domain(row: UserModel) -> User:
    return User(
        id=row.id,
        project_id=row.project_id,
        name=row.name,
        email=row.email,
        role=row.role,
        password_hash=row.password_hash,
    )


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, user_id: int) -> User | None:
        row = self._session.get(UserModel, user_id)
        return _user_to_domain(row) if row else None

    def get_by_email(self, email: str) -> User | None:
        row = self._session.execute(
            select(UserModel).where(UserModel.email == email)
        ).scalar_one_or_none()
        return _user_to_domain(row) if row else None

    def list_by_project(self, project_id: int) -> list[User]:
        rows = (
            self._session.execute(select(UserModel).where(UserModel.project_id == project_id))
            .scalars()
            .all()
        )
        return [_user_to_domain(r) for r in rows]

    def add(self, user: User) -> User:
        row = UserModel(
            project_id=user.project_id,
            name=user.name,
            email=user.email,
            role=user.role,
            password_hash=user.password_hash,
        )
        self._session.add(row)
        self._session.flush()
        return _user_to_domain(row)


class SqlAlchemyIntegrationUserRepository(IntegrationUserRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, integration_user_id: int) -> IntegrationUser | None:
        row = self._session.get(IntegrationUserModel, integration_user_id)
        if row is None:
            return None
        return IntegrationUser(
            id=row.id,
            project_id=row.project_id,
            name=row.name,
            permission_scope=PermissionScope(frozenset(row.permission_scope)),
        )

    def add(self, integration_user: IntegrationUser) -> IntegrationUser:
        row = IntegrationUserModel(
            project_id=integration_user.project_id,
            name=integration_user.name,
            permission_scope=sorted(integration_user.permission_scope.resource_types),
        )
        self._session.add(row)
        self._session.flush()
        integration_user.id = row.id
        return integration_user


class SqlAlchemyOAuthClientRepository(OAuthClientRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def _to_domain(self, row: OAuthClientModel) -> OAuthClient:
        return OAuthClient(
            client_id=row.client_id,
            client_secret_hash=row.client_secret_hash,
            integration_user_id=row.integration_user_id,
            authorization_code=row.authorization_code,
        )

    def get(self, client_id: str) -> OAuthClient | None:
        row = self._session.get(OAuthClientModel, client_id)
        return self._to_domain(row) if row else None

    def get_by_authorization_code(self, code: str) -> OAuthClient | None:
        row = self._session.execute(
            select(OAuthClientModel).where(OAuthClientModel.authorization_code == code)
        ).scalar_one_or_none()
        return self._to_domain(row) if row else None

    def add(self, client: OAuthClient) -> OAuthClient:
        row = OAuthClientModel(
            client_id=client.client_id,
            client_secret_hash=client.client_secret_hash,
            integration_user_id=client.integration_user_id,
            authorization_code=client.authorization_code,
        )
        self._session.add(row)
        self._session.flush()
        return client

    def consume_authorization_code(self, client_id: str) -> None:
        row = self._session.get(OAuthClientModel, client_id)
        row.authorization_code = None
        self._session.flush()


class SqlAlchemyOAuthTokenRepository(OAuthTokenRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def _to_domain(self, row: OAuthTokenModel) -> OAuthToken:
        return OAuthToken(
            access_token=row.access_token,
            refresh_token=row.refresh_token,
            client_id=row.client_id,
            expires_at=row.expires_at,
        )

    def get_by_access_token(self, access_token: str) -> OAuthToken | None:
        row = self._session.get(OAuthTokenModel, access_token)
        return self._to_domain(row) if row else None

    def get_by_refresh_token(self, refresh_token: str) -> OAuthToken | None:
        row = self._session.execute(
            select(OAuthTokenModel).where(OAuthTokenModel.refresh_token == refresh_token)
        ).scalar_one_or_none()
        return self._to_domain(row) if row else None

    def add(self, token: OAuthToken) -> OAuthToken:
        row = OAuthTokenModel(
            access_token=token.access_token,
            refresh_token=token.refresh_token,
            client_id=token.client_id,
            expires_at=token.expires_at,
        )
        self._session.add(row)
        self._session.flush()
        return token

    def delete(self, access_token: str) -> None:
        row = self._session.get(OAuthTokenModel, access_token)
        if row is not None:
            self._session.delete(row)
            self._session.flush()
