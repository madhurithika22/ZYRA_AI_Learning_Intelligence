"""add_phase10_replanning_versioning_columns

Revision ID: a9f812b34c5e
Revises: e7f1a9b24c8d
Create Date: 2026-08-27 23:50:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a9f812b34c5e'
down_revision: Union[str, None] = 'e7f1a9b24c8d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add versioning columns to learning_paths
    op.add_column('learning_paths', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('learning_paths', sa.Column('parent_path_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('learning_paths', sa.Column('generation_reason', sa.String(length=255), nullable=True))
    op.add_column('learning_paths', sa.Column('change_summary', postgresql.JSONB(), nullable=True))
    op.create_index(op.f('ix_learning_paths_parent_path_id'), 'learning_paths', ['parent_path_id'], unique=False)
    op.create_foreign_key('fk_learning_paths_parent_path_id', 'learning_paths', 'learning_paths', ['parent_path_id'], ['id'], ondelete='SET NULL')

    # 2. Add lineage and status columns to learning_path_nodes
    op.add_column('learning_path_nodes', sa.Column('source_node_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('learning_path_nodes', sa.Column('status', sa.String(length=40), nullable=False, server_default='pending'))
    op.create_index(op.f('ix_learning_path_nodes_source_node_id'), 'learning_path_nodes', ['source_node_id'], unique=False)
    op.create_foreign_key('fk_learning_path_nodes_source_node_id', 'learning_path_nodes', 'learning_path_nodes', ['source_node_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('fk_learning_path_nodes_source_node_id', 'learning_path_nodes', type_='foreignkey')
    op.drop_index(op.f('ix_learning_path_nodes_source_node_id'), table_name='learning_path_nodes')
    op.drop_column('learning_path_nodes', 'status')
    op.drop_column('learning_path_nodes', 'source_node_id')

    op.drop_constraint('fk_learning_paths_parent_path_id', 'learning_paths', type_='foreignkey')
    op.drop_index(op.f('ix_learning_paths_parent_path_id'), table_name='learning_paths')
    op.drop_column('learning_paths', 'change_summary')
    op.drop_column('learning_paths', 'generation_reason')
    op.drop_column('learning_paths', 'parent_path_id')
    op.drop_column('learning_paths', 'version')
