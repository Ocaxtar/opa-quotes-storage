"""rename_symbol_to_ticker

Revision ID: 5b6e856c52a1
Revises: 1c7df15853b2
Create Date: 2026-01-19 11:11:12.126433

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b6e856c52a1'
down_revision: Union[str, Sequence[str], None] = '1c7df15853b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename column symbol to ticker in quotes.real_time table.
    
    This migration:
    1. Removes existing compression policy (references 'symbol')
    2. Disables compression temporarily
    3. Renames the column symbol -> ticker
    4. Re-enables compression with updated segmentby
    5. Re-adds compression policy
    """
    # Step 1: Remove compression policy
    op.execute(
        """
        SELECT remove_compression_policy('quotes.real_time', if_exists => TRUE);
        """
    )
    
    # Step 2: Disable compression (needed to rename segmentby column)
    op.execute(
        """
        ALTER TABLE quotes.real_time SET (timescaledb.compress = FALSE);
        """
    )
    
    # Step 3: Rename column
    op.execute(
        """
        ALTER TABLE quotes.real_time RENAME COLUMN symbol TO ticker;
        """
    )
    
    # Step 4: Re-enable compression with updated segmentby
    op.execute(
        """
        ALTER TABLE quotes.real_time SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'ticker',
            timescaledb.compress_orderby = 'timestamp DESC'
        );
        """
    )
    
    # Step 5: Re-add compression policy
    op.execute(
        """
        SELECT add_compression_policy('quotes.real_time',
                                      INTERVAL '30 days',
                                      if_not_exists => TRUE);
        """
    )


def downgrade() -> None:
    """Revert column rename from ticker to symbol.
    
    This migration:
    1. Removes compression policy
    2. Disables compression
    3. Renames the column ticker -> symbol
    4. Re-enables compression with original segmentby
    5. Re-adds compression policy
    """
    # Step 1: Remove compression policy
    op.execute(
        """
        SELECT remove_compression_policy('quotes.real_time', if_exists => TRUE);
        """
    )
    
    # Step 2: Disable compression
    op.execute(
        """
        ALTER TABLE quotes.real_time SET (timescaledb.compress = FALSE);
        """
    )
    
    # Step 3: Rename column back
    op.execute(
        """
        ALTER TABLE quotes.real_time RENAME COLUMN ticker TO symbol;
        """
    )
    
    # Step 4: Re-enable compression with original segmentby
    op.execute(
        """
        ALTER TABLE quotes.real_time SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'symbol',
            timescaledb.compress_orderby = 'timestamp DESC'
        );
        """
    )
    
    # Step 5: Re-add compression policy
    op.execute(
        """
        SELECT add_compression_policy('quotes.real_time',
                                      INTERVAL '30 days',
                                      if_not_exists => TRUE);
        """
    )
