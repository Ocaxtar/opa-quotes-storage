"""Unit tests for SQLAlchemy models."""

from datetime import UTC, datetime
from decimal import Decimal

from opa_quotes_storage.models import RealTimeQuote


class TestRealTimeQuote:
    """Tests for RealTimeQuote model."""

    def test_real_time_quote_creation(self):
        """Test creating a RealTimeQuote instance."""
        timestamp = datetime.now(UTC)
        quote = RealTimeQuote(symbol="AAPL", timestamp=timestamp, close=Decimal("180.50"))

        assert quote.symbol == "AAPL"
        assert quote.timestamp == timestamp
        assert quote.close == Decimal("180.50")

    def test_real_time_quote_with_all_fields(self):
        """Test creating a quote with all fields populated."""
        timestamp = datetime.now(UTC)
        quote = RealTimeQuote(
            symbol="MSFT",
            timestamp=timestamp,
            open=Decimal("420.10"),
            high=Decimal("422.50"),
            low=Decimal("419.00"),
            close=Decimal("421.75"),
            volume=1234567,
            bid=Decimal("421.70"),
            ask=Decimal("421.80"),
            source="yfinance",
        )

        assert quote.symbol == "MSFT"
        assert quote.open == Decimal("420.10")
        assert quote.high == Decimal("422.50")
        assert quote.low == Decimal("419.00")
        assert quote.close == Decimal("421.75")
        assert quote.volume == 1234567
        assert quote.bid == Decimal("421.70")
        assert quote.ask == Decimal("421.80")
        assert quote.source == "yfinance"

    def test_real_time_quote_repr(self):
        """Test string representation of quote."""
        timestamp = datetime.now(UTC)
        quote = RealTimeQuote(symbol="AAPL", timestamp=timestamp, close=Decimal("180.50"))

        repr_str = repr(quote)
        assert "AAPL" in repr_str
        assert "180.50" in repr_str
        assert "RealTimeQuote" in repr_str

    def test_real_time_quote_to_dict(self):
        """Test converting quote to dictionary."""
        timestamp = datetime(2025, 12, 22, 10, 0, 0, tzinfo=UTC)
        quote = RealTimeQuote(
            symbol="TSLA",
            timestamp=timestamp,
            open=Decimal("250.00"),
            close=Decimal("255.50"),
            volume=987654,
            source="tiingo",
        )

        quote_dict = quote.to_dict()

        assert quote_dict["symbol"] == "TSLA"
        assert quote_dict["timestamp"] == "2025-12-22T10:00:00+00:00"
        assert quote_dict["open"] == 250.00
        assert quote_dict["close"] == 255.50
        assert quote_dict["volume"] == 987654
        assert quote_dict["source"] == "tiingo"

    def test_real_time_quote_optional_fields(self):
        """Test quote with only required fields."""
        timestamp = datetime.now(UTC)
        quote = RealTimeQuote(symbol="GOOGL", timestamp=timestamp)

        assert quote.symbol == "GOOGL"
        assert quote.timestamp == timestamp
        assert quote.open is None
        assert quote.high is None
        assert quote.low is None
        assert quote.close is None
        assert quote.volume is None
        assert quote.bid is None
        assert quote.ask is None
        assert quote.source is None

    def test_table_name_and_schema(self):
        """Test that table name and schema are correctly configured."""
        assert RealTimeQuote.__tablename__ == "real_time"
        assert RealTimeQuote.__table_args__ == {"schema": "quotes"}

    def test_primary_key_columns(self):
        """Test that symbol and timestamp are part of primary key."""
        table = RealTimeQuote.__table__
        pk_columns = {col.name for col in table.primary_key.columns}

        assert "symbol" in pk_columns
        assert "timestamp" in pk_columns
        assert len(pk_columns) == 2
