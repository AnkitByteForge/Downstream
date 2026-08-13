"""contracts, users, oauth clients/tokens, csrf tokens

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-13

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
        "contracts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vendor_id", sa.Integer(), sa.ForeignKey("vendors.id"), nullable=False),
        sa.Column("type", sa.String(24), nullable=False),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("value", sa.Numeric(16, 2), nullable=True),
        sa.Column("retention_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("company_code", sa.String(16), nullable=True),
        sa.Column("plant", sa.String(16), nullable=True),
        sa.Column("purchasing_org", sa.String(16), nullable=True),
        sa.Column("business_unit", sa.String(16), nullable=True),
    )
    op.create_index("ix_contracts_vendor_id", "contracts", ["vendor_id"])

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(200), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("password_hash", sa.String(300), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "oauth_clients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.String(64), nullable=False),
        sa.Column("client_secret_hash", sa.String(300), nullable=False),
        sa.Column("company_code", sa.String(16), nullable=False),
        sa.Column("permission_scope", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.create_index("ix_oauth_clients_client_id", "oauth_clients", ["client_id"], unique=True)

    op.create_table(
        "oauth_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("access_token", sa.String(128), nullable=False),
        sa.Column("client_id", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_oauth_tokens_access_token", "oauth_tokens", ["access_token"], unique=True)
    op.create_index("ix_oauth_tokens_client_id", "oauth_tokens", ["client_id"])

    op.create_table(
        "csrf_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_key", sa.String(64), nullable=False),
        sa.Column("token", sa.String(64), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_csrf_tokens_actor_key", "csrf_tokens", ["actor_key"])
    op.create_index("ix_csrf_tokens_token", "csrf_tokens", ["token"], unique=True)


def downgrade() -> None:
    op.drop_table("csrf_tokens")
    op.drop_table("oauth_tokens")
    op.drop_table("oauth_clients")
    op.drop_table("users")
    op.drop_table("contracts")
