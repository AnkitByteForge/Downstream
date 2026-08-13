from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.entities.user import OAuthClient, OAuthToken, User
from domain.repositories.user_repository import OAuthClientRepository, OAuthTokenRepository, UserRepository
from domain.value_objects import PermissionScope
from infrastructure.persistence.orm_models import OAuthClientModel, OAuthTokenModel, UserModel


def _user_to_domain(row: UserModel) -> User:
    return User(id=row.id, name=row.name, email=row.email, role=row.role, password_hash=row.password_hash)


def _client_to_domain(row: OAuthClientModel) -> OAuthClient:
    return OAuthClient(
        id=row.id,
        client_id=row.client_id,
        client_secret_hash=row.client_secret_hash,
        company_code=row.company_code,
        permission_scope=PermissionScope(resource_types=frozenset(row.permission_scope or [])),
    )


def _token_to_domain(row: OAuthTokenModel) -> OAuthToken:
    return OAuthToken(id=row.id, access_token=row.access_token, client_id=row.client_id, expires_at=row.expires_at)


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, user: User) -> User:
        row = UserModel(name=user.name, email=user.email, role=user.role, password_hash=user.password_hash)
        self._session.add(row)
        self._session.flush()
        return _user_to_domain(row)

    def get(self, user_id: int) -> User | None:
        row = self._session.get(UserModel, user_id)
        return _user_to_domain(row) if row else None

    def get_by_email(self, email: str) -> User | None:
        row = self._session.execute(select(UserModel).where(UserModel.email == email)).scalar_one_or_none()
        return _user_to_domain(row) if row else None


class SqlAlchemyOAuthClientRepository(OAuthClientRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, client: OAuthClient) -> OAuthClient:
        row = OAuthClientModel(
            client_id=client.client_id,
            client_secret_hash=client.client_secret_hash,
            company_code=client.company_code,
            permission_scope=sorted(client.permission_scope.resource_types),
        )
        self._session.add(row)
        self._session.flush()
        return _client_to_domain(row)

    def get_by_client_id(self, client_id: str) -> OAuthClient | None:
        row = self._session.execute(
            select(OAuthClientModel).where(OAuthClientModel.client_id == client_id)
        ).scalar_one_or_none()
        return _client_to_domain(row) if row else None


class SqlAlchemyOAuthTokenRepository(OAuthTokenRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, token: OAuthToken) -> OAuthToken:
        row = OAuthTokenModel(
            access_token=token.access_token, client_id=token.client_id, expires_at=token.expires_at
        )
        self._session.add(row)
        self._session.flush()
        return _token_to_domain(row)

    def get_by_access_token(self, access_token: str) -> OAuthToken | None:
        row = self._session.execute(
            select(OAuthTokenModel).where(OAuthTokenModel.access_token == access_token)
        ).scalar_one_or_none()
        return _token_to_domain(row) if row else None
