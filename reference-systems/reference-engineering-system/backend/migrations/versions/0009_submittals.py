"""submittals + submittal_revisions (ADR-004 parent/child) + their reference join tables

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-02

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "submittals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("number", sa.String(24), nullable=False),
        sa.Column(
            "spec_section_id", sa.Integer(), sa.ForeignKey("spec_sections.id"), nullable=False
        ),
        sa.Column(
            "package_id", sa.Integer(), sa.ForeignKey("submittal_packages.id"), nullable=True
        ),
        sa.Column("vendor_id", sa.Integer(), sa.ForeignKey("vendors.id"), nullable=True),
        sa.Column("commitment_id", sa.Integer(), sa.ForeignKey("commitments.id"), nullable=True),
        sa.Column("submittal_type", sa.String(40), nullable=False, server_default="shop_drawing"),
        sa.Column("category", sa.String(24), nullable=False, server_default="action"),
        sa.Column("lead_time_days", sa.Integer(), nullable=True),
        sa.Column("required_on_site_date", sa.Date(), nullable=True),
    )
    op.create_index("ix_submittals_project_id", "submittals", ["project_id"])

    op.create_table(
        "submittal_revisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("submittal_id", sa.Integer(), sa.ForeignKey("submittals.id"), nullable=False),
        sa.Column("rev_label", sa.String(24), nullable=False),
        sa.Column(
            "review_status_id",
            sa.Integer(),
            sa.ForeignKey("submittal_review_statuses.id"),
            nullable=False,
        ),
        sa.Column(
            "ball_in_court_role", sa.String(24), nullable=False, server_default="submitter"
        ),
        sa.Column(
            "ball_in_court_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column("equipment_tag", sa.String(40), nullable=True),
        sa.Column("manufacturer", sa.String(120), nullable=True),
        sa.Column("model", sa.String(80), nullable=True),
        sa.Column("capacity_value", sa.Numeric(10, 2), nullable=True),
        sa.Column("capacity_unit", sa.String(20), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disposed_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("disposition_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_submittal_revisions_submittal_id", "submittal_revisions", ["submittal_id"])

    op.create_table(
        "submittal_drawing_refs",
        sa.Column(
            "submittal_revision_id",
            sa.Integer(),
            sa.ForeignKey("submittal_revisions.id"),
            primary_key=True,
        ),
        sa.Column(
            "drawing_version_id",
            sa.Integer(),
            sa.ForeignKey("drawing_versions.id"),
            primary_key=True,
        ),
    )

    op.create_table(
        "submittal_location_refs",
        sa.Column(
            "submittal_revision_id",
            sa.Integer(),
            sa.ForeignKey("submittal_revisions.id"),
            primary_key=True,
        ),
        sa.Column(
            "location_id", sa.Integer(), sa.ForeignKey("locations.id"), primary_key=True
        ),
    )


def downgrade() -> None:
    op.drop_table("submittal_location_refs")
    op.drop_table("submittal_drawing_refs")
    op.drop_table("submittal_revisions")
    op.drop_table("submittals")
