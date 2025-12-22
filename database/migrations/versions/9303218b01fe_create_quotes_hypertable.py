"""create_quotes_hypertable

Revision ID: 9303218b01fe
Revises: 
Create Date: 2025-12-22 12:22:46.466981

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9303218b01fe'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create quotes schema and real_time hypertable."""
    # Create schema
    op.execute("CREATE SCHEMA IF NOT EXISTS quotes")
    
    # Create table
    op.create_table(
        'real_time',
        sa.Column('symbol', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('open', sa.NUMERIC(10, 2)),
        sa.Column('high', sa.NUMERIC(10, 2)),
        sa.Column('low', sa.NUMERIC(10, 2)),
        sa.Column('close', sa.NUMERIC(10, 2)),
        sa.Column('volume', sa.BigInteger()),
        sa.Column('bid', sa.NUMERIC(10, 2)),
        sa.Column('ask', sa.NUMERIC(10, 2)),
        sa.Column('source', sa.Text()),
        sa.PrimaryKeyConstraint('symbol', 'timestamp'),
        schema='quotes'
    )
    
    # Convert to hypertable (TimescaleDB)
    op.execute("""
        SELECT create_hypertable('quotes.real_time', 'timestamp', 
                                 if_not_exists => TRUE);
    """)
    
    # Create index for timestamp DESC queries
    op.create_index(
        'idx_timestamp_desc',
        'real_time',
        ['timestamp'],
        schema='quotes',
        postgresql_using='btree',
        postgresql_ops={'timestamp': 'DESC'}
    )


def downgrade() -> None:
    """Drop hypertable and schema."""
    op.drop_table('real_time', schema='quotes')
    op.execute("DROP SCHEMA IF EXISTS quotes CASCADE")
