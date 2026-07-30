"""core project structure: disciplines, projects, spec divisions/sections, locations

Revision ID: 0001
Revises:
Create Date: 2026-07-31

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
        "disciplines",
        sa.Column("code", sa.String(4), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
    )

    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("spec_format", sa.String(16), nullable=False, server_default="MF2020"),
    )

    op.create_table(
        "spec_divisions",
        sa.Column("number", sa.String(4), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
    )

    op.create_table(
        "spec_sections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column(
            "division_number", sa.String(4), sa.ForeignKey("spec_divisions.number"), nullable=False
        ),
        sa.Column("number", sa.String(16), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("substitution_policy", sa.String(400), nullable=True),
    )
    op.create_index("ix_spec_sections_project_id", "spec_sections", ["project_id"])

    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("locations.id"), nullable=True),
        sa.Column("tier_level", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("type", sa.String(24), nullable=False),
    )
    op.create_index("ix_locations_project_id", "locations", ["project_id"])


def downgrade() -> None:
    op.drop_table("locations")
    op.drop_table("spec_sections")
    op.drop_table("spec_divisions")
    op.drop_table("projects")
    op.drop_table("disciplines")
