"""schedule activities + model objects (RES-5, ADR-008)

Revision ID: 0013
Revises: 0012
Create Date: 2026-08-12

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "schedule_activities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("activity_code", sa.String(40), nullable=False),
        sa.Column("type", sa.String(16), nullable=False),
        sa.Column("wbs", sa.String(60), nullable=True),
        sa.Column("delivery_milestone", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_schedule_activities_project_id", "schedule_activities", ["project_id"])

    # One directed edge table (activity -> predecessor); successors are its
    # reverse query, never a second, independently-drifting list (ADR-008).
    op.create_table(
        "schedule_activity_predecessors",
        sa.Column(
            "schedule_activity_id",
            sa.Integer(),
            sa.ForeignKey("schedule_activities.id"),
            primary_key=True,
        ),
        sa.Column(
            "predecessor_id",
            sa.Integer(),
            sa.ForeignKey("schedule_activities.id"),
            primary_key=True,
        ),
    )

    # Submittal -SCHEDULED_WITH-> ScheduleActivity (The Reference Engineering
    # System.md §16).
    op.create_table(
        "schedule_activity_submittals",
        sa.Column(
            "schedule_activity_id",
            sa.Integer(),
            sa.ForeignKey("schedule_activities.id"),
            primary_key=True,
        ),
        sa.Column("submittal_id", sa.Integer(), sa.ForeignKey("submittals.id"), primary_key=True),
    )

    op.create_table(
        "model_objects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("discipline_code", sa.String(4), nullable=False),
        sa.Column("appearance_profile", sa.String(16), nullable=False),
        sa.Column("location_id", sa.Integer(), sa.ForeignKey("locations.id"), nullable=True),
        sa.Column(
            "resource_link_id",
            sa.Integer(),
            sa.ForeignKey("schedule_activities.id"),
            nullable=True,
        ),
    )
    op.create_index("ix_model_objects_project_id", "model_objects", ["project_id"])


def downgrade() -> None:
    op.drop_table("model_objects")
    op.drop_table("schedule_activity_submittals")
    op.drop_table("schedule_activity_predecessors")
    op.drop_table("schedule_activities")
