"""create_quotes_alias_view

Revision ID: 737850d30a66
Revises: 27db759ff680
Create Date: 2026-01-26 11:49:00.875864

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '737850d30a66'
down_revision: Union[str, Sequence[str], None] = '27db759ff680'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create quotes.quotes VIEW as alias for quotes.real_time for backward compatibility.
    
    This VIEW allows external components (dashboard, opa-shared-utils) to query
    quotes.quotes while the actual hypertable is quotes.real_time.
    
    Background:
    - Original design: hypertable named 'real_time' 
    - External references expected 'quotes' table
    - Solution: CREATE VIEW quotes.quotes AS SELECT * FROM quotes.real_time
    """
    op.execute(
        """
        CREATE VIEW quotes.quotes AS
        SELECT 
            ticker,
            timestamp,
            open,
            high,
            low,
            close,
            volume,
            bid,
            ask,
            source
        FROM quotes.real_time;
        """
    )
    
    # Add comment explaining the view
    op.execute(
        """
        COMMENT ON VIEW quotes.quotes IS 
        'Compatibility alias for quotes.real_time hypertable. External components reference this view.';
        """
    )


def downgrade() -> None:
    """Drop quotes.quotes VIEW."""
    op.execute("DROP VIEW IF EXISTS quotes.quotes CASCADE;")
