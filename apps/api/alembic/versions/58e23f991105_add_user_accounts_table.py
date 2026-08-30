"""add_user_accounts_table

Revision ID: 58e23f991105
Revises: 47f53d334004
Create Date: 2026-08-28 17:32:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '58e23f991105'
down_revision: Union[str, None] = '47f53d334004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('learner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=512), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['learner_id'], ['learners.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('learner_id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_user_accounts_email'), 'user_accounts', ['email'], unique=True)
    op.create_index(op.f('ix_user_accounts_learner_id'), 'user_accounts', ['learner_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_accounts_learner_id'), table_name='user_accounts')
    op.drop_index(op.f('ix_user_accounts_email'), table_name='user_accounts')
    op.drop_table('user_accounts')
