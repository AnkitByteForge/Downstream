"""add fla_value/fla_unit to submittal_revisions (ADR-006)

MCA and FLA are first-class, nullable engineering fields on SubmittalRevision,
mirroring the existing capacity_value/capacity_unit pair. Backward compatible:
existing rows keep NULL until a revision supplies them.

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-07

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "submittal_revisions",
        sa.Column("fla_value", sa.Numeric(10, 2), nullable=True),
    )
    op.add_column(
        "submittal_revisions",
        sa.Column("fla_unit", sa.String(20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("submittal_revisions", "fla_unit")
    op.drop_column("submittal_revisions", "fla_value")
