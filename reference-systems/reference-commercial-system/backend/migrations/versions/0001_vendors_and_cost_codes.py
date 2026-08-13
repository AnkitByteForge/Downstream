"""vendors, vendor scope views, cost codes

Revision ID: 0001
Revises:
Create Date: 2026-08-13

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vendors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("qualification_status", sa.String(24), nullable=False, server_default="PROSPECTIVE"),
        sa.Column("performance_score", sa.Numeric(5, 2), nullable=True),
    )

    op.create_table(
        "vendor_scope_views",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vendor_id", sa.Integer(), sa.ForeignKey("vendors.id"), nullable=False),
        sa.Column("company_code", sa.String(16), nullable=True),
        sa.Column("purchasing_org", sa.String(16), nullable=True),
        sa.Column("blocked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("purchasing_terms", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_vendor_scope_views_vendor_id", "vendor_scope_views", ["vendor_id"])

    op.create_table(
        "cost_codes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("native_code", sa.String(32), nullable=False),
        sa.Column("cost_code_format", sa.String(32), nullable=False),
        sa.Column("standard_ref", sa.String(32), nullable=True),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("cost_codes.id"), nullable=True),
        sa.Column("company_code", sa.String(16), nullable=True),
        sa.Column("plant", sa.String(16), nullable=True),
        sa.Column("purchasing_org", sa.String(16), nullable=True),
        sa.Column("business_unit", sa.String(16), nullable=True),
        sa.Column("budget_baseline", sa.Numeric(16, 2), nullable=True),
        sa.Column("budget_current", sa.Numeric(16, 2), nullable=True),
        sa.Column("committed", sa.Numeric(16, 2), nullable=True),
        sa.Column("actual", sa.Numeric(16, 2), nullable=True),
        sa.Column("etc", sa.Numeric(16, 2), nullable=True),
        sa.Column("eac", sa.Numeric(16, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("cost_codes")
    op.drop_table("vendor_scope_views")
    op.drop_table("vendors")
