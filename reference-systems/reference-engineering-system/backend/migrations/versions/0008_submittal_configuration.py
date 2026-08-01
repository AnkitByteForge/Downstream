"""submittal packages (ADR-005) and configurable review-status vocabulary (ADR-003)

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-02

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "submittal_packages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
    )
    op.create_index("ix_submittal_packages_project_id", "submittal_packages", ["project_id"])

    op.create_table(
        "submittal_review_statuses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("gates_procurement", sa.Boolean(), nullable=False),
        sa.Column("is_terminal", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index(
        "ix_submittal_review_statuses_project_id", "submittal_review_statuses", ["project_id"]
    )


def downgrade() -> None:
    op.drop_table("submittal_review_statuses")
    op.drop_table("submittal_packages")
