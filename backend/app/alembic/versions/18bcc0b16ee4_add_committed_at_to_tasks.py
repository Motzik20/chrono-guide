"""add committed_at to tasks

Revision ID: 18bcc0b16ee4
Revises: 3e75254707a3
Create Date: 2026-01-03 11:47:28.594717

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '18bcc0b16ee4'
down_revision: Union[str, None] = '3e75254707a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'tasks',
        sa.Column('committed_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('ix_tasks_committed_at', 'tasks', ['committed_at'])


def downgrade() -> None:
    op.drop_index('ix_tasks_committed_at', table_name='tasks')
    op.drop_column('tasks', 'committed_at')
