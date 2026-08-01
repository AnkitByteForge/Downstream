"""vendors and commitments (RES-3's own minimal, lifecycle-free Commitment)

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-02

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vendors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
    )
    op.create_index("ix_vendors_project_id", "vendors", ["project_id"])

    op.create_table(
        "commitments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("vendor_id", sa.Integer(), sa.ForeignKey("vendors.id"), nullable=False),
        sa.Column("cost_code", sa.String(32), nullable=False),
        sa.Column("description", sa.String(300), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column(
            "spec_section_id", sa.Integer(), sa.ForeignKey("spec_sections.id"), nullable=True
        ),
    )
    op.create_index("ix_commitments_project_id", "commitments", ["project_id"])


def downgrade() -> None:
    op.drop_table("commitments")
    op.drop_table("vendors")
