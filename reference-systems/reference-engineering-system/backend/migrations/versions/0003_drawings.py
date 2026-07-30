"""drawings, drawing versions, revision clouds, drawing-version location refs

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-31

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
        "drawings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("sheet_number", sa.String(24), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column(
            "discipline_code", sa.String(4), sa.ForeignKey("disciplines.code"), nullable=False
        ),
        sa.Column("current_version_id", sa.Integer(), nullable=True),
    )
    op.create_index("ix_drawings_project_id", "drawings", ["project_id"])

    op.create_table(
        "drawing_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("drawing_id", sa.Integer(), sa.ForeignKey("drawings.id"), nullable=False),
        sa.Column("revision_label", sa.String(24), nullable=False),
        sa.Column("issuance_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="DRAFT"),
        sa.Column(
            "discipline_code", sa.String(4), sa.ForeignKey("disciplines.code"), nullable=False
        ),
        sa.Column("superseded_by_id", sa.Integer(), sa.ForeignKey("drawing_versions.id"), nullable=True),
    )
    op.create_index("ix_drawing_versions_drawing_id", "drawing_versions", ["drawing_id"])

    # Circular FK (drawings.current_version_id -> drawing_versions.id) added
    # after both tables exist, matching the ORM's use_alter=True declaration.
    op.create_foreign_key(
        "fk_drawings_current_version_id",
        "drawings",
        "drawing_versions",
        ["current_version_id"],
        ["id"],
    )

    op.create_table(
        "drawing_version_revision_clouds",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "version_id", sa.Integer(), sa.ForeignKey("drawing_versions.id"), nullable=False
        ),
        sa.Column("area", sa.String(100), nullable=False),
        sa.Column("delta_number", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(400), nullable=False),
    )
    op.create_index(
        "ix_drawing_version_revision_clouds_version_id",
        "drawing_version_revision_clouds",
        ["version_id"],
    )

    op.create_table(
        "drawing_version_locations",
        sa.Column(
            "version_id", sa.Integer(), sa.ForeignKey("drawing_versions.id"), primary_key=True
        ),
        sa.Column("location_id", sa.Integer(), sa.ForeignKey("locations.id"), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("drawing_version_locations")
    op.drop_table("drawing_version_revision_clouds")
    op.drop_constraint("fk_drawings_current_version_id", "drawings", type_="foreignkey")
    op.drop_table("drawing_versions")
    op.drop_table("drawings")
