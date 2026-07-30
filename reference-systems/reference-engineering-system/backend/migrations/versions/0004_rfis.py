"""RFIs and their drawing/spec-section/location reference join tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-31

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rfis",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("number", sa.String(16), nullable=False),
        sa.Column("display_number", sa.String(32), nullable=False),
        sa.Column("subject", sa.String(300), nullable=False),
        sa.Column("question", sa.Text(), nullable=True),
        sa.Column("response", sa.Text(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="DRAFT"),
        sa.Column("ball_in_court_role", sa.String(24), nullable=False, server_default="assignee"),
        sa.Column("ball_in_court_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("cost_impact_flag", sa.String(16), nullable=True),
        sa.Column("cost_code", sa.String(32), nullable=True),
        sa.Column(
            "discipline_code", sa.String(4), sa.ForeignKey("disciplines.code"), nullable=True
        ),
        sa.Column("spawned_change_id", sa.Integer(), nullable=True),
        sa.Column("raw_document_ref", sa.String(200), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_rfis_project_id", "rfis", ["project_id"])

    op.create_table(
        "rfi_drawing_refs",
        sa.Column("rfi_id", sa.Integer(), sa.ForeignKey("rfis.id"), primary_key=True),
        sa.Column(
            "version_id", sa.Integer(), sa.ForeignKey("drawing_versions.id"), primary_key=True
        ),
    )

    op.create_table(
        "rfi_spec_section_refs",
        sa.Column("rfi_id", sa.Integer(), sa.ForeignKey("rfis.id"), primary_key=True),
        sa.Column(
            "spec_section_id", sa.Integer(), sa.ForeignKey("spec_sections.id"), primary_key=True
        ),
    )

    op.create_table(
        "rfi_location_refs",
        sa.Column("rfi_id", sa.Integer(), sa.ForeignKey("rfis.id"), primary_key=True),
        sa.Column("location_id", sa.Integer(), sa.ForeignKey("locations.id"), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("rfi_location_refs")
    op.drop_table("rfi_spec_section_refs")
    op.drop_table("rfi_drawing_refs")
    op.drop_table("rfis")
