"""revision cloud source_evidence_ref (ADR-009)

Revision ID: 0014
Revises: 0013
Create Date: 2026-08-13

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "drawing_version_revision_clouds",
        sa.Column("source_evidence_ref", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("drawing_version_revision_clouds", "source_evidence_ref")
