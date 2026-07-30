from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(40))
    password_hash: Mapped[str] = mapped_column(String(200))


class IntegrationUserModel(Base):
    __tablename__ = "integration_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    permission_scope: Mapped[list[str]] = mapped_column(JSON)


class OAuthClientModel(Base):
    __tablename__ = "oauth_clients"

    client_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    client_secret_hash: Mapped[str] = mapped_column(String(200))
    integration_user_id: Mapped[int] = mapped_column(ForeignKey("integration_users.id"))
    authorization_code: Mapped[str | None] = mapped_column(String(64), nullable=True)


class OAuthTokenModel(Base):
    __tablename__ = "oauth_tokens"

    access_token: Mapped[str] = mapped_column(String(200), primary_key=True)
    refresh_token: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    client_id: Mapped[str] = mapped_column(ForeignKey("oauth_clients.client_id"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
