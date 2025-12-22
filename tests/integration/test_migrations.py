"""Integration tests for Alembic migrations and TimescaleDB setup."""

import pytest
from sqlalchemy import text


class TestMigrations:
    """Tests for database migrations."""
    
    def test_hypertable_exists(self, db_connection):
        """Verify quotes.real_time hypertable exists."""
        result = db_connection.execute(text("""
            SELECT * FROM timescaledb_information.hypertables 
            WHERE hypertable_schema = 'quotes' 
            AND hypertable_name = 'real_time'
        """)).fetchone()
        
        assert result is not None, "Hypertable quotes.real_time not found"
    
    def test_table_columns(self, db_connection):
        """Verify all required columns exist in quotes.real_time."""
        result = db_connection.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'quotes' 
            AND table_name = 'real_time'
            ORDER BY ordinal_position
        """)).fetchall()
        
        columns = {row[0] for row in result}
        required_columns = {
            'symbol', 'timestamp', 'open', 'high', 'low', 
            'close', 'volume', 'bid', 'ask', 'source'
        }
        
        assert required_columns.issubset(columns), \
            f"Missing columns: {required_columns - columns}"
    
    def test_primary_key_constraint(self, db_connection):
        """Verify primary key is (symbol, timestamp)."""
        result = db_connection.execute(text("""
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid 
                AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = 'quotes.real_time'::regclass
            AND i.indisprimary
            ORDER BY a.attnum
        """)).fetchall()
        
        pk_columns = [row[0] for row in result]
        assert pk_columns == ['symbol', 'timestamp'], \
            f"Expected PK (symbol, timestamp), got {pk_columns}"
    
    def test_compression_enabled(self, db_connection):
        """Verify compression is enabled on hypertable."""
        result = db_connection.execute(text("""
            SELECT compression_enabled 
            FROM timescaledb_information.hypertables 
            WHERE hypertable_schema = 'quotes' 
            AND hypertable_name = 'real_time'
        """)).fetchone()
        
        assert result is not None, "Hypertable not found"
        assert result[0] is True, "Compression not enabled"
    
    def test_compression_policy_exists(self, db_connection):
        """Verify compression policy exists."""
        result = db_connection.execute(text("""
            SELECT * 
            FROM timescaledb_information.jobs 
            WHERE proc_schema = '_timescaledb_functions'
            AND proc_name = 'policy_compression'
            AND hypertable_name = 'real_time'
        """)).fetchone()
        
        assert result is not None, "Compression policy not found"
    
    def test_retention_policy_exists(self, db_connection):
        """Verify retention policy exists."""
        result = db_connection.execute(text("""
            SELECT * 
            FROM timescaledb_information.jobs 
            WHERE proc_schema = '_timescaledb_functions'
            AND proc_name = 'policy_retention'
            AND hypertable_name = 'real_time'
        """)).fetchone()
        
        assert result is not None, "Retention policy not found"
    
    def test_timestamp_index_exists(self, db_connection):
        """Verify timestamp DESC index exists."""
        result = db_connection.execute(text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'quotes' 
            AND tablename = 'real_time'
            AND indexname = 'idx_timestamp_desc'
        """)).fetchone()
        
        assert result is not None, "Index idx_timestamp_desc not found"
    
    def test_can_insert_quote(self, db_connection):
        """Verify we can insert a quote into the hypertable."""
        from datetime import datetime, timezone
        
        # Insert test quote
        db_connection.execute(text("""
            INSERT INTO quotes.real_time 
            (symbol, timestamp, close) 
            VALUES (:symbol, :timestamp, :close)
        """), {
            'symbol': 'TEST',
            'timestamp': datetime.now(timezone.utc),
            'close': 100.50
        })
        db_connection.commit()
        
        # Verify insert
        result = db_connection.execute(text("""
            SELECT symbol, close 
            FROM quotes.real_time 
            WHERE symbol = 'TEST'
        """)).fetchone()
        
        assert result is not None
        assert result[0] == 'TEST'
        assert float(result[1]) == 100.50
        
        # Cleanup
        db_connection.execute(text("""
            DELETE FROM quotes.real_time WHERE symbol = 'TEST'
        """))
        db_connection.commit()


@pytest.fixture
def db_connection():
    """Provide a database connection for tests."""
    import psycopg2
    
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        user="opa_user",
        password="opa_password",
        database="opa_quotes"
    )
    conn.autocommit = False
    yield conn
    conn.close()
