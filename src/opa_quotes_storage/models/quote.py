"""SQLAlchemy model for real-time market quotes."""


from sqlalchemy import NUMERIC, TIMESTAMP, BigInteger, Column, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class RealTimeQuote(Base):
    """
    Model for real-time market quotes stored in TimescaleDB hypertable.

    Attributes:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        timestamp: Quote timestamp (UTC)
        open: Opening price
        high: High price
        low: Low price
        close: Closing price
        volume: Trading volume
        bid: Bid price
        ask: Ask price
        source: Data source (e.g., 'yfinance', 'tiingo')
    """

    __tablename__ = "real_time"
    __table_args__ = {"schema": "quotes"}

    # Primary key compuesta (symbol, timestamp)
    symbol = Column(Text, primary_key=True, nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), primary_key=True, nullable=False)

    # OHLC data
    open = Column(NUMERIC(10, 2))
    high = Column(NUMERIC(10, 2))
    low = Column(NUMERIC(10, 2))
    close = Column(NUMERIC(10, 2))

    # Volume and bid/ask
    volume = Column(BigInteger)
    bid = Column(NUMERIC(10, 2))
    ask = Column(NUMERIC(10, 2))

    # Metadata
    source = Column(Text)

    def __repr__(self) -> str:
        """String representation of the quote."""
        return (
            f"<RealTimeQuote(symbol={self.symbol}, "
            f"timestamp={self.timestamp}, close={self.close})>"
        )

    def to_dict(self) -> dict:
        """Convert quote to dictionary."""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "open": float(self.open) if self.open else None,
            "high": float(self.high) if self.high else None,
            "low": float(self.low) if self.low else None,
            "close": float(self.close) if self.close else None,
            "volume": self.volume,
            "bid": float(self.bid) if self.bid else None,
            "ask": float(self.ask) if self.ask else None,
            "source": self.source,
        }
