"""Checks table

Revision ID: c7f444a35e9c
Revises: 4a76550f1dde
Create Date: 2026-01-15 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7f444a35e9c'
down_revision: str | Sequence[str] | None = '4a76550f1dde'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'check',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum('PING', 'HTTP', 'HTTPS', 'DNS', 'TCP', name='checktypeenum'), nullable=False),
        sa.Column('target', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'SUCCESS', 'FAILED', name='checkstatusenum'), nullable=False, server_default='PENDING'),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('message', sa.String(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('check')
    op.execute(sa.text("DROP TYPE IF EXISTS checktypeenum"))
    op.execute(sa.text("DROP TYPE IF EXISTS checkstatusenum"))
