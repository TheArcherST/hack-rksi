"""Enable FKs in SQLite  

Revision ID: bac8c025992f
Revises: 1dd5c68f219a
Create Date: 2025-11-25 10:06:12.083202

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bac8c025992f'
down_revision: str | Sequence[str] | None = '1dd5c68f219a'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("PRAGMA foreign_keys = ON;")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("PRAGMA foreign_keys = OFF;")
