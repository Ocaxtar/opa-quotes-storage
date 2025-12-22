"""add_retention_policies

Revision ID: 1c7df15853b2
Revises: 9303218b01fe
Create Date: 2025-12-22 12:23:15.854257

"""
from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1c7df15853b2"
down_revision: Union[str, Sequence[str], None] = "9303218b01fe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add compression and retention policies to hypertable."""
    # Enable compression on hypertable
    op.execute(
        """
        ALTER TABLE quotes.real_time SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'symbol',
            timescaledb.compress_orderby = 'timestamp DESC'
        );
    """
    )

    # Add compression policy: compress chunks older than 30 days
    op.execute(
        """
        SELECT add_compression_policy('quotes.real_time',
                                      INTERVAL '30 days',
                                      if_not_exists => TRUE);
    """
    )

    # Add retention policy: drop chunks older than 2 years
    op.execute(
        """
        SELECT add_retention_policy('quotes.real_time',
                                    INTERVAL '2 years',
                                    if_not_exists => TRUE);
    """
    )


def downgrade() -> None:
    """Remove compression and retention policies."""
    # Remove retention policy
    op.execute(
        """
        SELECT remove_retention_policy('quotes.real_time', if_exists => TRUE);
    """
    )

    # Remove compression policy
    op.execute(
        """
        SELECT remove_compression_policy('quotes.real_time', if_exists => TRUE);
    """
    )
