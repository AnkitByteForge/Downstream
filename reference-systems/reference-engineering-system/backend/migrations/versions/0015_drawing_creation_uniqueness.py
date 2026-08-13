"""drawing/drawing_version natural-key uniqueness (ADR-009, E.4)

Deterministic idempotency backstop for the new creation API: a Drawing's
natural key is (project_id, sheet_number); a DrawingVersion's is
(drawing_id, revision_label). Verified against existing seed data before
this migration was written -- no collisions exist in either table.

Revision ID: 0015
Revises: 0014
Create Date: 2026-08-13

"""
from __future__ import annotations

from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_drawings_project_sheet_number", "drawings", ["project_id", "sheet_number"]
    )
    op.create_unique_constraint(
        "uq_drawing_versions_drawing_revision_label",
        "drawing_versions",
        ["drawing_id", "revision_label"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_drawing_versions_drawing_revision_label", "drawing_versions", type_="unique"
    )
    op.drop_constraint("uq_drawings_project_sheet_number", "drawings", type_="unique")
