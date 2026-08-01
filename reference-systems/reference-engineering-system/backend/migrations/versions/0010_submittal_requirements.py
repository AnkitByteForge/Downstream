"""spec-driven submittal register entries

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-02

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "submittal_requirements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column(
            "spec_section_id", sa.Integer(), sa.ForeignKey("spec_sections.id"), nullable=False
        ),
        sa.Column("submittal_type", sa.String(40), nullable=False),
        sa.Column("category", sa.String(24), nullable=False),
    )
    op.create_index("ix_submittal_requirements_project_id", "submittal_requirements", ["project_id"])


def downgrade() -> None:
    op.drop_table("submittal_requirements")
