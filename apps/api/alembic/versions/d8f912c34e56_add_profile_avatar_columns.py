"""add_profile_avatar_columns

Revision ID: d8f912c34e56
Revises: a9f812b34c5e
Create Date: 2026-08-30 16:22:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d8f912c34e56"
down_revision: Union[str, None] = "58e23f991105"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add avatar_gender and avatar_variant columns to learner_profiles."""
    op.add_column(
        "learner_profiles",
        sa.Column("avatar_gender", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "learner_profiles",
        sa.Column("avatar_variant", sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    """Remove avatar_gender and avatar_variant columns from learner_profiles."""
    op.drop_column("learner_profiles", "avatar_variant")
    op.drop_column("learner_profiles", "avatar_gender")
