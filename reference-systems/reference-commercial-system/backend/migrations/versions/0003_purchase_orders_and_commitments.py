"""purchase orders, po lines, po schedule lines, commitments

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-13

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("po_number", sa.String(32), nullable=True),
        sa.Column("vendor_id", sa.Integer(), sa.ForeignKey("vendors.id"), nullable=False),
        sa.Column("contract_id", sa.Integer(), sa.ForeignKey("contracts.id"), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("payment_terms", sa.String(64), nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default="DRAFT"),
        sa.Column("acknowledged", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivery_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("final_invoice", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("company_code", sa.String(16), nullable=True),
        sa.Column("plant", sa.String(16), nullable=True),
        sa.Column("purchasing_org", sa.String(16), nullable=True),
        sa.Column("business_unit", sa.String(16), nullable=True),
    )
    op.create_index("ix_purchase_orders_vendor_id", "purchase_orders", ["vendor_id"])
    op.create_index("ix_purchase_orders_company_code", "purchase_orders", ["company_code"])
    op.create_index("ix_purchase_orders_changed_at", "purchase_orders", ["changed_at"])
    op.create_index("uq_purchase_orders_po_number", "purchase_orders", ["po_number"], unique=True)

    op.create_table(
        "po_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("po_id", sa.Integer(), sa.ForeignKey("purchase_orders.id"), nullable=False),
        sa.Column("line_no", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(300), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("uom", sa.String(16), nullable=False),
        sa.Column("unit_price", sa.Numeric(16, 2), nullable=False),
        sa.Column("value", sa.Numeric(16, 2), nullable=False),
        sa.Column("cost_code_id", sa.Integer(), sa.ForeignKey("cost_codes.id"), nullable=True),
        sa.Column("spec_section_refs", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("lifecycle_position", sa.String(16), nullable=False, server_default="draft"),
    )
    op.create_index("ix_po_lines_po_id", "po_lines", ["po_id"])

    op.create_table(
        "po_schedule_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("po_line_id", sa.Integer(), sa.ForeignKey("po_lines.id"), nullable=False),
        sa.Column("schedule_no", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("required_on_site_date", sa.Date(), nullable=True),
        sa.Column("promised_date", sa.Date(), nullable=True),
        sa.Column("linked_schedule_activity_ref", sa.String(32), nullable=True),
        sa.Column("delivery_status", sa.String(24), nullable=False, server_default="SCHEDULED"),
    )
    op.create_index("ix_po_schedule_lines_po_line_id", "po_schedule_lines", ["po_line_id"])

    op.create_table(
        "commitments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_type", sa.String(16), nullable=False),
        sa.Column("cost_code_id", sa.Integer(), sa.ForeignKey("cost_codes.id"), nullable=False),
        sa.Column("po_id", sa.Integer(), sa.ForeignKey("purchase_orders.id"), nullable=True),
        sa.Column("committed_amount", sa.Numeric(16, 2), nullable=False),
        sa.Column("relieved_amount", sa.Numeric(16, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="OPEN"),
        sa.Column("company_code", sa.String(16), nullable=True),
        sa.Column("plant", sa.String(16), nullable=True),
        sa.Column("purchasing_org", sa.String(16), nullable=True),
        sa.Column("business_unit", sa.String(16), nullable=True),
    )
    op.create_index("ix_commitments_cost_code_id", "commitments", ["cost_code_id"])


def downgrade() -> None:
    op.drop_table("commitments")
    op.drop_table("po_schedule_lines")
    op.drop_table("po_lines")
    op.drop_table("purchase_orders")
