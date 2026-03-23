"""add expires_at column

Revision ID: a1b2c3d4e5f6
Revises: 8d6db6ffc255
Create Date: 2026-03-23 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "8d6db6ffc255"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add optional expires_at column to urls table."""
    op.add_column(
        "urls",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Remove expires_at column from urls table."""
    op.drop_column("urls", "expires_at")
