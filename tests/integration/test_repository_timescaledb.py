"""Integration tests for QuoteRepository with TimescaleDB."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import text

from opa_quotes_storage.repository import QuoteRepository
from opa_quotes_storage.models import RealTimeQuote


pytestmark = pytest.mark.integration


class TestQuoteRepositoryIntegration:
    """Integration tests requiring TimescaleDB."""
    
    def test_bulk_insert_and_retrieve(self, db_session):
        """Test bulk insert and retrieval."""
        repo = QuoteRepository(session=db_session)
        
        # Insert test quotes
        quotes = [
            {
                "symbol": "AAPL",
                "timestamp": datetime(2025, 12, 22, 10, 0, tzinfo=timezone.utc),
                "open": 180.00,
                "high": 181.00,
                "low": 179.50,
                "close": 180.50,
                "volume": 1000000,
                "source": "test"
            },
            {
                "symbol": "AAPL",
                "timestamp": datetime(2025, 12, 22, 10, 1, tzinfo=timezone.utc),
                "open": 180.50,
                "high": 181.50,
                "low": 180.00,
                "close": 180.75,
                "volume": 1200000,
                "source": "test"
            },
            {
                "symbol": "AAPL",
                "timestamp": datetime(2025, 12, 22, 10, 2, tzinfo=timezone.utc),
                "open": 180.75,
                "high": 182.00,
                "low": 180.50,
                "close": 181.25,
                "volume": 1500000,
                "source": "test"
            }
        ]
        
        count = repo.bulk_insert(quotes)
        assert count == 3
        
        # Retrieve and verify
        results = repo.get_quotes(
            "AAPL",
            datetime(2025, 12, 22, tzinfo=timezone.utc),
            datetime(2025, 12, 23, tzinfo=timezone.utc)
        )
        
        assert len(results) == 3
        assert float(results[0].close) == 180.50
        assert float(results[1].close) == 180.75
        assert float(results[2].close) == 181.25
        assert results[0].source == "test"
        
        # Cleanup
        db_session.execute(
            text("DELETE FROM quotes.real_time WHERE source = 'test'")
        )
        db_session.commit()
    
    def test_get_latest_quote(self, db_session):
        """Test getting the most recent quote."""
        repo = QuoteRepository(session=db_session)
        
        # Insert quotes with different timestamps
        quotes = [
            {
                "symbol": "MSFT",
                "timestamp": datetime(2025, 12, 22, 10, 0, tzinfo=timezone.utc),
                "close": 420.00,
                "source": "test"
            },
            {
                "symbol": "MSFT",
                "timestamp": datetime(2025, 12, 22, 10, 5, tzinfo=timezone.utc),
                "close": 422.00,
                "source": "test"
            },
            {
                "symbol": "MSFT",
                "timestamp": datetime(2025, 12, 22, 10, 2, tzinfo=timezone.utc),
                "close": 421.00,
                "source": "test"
            }
        ]
        
        repo.bulk_insert(quotes)
        
        # Get latest - should be 10:05 with close 422.00
        latest = repo.get_latest_quote("MSFT")
        
        assert latest is not None
        assert latest.timestamp == datetime(2025, 12, 22, 10, 5, tzinfo=timezone.utc)
        assert float(latest.close) == 422.00
        
        # Cleanup
        db_session.execute(
            text("DELETE FROM quotes.real_time WHERE source = 'test'")
        )
        db_session.commit()
    
    def test_get_intraday_quotes(self, db_session):
        """Test getting all quotes for a specific day."""
        repo = QuoteRepository(session=db_session)
        
        # Insert quotes spanning multiple days
        quotes = [
            {
                "symbol": "GOOGL",
                "timestamp": datetime(2025, 12, 21, 15, 30, tzinfo=timezone.utc),
                "close": 140.00,
                "source": "test"
            },
            {
                "symbol": "GOOGL",
                "timestamp": datetime(2025, 12, 22, 9, 30, tzinfo=timezone.utc),
                "close": 141.00,
                "source": "test"
            },
            {
                "symbol": "GOOGL",
                "timestamp": datetime(2025, 12, 22, 12, 0, tzinfo=timezone.utc),
                "close": 142.00,
                "source": "test"
            },
            {
                "symbol": "GOOGL",
                "timestamp": datetime(2025, 12, 22, 16, 0, tzinfo=timezone.utc),
                "close": 143.00,
                "source": "test"
            },
            {
                "symbol": "GOOGL",
                "timestamp": datetime(2025, 12, 23, 10, 0, tzinfo=timezone.utc),
                "close": 144.00,
                "source": "test"
            }
        ]
        
        repo.bulk_insert(quotes)
        
        # Get only Dec 22 quotes
        intraday = repo.get_intraday_quotes(
            "GOOGL",
            datetime(2025, 12, 22, tzinfo=timezone.utc)
        )
        
        assert len(intraday) == 3
        assert all(q.timestamp.date() == datetime(2025, 12, 22).date() for q in intraday)
        assert float(intraday[0].close) == 141.00
        assert float(intraday[2].close) == 143.00
        
        # Cleanup
        db_session.execute(
            text("DELETE FROM quotes.real_time WHERE source = 'test'")
        )
        db_session.commit()
    
    def test_get_quotes_with_limit(self, db_session):
        """Test query limit parameter."""
        repo = QuoteRepository(session=db_session)
        
        # Insert 10 quotes
        quotes = [
            {
                "symbol": "TSLA",
                "timestamp": datetime(2025, 12, 22, 10, i, tzinfo=timezone.utc),
                "close": 250.00 + i,
                "source": "test"
            }
            for i in range(10)
        ]
        
        repo.bulk_insert(quotes)
        
        # Get only first 5
        results = repo.get_quotes(
            "TSLA",
            datetime(2025, 12, 22, tzinfo=timezone.utc),
            datetime(2025, 12, 23, tzinfo=timezone.utc),
            limit=5
        )
        
        assert len(results) == 5
        assert float(results[0].close) == 250.00
        assert float(results[4].close) == 254.00
        
        # Cleanup
        db_session.execute(
            text("DELETE FROM quotes.real_time WHERE source = 'test'")
        )
        db_session.commit()
    
    def test_get_symbols(self, db_session):
        """Test getting list of distinct symbols."""
        repo = QuoteRepository(session=db_session)
        
        # Insert quotes for multiple symbols
        quotes = [
            {
                "symbol": sym,
                "timestamp": datetime(2025, 12, 22, 10, 0, tzinfo=timezone.utc),
                "close": 100.00,
                "source": "test"
            }
            for sym in ["AAPL", "MSFT", "GOOGL", "TSLA"]
        ]
        
        repo.bulk_insert(quotes)
        
        symbols = repo.get_symbols()
        
        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert "GOOGL" in symbols
        assert "TSLA" in symbols
        
        # Cleanup
        db_session.execute(
            text("DELETE FROM quotes.real_time WHERE source = 'test'")
        )
        db_session.commit()
    
    def test_count_quotes(self, db_session):
        """Test counting quotes."""
        repo = QuoteRepository(session=db_session)
        
        # Insert test quotes
        quotes = [
            {
                "symbol": "META",
                "timestamp": datetime(2025, 12, 22, 10, i, tzinfo=timezone.utc),
                "close": 350.00 + i,
                "source": "test"
            }
            for i in range(5)
        ]
        
        repo.bulk_insert(quotes)
        
        # Count all META quotes
        count = repo.count_quotes(symbol="META")
        assert count >= 5
        
        # Count with date range
        count_range = repo.count_quotes(
            symbol="META",
            start_date=datetime(2025, 12, 22, 10, 2, tzinfo=timezone.utc),
            end_date=datetime(2025, 12, 22, 10, 4, tzinfo=timezone.utc)
        )
        assert count_range == 3
        
        # Cleanup
        db_session.execute(
            text("DELETE FROM quotes.real_time WHERE source = 'test'")
        )
        db_session.commit()
    
    def test_case_insensitive_symbol_query(self, db_session):
        """Test that symbol queries are case-insensitive."""
        repo = QuoteRepository(session=db_session)
        
        # Insert with uppercase
        quotes = [{
            "symbol": "NVDA",
            "timestamp": datetime(2025, 12, 22, 10, 0, tzinfo=timezone.utc),
            "close": 500.00,
            "source": "test"
        }]
        
        repo.bulk_insert(quotes)
        
        # Query with lowercase - should work
        results = repo.get_quotes(
            "nvda",  # lowercase
            datetime(2025, 12, 22, tzinfo=timezone.utc),
            datetime(2025, 12, 23, tzinfo=timezone.utc)
        )
        
        assert len(results) >= 1
        assert results[0].symbol == "NVDA"
        
        # Cleanup
        db_session.execute(
            text("DELETE FROM quotes.real_time WHERE source = 'test'")
        )
        db_session.commit()


@pytest.fixture
def db_session():
    """Provide database session for integration tests."""
    import psycopg2
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Create engine
    engine = create_engine(
        "postgresql://opa_user:opa_password@localhost:5432/opa_quotes"
    )
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    # Rollback and close
    session.rollback()
    session.close()
    engine.dispose()
