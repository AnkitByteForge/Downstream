"""human users + integration/OAuth2 auth surface

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-31

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(200), nullable=False, unique=True),
        sa.Column("role", sa.String(40), nullable=False),
        sa.Column("password_hash", sa.String(200), nullable=False),
    )
    op.create_index("ix_users_project_id", "users", ["project_id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "integration_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("permission_scope", sa.JSON(), nullable=False),
    )
    op.create_index("ix_integration_users_project_id", "integration_users", ["project_id"])

    op.create_table(
        "oauth_clients",
        sa.Column("client_id", sa.String(64), primary_key=True),
        sa.Column("client_secret_hash", sa.String(200), nullable=False),
        sa.Column(
            "integration_user_id",
            sa.Integer(),
            sa.ForeignKey("integration_users.id"),
            nullable=False,
        ),
        sa.Column("authorization_code", sa.String(64), nullable=True),
    )

    op.create_table(
        "oauth_tokens",
        sa.Column("access_token", sa.String(200), primary_key=True),
        sa.Column("refresh_token", sa.String(200), nullable=False, unique=True),
        sa.Column(
            "client_id", sa.String(64), sa.ForeignKey("oauth_clients.client_id"), nullable=False
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_oauth_tokens_refresh_token", "oauth_tokens", ["refresh_token"], unique=True)


def downgrade() -> None:
    op.drop_table("oauth_tokens")
    op.drop_table("oauth_clients")
    op.drop_table("integration_users")
    op.drop_table("users")
