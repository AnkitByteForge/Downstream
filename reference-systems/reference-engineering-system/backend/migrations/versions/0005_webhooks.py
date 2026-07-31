"""webhook subscriptions and delivery log

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-01

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "webhook_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("resource_name", sa.String(40), nullable=False),
        sa.Column("event_type", sa.String(24), nullable=False),
        sa.Column("target_url", sa.String(500), nullable=False),
        sa.Column("secret", sa.String(200), nullable=False),
    )
    op.create_index("ix_webhook_subscriptions_project_id", "webhook_subscriptions", ["project_id"])

    op.create_table(
        "webhook_deliveries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column(
            "subscription_id",
            sa.Integer(),
            sa.ForeignKey("webhook_subscriptions.id"),
            nullable=False,
        ),
        sa.Column("resource_name", sa.String(40), nullable=False),
        sa.Column("resource_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(24), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_webhook_deliveries_project_id", "webhook_deliveries", ["project_id"])


def downgrade() -> None:
    op.drop_table("webhook_deliveries")
    op.drop_table("webhook_subscriptions")
