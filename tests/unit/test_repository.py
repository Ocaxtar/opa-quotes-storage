"""Unit tests for QuoteRepository."""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock

import pytest
from opa_quotes_storage.repository import QuoteRepository, QuoteSchema
from pydantic import ValidationError


class TestQuoteSchema:
    """Tests for QuoteSchema validation."""

    def test_valid_quote(self):
        """Test validating a valid quote."""
        quote_data = {
            "symbol": "aapl",  # Will be uppercased
            "timestamp": datetime(2025, 12, 22, 10, 0, tzinfo=UTC),
            "close": 180.50,
        }

        quote = QuoteSchema(**quote_data)

        assert quote.symbol == "AAPL"  # Uppercased
        assert quote.close == Decimal("180.50")

    def test_symbol_validation_empty(self):
        """Test that empty symbol raises error."""
        with pytest.raises(ValidationError) as exc_info:
            QuoteSchema(symbol="", timestamp=datetime.now(UTC))

        assert "symbol" in str(exc_info.value)

    def test_symbol_validation_too_long(self):
        """Test that symbol >10 chars raises error."""
        with pytest.raises(ValidationError):
            QuoteSchema(symbol="VERYLONGSYMBOL", timestamp=datetime.now(UTC))

    def test_timestamp_utc_conversion(self):
        """Test that naive datetime gets UTC timezone."""
        naive_dt = datetime(2025, 12, 22, 10, 0)  # No timezone

        quote = QuoteSchema(symbol="AAPL", timestamp=naive_dt)

        assert quote.timestamp.tzinfo == UTC

    def test_negative_prices_rejected(self):
        """Test that negative prices raise error."""
        with pytest.raises(ValidationError):
            QuoteSchema(symbol="AAPL", timestamp=datetime.now(UTC), close=-10.50)

    def test_all_fields_valid(self):
        """Test quote with all fields populated."""
        quote_data = {
            "symbol": "MSFT",
            "timestamp": datetime(2025, 12, 22, 10, 0, tzinfo=UTC),
            "open": 420.10,
            "high": 422.50,
            "low": 419.00,
            "close": 421.75,
            "volume": 1234567,
            "bid": 421.70,
            "ask": 421.80,
            "source": "yfinance",
        }

        quote = QuoteSchema(**quote_data)

        assert quote.symbol == "MSFT"
        assert quote.volume == 1234567
        assert quote.source == "yfinance"


class TestQuoteRepository:
    """Tests for QuoteRepository."""

    def test_init(self):
        """Test repository initialization."""
        mock_session = Mock()
        repo = QuoteRepository(session=mock_session)

        assert repo.session == mock_session

    def test_bulk_insert_validates_data(self):
        """Test that bulk_insert validates quotes."""
        mock_session = Mock()
        repo = QuoteRepository(session=mock_session)

        # Invalid quote (empty symbol)
        with pytest.raises(ValidationError):
            repo.bulk_insert([{"symbol": "", "timestamp": datetime.now(UTC)}])

    def test_bulk_insert_success(self):
        """Test successful bulk insert."""
        mock_session = Mock()
        repo = QuoteRepository(session=mock_session)

        quotes = [
            {
                "symbol": "AAPL",
                "timestamp": datetime(2025, 12, 22, 10, 0, tzinfo=UTC),
                "close": 180.50,
            }
        ]

        count = repo.bulk_insert(quotes)

        assert count == 1
        assert mock_session.bulk_save_objects.called
        assert mock_session.commit.called

    def test_bulk_insert_multiple_quotes(self):
        """Test inserting multiple quotes."""
        mock_session = Mock()
        repo = QuoteRepository(session=mock_session)

        quotes = [
            {
                "symbol": "AAPL",
                "timestamp": datetime(2025, 12, 22, 10, i, tzinfo=UTC),
                "close": 180.00 + i,
            }
            for i in range(10)
        ]

        count = repo.bulk_insert(quotes)

        assert count == 10

    def test_get_quotes_builds_correct_query(self):
        """Test that get_quotes builds correct SQLAlchemy query."""
        mock_session = Mock()
        mock_execute = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_execute.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_execute

        repo = QuoteRepository(session=mock_session)

        start = datetime(2025, 12, 1, tzinfo=UTC)
        end = datetime(2025, 12, 31, tzinfo=UTC)

        repo.get_quotes("AAPL", start, end)

        assert mock_session.execute.called

    def test_get_quotes_with_limit(self):
        """Test get_quotes with limit parameter."""
        mock_session = Mock()
        mock_execute = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_execute.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_execute

        repo = QuoteRepository(session=mock_session)

        repo.get_quotes("AAPL", datetime(2025, 12, 1), datetime(2025, 12, 31), limit=100)

        assert mock_session.execute.called

    def test_get_latest_quote(self):
        """Test getting latest quote."""
        mock_session = Mock()
        mock_execute = MagicMock()
        mock_execute.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_execute

        repo = QuoteRepository(session=mock_session)

        result = repo.get_latest_quote("AAPL")

        assert result is None
        assert mock_session.execute.called

    def test_get_intraday_quotes(self):
        """Test getting intraday quotes."""
        mock_session = Mock()
        mock_execute = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_execute.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_execute

        repo = QuoteRepository(session=mock_session)

        result = repo.get_intraday_quotes("AAPL", datetime(2025, 12, 22, tzinfo=UTC))

        assert result == []
        assert mock_session.execute.called

    def test_symbol_uppercase_conversion(self):
        """Test that symbols are converted to uppercase."""
        mock_session = Mock()
        mock_execute = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_execute.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_execute

        repo = QuoteRepository(session=mock_session)

        # Should convert to uppercase
        repo.get_quotes(
            "aapl",  # lowercase
            datetime(2025, 12, 1),
            datetime(2025, 12, 31),
        )

        assert mock_session.execute.called
