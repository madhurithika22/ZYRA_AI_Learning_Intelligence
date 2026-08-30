"""add_phase7_proof_of_mastery_tables

Revision ID: e7f1a9b24c8d
Revises: 2def2ae295f4
Create Date: 2026-08-27 21:12:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e7f1a9b24c8d"
down_revision: Union[str, Sequence[str], None] = "2def2ae295f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "learning_activity_attempts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("learner_id", sa.UUID(), nullable=False),
        sa.Column("learning_path_id", sa.UUID(), nullable=False),
        sa.Column("learning_path_node_id", sa.UUID(), nullable=False),
        sa.Column("resource_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("time_spent_minutes", sa.Integer(), nullable=True),
        sa.Column("completion_percentage", sa.Float(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["learner_id"], ["learners.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["learning_path_id"], ["learning_paths.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["learning_path_node_id"], ["learning_path_nodes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resource_id"], ["learning_resources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_learning_activity_attempts_learner_id"),
        "learning_activity_attempts",
        ["learner_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_learning_activity_attempts_learning_path_id"),
        "learning_activity_attempts",
        ["learning_path_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_learning_activity_attempts_learning_path_node_id"),
        "learning_activity_attempts",
        ["learning_path_node_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_learning_activity_attempts_idempotency_key"),
        "learning_activity_attempts",
        ["idempotency_key"],
        unique=False,
    )

    op.create_table(
        "mastery_check_attempts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("learner_id", sa.UUID(), nullable=False),
        sa.Column("activity_attempt_id", sa.UUID(), nullable=False),
        sa.Column("learning_path_node_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["activity_attempt_id"], ["learning_activity_attempts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["learner_id"], ["learners.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["learning_path_node_id"], ["learning_path_nodes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_mastery_check_attempts_activity_attempt_id"),
        "mastery_check_attempts",
        ["activity_attempt_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_mastery_check_attempts_learner_id"),
        "mastery_check_attempts",
        ["learner_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_mastery_check_attempts_learning_path_node_id"),
        "mastery_check_attempts",
        ["learning_path_node_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_mastery_check_attempts_idempotency_key"),
        "mastery_check_attempts",
        ["idempotency_key"],
        unique=False,
    )

    op.create_table(
        "mastery_outcomes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("learner_id", sa.UUID(), nullable=False),
        sa.Column("activity_attempt_id", sa.UUID(), nullable=False),
        sa.Column("mastery_check_id", sa.UUID(), nullable=True),
        sa.Column("skill_id", sa.UUID(), nullable=False),
        sa.Column("before_mastery", sa.Float(), nullable=False),
        sa.Column("after_mastery", sa.Float(), nullable=False),
        sa.Column("mastery_delta", sa.Float(), nullable=False),
        sa.Column("before_confidence", sa.Float(), nullable=False),
        sa.Column("after_confidence", sa.Float(), nullable=False),
        sa.Column("confidence_delta", sa.Float(), nullable=False),
        sa.Column("evidence_score", sa.Float(), nullable=False),
        sa.Column("evidence_quality", sa.Float(), nullable=False),
        sa.Column("proof_strength", sa.Float(), nullable=False),
        sa.Column("classification", sa.String(length=64), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["activity_attempt_id"], ["learning_activity_attempts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["learner_id"], ["learners.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["mastery_check_id"], ["mastery_check_attempts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_mastery_outcomes_activity_attempt_id"),
        "mastery_outcomes",
        ["activity_attempt_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_mastery_outcomes_learner_id"),
        "mastery_outcomes",
        ["learner_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_mastery_outcomes_mastery_check_id"),
        "mastery_outcomes",
        ["mastery_check_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_mastery_outcomes_skill_id"),
        "mastery_outcomes",
        ["skill_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("mastery_outcomes")
    op.drop_table("mastery_check_attempts")
    op.drop_table("learning_activity_attempts")
