"""Repository for quote data access with validation."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import and_, insert, select
from sqlalchemy.orm import Session

from .models import RealTimeQuote


class QuoteSchema(BaseModel):
    """Pydantic schema for quote validation."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, from_attributes=True
    )

    symbol: str = Field(..., min_length=1, max_length=10, description="Ticker symbol")
    timestamp: datetime = Field(..., description="Quote timestamp (UTC)")
    open: Optional[Decimal] = Field(None, ge=0, description="Opening price")
    high: Optional[Decimal] = Field(None, ge=0, description="High price")
    low: Optional[Decimal] = Field(None, ge=0, description="Low price")
    close: Optional[Decimal] = Field(None, ge=0, description="Closing price")
    volume: Optional[int] = Field(None, ge=0, description="Trading volume")
    bid: Optional[Decimal] = Field(None, ge=0, description="Bid price")
    ask: Optional[Decimal] = Field(None, ge=0, description="Ask price")
    source: Optional[str] = Field(None, max_length=50, description="Data source")

    @field_validator("symbol")
    @classmethod
    def uppercase_symbol(cls, v: str) -> str:
        """Convert symbol to uppercase."""
        return v.upper().strip()

    @field_validator("timestamp")
    @classmethod
    def ensure_utc(cls, v: datetime) -> datetime:
        """Ensure timestamp has timezone info."""
        if v.tzinfo is None:
            return v.replace(tzinfo=UTC)
        return v


class QuoteRepository:
    """
    Repository for accessing quote data in TimescaleDB.

    Provides high-performance bulk insert and query operations
    optimized for time-series data.
    """

    def __init__(self, session: Session):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def bulk_insert(self, quotes: list[dict[str, Any]], batch_size: int | None = 1000) -> int:
        """
        Insert batch of quotes efficiently with validation.

        Args:
                 quotes: List of dicts with keys: symbol, timestamp, open, high,
                     low, close, volume, bid, ask, source
                 batch_size: Number of records per insert batch (None for all)

        Returns:
            Number of quotes inserted

        Raises:
            ValidationError: If quote data is invalid

        Example:
            >>> quotes = [{
            ...     "symbol": "AAPL",
            ...     "timestamp": datetime(2025, 12, 22, 10, 0, tzinfo=timezone.utc),
            ...     "close": 180.50,
            ...     "volume": 1000000
            ... }]
            >>> count = repo.bulk_insert(quotes)
            >>> print(count)
            1
        """
        if not quotes:
            return 0

        # Validate with Pydantic
        validated = [QuoteSchema(**q).model_dump() for q in quotes]

        if not validated:
            return 0

        stmt = insert(RealTimeQuote)

        if batch_size is None or batch_size <= 0:
            batch_size = len(validated)

        for i in range(0, len(validated), batch_size):
            self.session.execute(stmt, validated[i : i + batch_size])

        self.session.commit()

        return len(validated)

    def get_quotes(
        self, symbol: str, start_date: datetime, end_date: datetime, limit: Optional[int] = None
    ) -> list[RealTimeQuote]:
        """
        Retrieve quotes for symbol in date range.

        Args:
            symbol: Ticker symbol (e.g., "AAPL")
            start_date: Start of time range (inclusive)
            end_date: End of time range (inclusive)
            limit: Max number of results (default: no limit)

        Returns:
            List of quotes ordered by timestamp ASC

        Example:
            >>> quotes = repo.get_quotes(
            ...     "AAPL",
            ...     datetime(2025, 12, 1),
            ...     datetime(2025, 12, 31)
            ... )
            >>> len(quotes)
            1000
        """
        stmt = (
            select(RealTimeQuote)
            .where(
                and_(
                    RealTimeQuote.symbol == symbol.upper(),
                    RealTimeQuote.timestamp >= start_date,
                    RealTimeQuote.timestamp <= end_date,
                )
            )
            .order_by(RealTimeQuote.timestamp.asc())
        )

        if limit:
            stmt = stmt.limit(limit)

        return list(self.session.execute(stmt).scalars().all())

    def get_latest_quote(self, symbol: str) -> Optional[RealTimeQuote]:
        """
        Get most recent quote for symbol.

        Args:
            symbol: Ticker symbol

        Returns:
            Most recent quote or None if not found

        Example:
            >>> quote = repo.get_latest_quote("AAPL")
            >>> if quote:
            ...     print(f"Latest: ${quote.close}")
            Latest: $180.50
        """
        stmt = (
            select(RealTimeQuote)
            .where(RealTimeQuote.symbol == symbol.upper())
            .order_by(RealTimeQuote.timestamp.desc())
            .limit(1)
        )

        return self.session.execute(stmt).scalar_one_or_none()

    def get_intraday_quotes(
        self, symbol: str, date: datetime, interval: str = "1m"
    ) -> list[RealTimeQuote]:
        """
        Get minute-by-minute quotes for a specific day.

        Args:
            symbol: Ticker symbol
            date: Date to retrieve (time will be ignored)
            interval: Resolution (1m, 5m, 15m, 1h) - currently returns all

        Returns:
            List of quotes for that day ordered by timestamp

        Example:
            >>> quotes = repo.get_intraday_quotes(
            ...     "AAPL",
            ...     datetime(2025, 12, 22)
            ... )
            >>> len(quotes)
            390  # Full trading day
        """
        # Set to start/end of day in UTC
        if date.tzinfo is None:
            date = date.replace(tzinfo=UTC)

        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = date.replace(hour=23, minute=59, second=59, microsecond=999999)

        return self.get_quotes(symbol, start, end)

    def get_symbols(self, limit: Optional[int] = None) -> list[str]:
        """
        Get list of distinct symbols in database.

        Args:
            limit: Max number of symbols to return

        Returns:
            List of unique ticker symbols

        Example:
            >>> symbols = repo.get_symbols(limit=10)
            >>> print(symbols)
            ['AAPL', 'MSFT', 'GOOGL', ...]
        """
        stmt = select(RealTimeQuote.symbol).distinct().order_by(RealTimeQuote.symbol.asc())

        if limit:
            stmt = stmt.limit(limit)

        return list(self.session.execute(stmt).scalars().all())

    def count_quotes(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """
        Count quotes matching criteria.

        Args:
            symbol: Filter by symbol (optional)
            start_date: Start of time range (optional)
            end_date: End of time range (optional)

        Returns:
            Number of quotes matching criteria

        Example:
            >>> count = repo.count_quotes("AAPL")
            >>> print(f"Total AAPL quotes: {count}")
            Total AAPL quotes: 50000
        """
        from sqlalchemy import func

        stmt = select(func.count()).select_from(RealTimeQuote)

        conditions = []
        if symbol:
            conditions.append(RealTimeQuote.symbol == symbol.upper())
        if start_date:
            conditions.append(RealTimeQuote.timestamp >= start_date)
        if end_date:
            conditions.append(RealTimeQuote.timestamp <= end_date)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        return self.session.execute(stmt).scalar_one()
