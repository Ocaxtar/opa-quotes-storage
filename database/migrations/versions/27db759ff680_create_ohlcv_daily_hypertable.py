"""create_ohlcv_daily_hypertable

Revision ID: 27db759ff680
Revises: 5b6e856c52a1
Create Date: 2026-01-23 11:57:33.677397

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '27db759ff680'
down_revision: Union[str, Sequence[str], None] = '5b6e856c52a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create ohlcv_daily table for historical OHLCV quotes (daily resolution)."""
    # Create table
    op.create_table(
        "ohlcv_daily",
        sa.Column("ticker", sa.VARCHAR(10), nullable=False),
        sa.Column("date", sa.DATE(), nullable=False),
        sa.Column("open", sa.FLOAT(), nullable=False),
        sa.Column("high", sa.FLOAT(), nullable=False),
        sa.Column("low", sa.FLOAT(), nullable=False),
        sa.Column("close", sa.FLOAT(), nullable=False),
        sa.Column("adj_close", sa.FLOAT(), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("ticker", "date"),
        schema="quotes",
    )

    # Convert to hypertable (TimescaleDB)
    op.execute(
        """
        SELECT create_hypertable('quotes.ohlcv_daily', 'date',
                                 if_not_exists => TRUE);
        """
    )

    # Create index for ticker queries
    op.create_index(
        "idx_ohlcv_daily_ticker",
        "ohlcv_daily",
        ["ticker"],
        schema="quotes",
        postgresql_using="btree",
    )

    # Create composite index for ticker + date range queries
    op.create_index(
        "idx_ohlcv_daily_ticker_date",
        "ohlcv_daily",
        ["ticker", "date"],
        schema="quotes",
        postgresql_using="btree",
    )


def downgrade() -> None:
    """Drop ohlcv_daily table."""
    op.drop_index("idx_ohlcv_daily_ticker_date", table_name="ohlcv_daily", schema="quotes")
    op.drop_index("idx_ohlcv_daily_ticker", table_name="ohlcv_daily", schema="quotes")
    op.drop_table("ohlcv_daily", schema="quotes")
