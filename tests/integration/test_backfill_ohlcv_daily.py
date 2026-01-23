"""Integration tests for backfill_ohlcv_daily script."""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.backfill.backfill_ohlcv_daily import (
    BackfillCheckpoint,
    fetch_ohlcv_data,
    insert_ohlcv_data,
    validate_data_quality,
)


@pytest.fixture
def temp_checkpoint_file(tmp_path):
    """Create temporary checkpoint file."""
    checkpoint_file = tmp_path / "checkpoint.json"
    return str(checkpoint_file)


class TestBackfillCheckpoint:
    """Tests for BackfillCheckpoint class."""

    def test_load_empty_checkpoint(self, temp_checkpoint_file):
        """Test loading checkpoint when file doesn't exist."""
        checkpoint = BackfillCheckpoint(temp_checkpoint_file)
        state = checkpoint.load()
        assert state["completed_tickers"] == []
        assert state["failed_tickers"] == []
        assert state["last_updated"] is None

    def test_save_and_load_checkpoint(self, temp_checkpoint_file):
        """Test saving and loading checkpoint state."""
        checkpoint = BackfillCheckpoint(temp_checkpoint_file)
        test_state = {
            "completed_tickers": ["AAPL", "MSFT"],
            "failed_tickers": [{"ticker": "INVALID", "error": "No data"}],
        }
        checkpoint.save(test_state)

        loaded_state = checkpoint.load()
        assert "AAPL" in loaded_state["completed_tickers"]
        assert "MSFT" in loaded_state["completed_tickers"]
        assert len(loaded_state["failed_tickers"]) == 1
        assert loaded_state["last_updated"] is not None

    def test_mark_completed(self, temp_checkpoint_file):
        """Test marking ticker as completed."""
        checkpoint = BackfillCheckpoint(temp_checkpoint_file)
        checkpoint.mark_completed("AAPL")
        
        state = checkpoint.load()
        assert "AAPL" in state["completed_tickers"]

    def test_mark_failed(self, temp_checkpoint_file):
        """Test marking ticker as failed."""
        checkpoint = BackfillCheckpoint(temp_checkpoint_file)
        checkpoint.mark_failed("INVALID", "No data available")
        
        state = checkpoint.load()
        assert len(state["failed_tickers"]) == 1
        assert state["failed_tickers"][0]["ticker"] == "INVALID"


@pytest.mark.integration
class TestFetchOHLCVData:
    """Integration tests for fetch_ohlcv_data (requires network)."""

    def test_fetch_valid_ticker(self):
        """Test fetching data for a valid ticker."""
        # Use a short date range to speed up test
        start_date = "2024-01-01"
        end_date = "2024-01-31"
        
        data = fetch_ohlcv_data("AAPL", start_date, end_date)
        
        assert data is not None
        assert len(data) > 0
        # Check tuple structure
        assert len(data[0]) == 8  # ticker, date, open, high, low, close, adj_close, volume
        assert data[0][0] == "AAPL"

    def test_fetch_invalid_ticker(self):
        """Test fetching data for invalid ticker."""
        data = fetch_ohlcv_data("INVALID_TICKER_XYZ", "2024-01-01", "2024-01-31")
        assert data is None


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("TEST_DB_AVAILABLE"),
    reason="Database not available for integration tests"
)
class TestInsertOHLCVData:
    """Integration tests for insert_ohlcv_data (requires database)."""

    @pytest.fixture
    def db_connection(self):
        """Create test database connection."""
        import psycopg2
        
        conn = psycopg2.connect(
            host="localhost",
            port=5433,
            database="opa_quotes",
            user="opa_user",
            password="opa_password",
        )
        yield conn
        conn.close()

    def test_insert_data(self, db_connection):
        """Test inserting OHLCV data into database."""
        test_data = [
            ("TEST", datetime(2024, 1, 1).date(), 100.0, 105.0, 99.0, 103.0, 103.0, 1000000),
            ("TEST", datetime(2024, 1, 2).date(), 103.0, 107.0, 102.0, 106.0, 106.0, 1200000),
        ]
        
        inserted = insert_ohlcv_data(db_connection, test_data)
        assert inserted == 2

        # Verify data was inserted
        with db_connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM quotes.ohlcv_daily WHERE ticker = %s",
                ("TEST",)
            )
            count = cursor.fetchone()[0]
            assert count >= 2

        # Cleanup
        with db_connection.cursor() as cursor:
            cursor.execute("DELETE FROM quotes.ohlcv_daily WHERE ticker = %s", ("TEST",))
            db_connection.commit()

    def test_insert_duplicate_updates(self, db_connection):
        """Test that inserting duplicate data updates existing records."""
        test_data = [
            ("TEST", datetime(2024, 1, 1).date(), 100.0, 105.0, 99.0, 103.0, 103.0, 1000000),
        ]
        
        # Insert first time
        insert_ohlcv_data(db_connection, test_data)
        
        # Update with different values
        updated_data = [
            ("TEST", datetime(2024, 1, 1).date(), 101.0, 106.0, 100.0, 104.0, 104.0, 1100000),
        ]
        insert_ohlcv_data(db_connection, updated_data)

        # Verify update
        with db_connection.cursor() as cursor:
            cursor.execute(
                "SELECT open, close FROM quotes.ohlcv_daily WHERE ticker = %s AND date = %s",
                ("TEST", datetime(2024, 1, 1).date())
            )
            open_val, close_val = cursor.fetchone()
            assert open_val == 101.0
            assert close_val == 104.0

        # Cleanup
        with db_connection.cursor() as cursor:
            cursor.execute("DELETE FROM quotes.ohlcv_daily WHERE ticker = %s", ("TEST",))
            db_connection.commit()


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("TEST_DB_AVAILABLE"),
    reason="Database not available for integration tests"
)
class TestValidateDataQuality:
    """Integration tests for validate_data_quality (requires database)."""

    @pytest.fixture
    def db_connection_with_data(self):
        """Create test database connection with sample data."""
        import psycopg2
        
        conn = psycopg2.connect(
            host="localhost",
            port=5433,
            database="opa_quotes",
            user="opa_user",
            password="opa_password",
        )
        
        # Insert test data
        test_data = [
            ("TESTVAL", datetime(2024, 1, 1).date(), 100.0, 105.0, 99.0, 103.0, 103.0, 1000000),
            ("TESTVAL", datetime(2024, 1, 2).date(), 103.0, 107.0, 102.0, 106.0, 106.0, 1200000),
            ("TESTVAL", datetime(2024, 1, 15).date(), 110.0, 115.0, 109.0, 113.0, 113.0, 1500000),
        ]
        insert_ohlcv_data(conn, test_data)
        
        yield conn
        
        # Cleanup
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM quotes.ohlcv_daily WHERE ticker = %s", ("TESTVAL",))
            conn.commit()
        conn.close()

    def test_validate_data_quality(self, db_connection_with_data):
        """Test data quality validation."""
        metrics = validate_data_quality(
            db_connection_with_data,
            "TESTVAL",
            "2024-01-01"
        )
        
        assert metrics["ticker"] == "TESTVAL"
        assert metrics["record_count"] >= 3
        assert metrics["min_date"] == datetime(2024, 1, 1).date()
        assert len(metrics["gaps"]) >= 1  # Gap between Jan 2 and Jan 15
