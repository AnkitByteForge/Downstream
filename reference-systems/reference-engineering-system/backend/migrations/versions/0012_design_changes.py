"""design changes (ASI/CCD/BULLETIN) + reference join tables

Revision ID: 0012
Revises: 0011
Create Date: 2026-08-07

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "design_changes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("number", sa.String(24), nullable=False),
        sa.Column("display_number", sa.String(40), nullable=False),
        sa.Column("type", sa.String(16), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="DRAFT"),
        sa.Column("change_reason", sa.String(1000), nullable=True),
        sa.Column("discipline_code", sa.String(4), nullable=True),
        sa.Column("source_rfi_id", sa.Integer(), sa.ForeignKey("rfis.id"), nullable=True),
        sa.Column("ball_in_court_role", sa.String(24), nullable=False, server_default="architect"),
        sa.Column(
            "ball_in_court_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column(
            "superseded_by_id", sa.Integer(), sa.ForeignKey("design_changes.id"), nullable=True
        ),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_design_changes_project_id", "design_changes", ["project_id"])
    op.create_index("ix_design_changes_source_rfi_id", "design_changes", ["source_rfi_id"])

    op.create_table(
        "design_change_drawing_versions",
        sa.Column(
            "design_change_id", sa.Integer(), sa.ForeignKey("design_changes.id"), primary_key=True
        ),
        sa.Column(
            "drawing_version_id", sa.Integer(), sa.ForeignKey("drawing_versions.id"), primary_key=True
        ),
    )

    op.create_table(
        "design_change_spec_sections",
        sa.Column(
            "design_change_id", sa.Integer(), sa.ForeignKey("design_changes.id"), primary_key=True
        ),
        sa.Column(
            "spec_section_id", sa.Integer(), sa.ForeignKey("spec_sections.id"), primary_key=True
        ),
    )

    op.create_table(
        "design_change_locations",
        sa.Column(
            "design_change_id", sa.Integer(), sa.ForeignKey("design_changes.id"), primary_key=True
        ),
        sa.Column("location_id", sa.Integer(), sa.ForeignKey("locations.id"), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("design_change_locations")
    op.drop_table("design_change_spec_sections")
    op.drop_table("design_change_drawing_versions")
    op.drop_table("design_changes")
