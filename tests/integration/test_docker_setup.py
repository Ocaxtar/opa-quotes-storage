"""Integration tests for Docker setup and TimescaleDB configuration."""

import subprocess

import pytest


def test_timescaledb_container_running():
    """Verify TimescaleDB container is running."""
    result = subprocess.run(
        ["docker", "ps", "--filter", "name=opa-quotes-storage-dev"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert "opa-quotes-storage-dev" in result.stdout


def test_timescaledb_extension_loaded(db_connection):
    """Verify TimescaleDB extension is loaded in the database."""
    cursor = db_connection.cursor()
    cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'timescaledb'")
    result = cursor.fetchone()
    assert result is not None
    assert result[0] == "timescaledb"


def test_database_connection_successful(db_connection):
    """Verify database connection is successful."""
    cursor = db_connection.cursor()
    cursor.execute("SELECT version();")
    result = cursor.fetchone()
    assert result is not None
    assert "PostgreSQL" in result[0]


def test_health_check_script_exits_successfully():
    """Verify health check script runs without errors."""
    result = subprocess.run(
        ["poetry", "run", "python", "scripts/setup/check_health.py"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "✅ TimescaleDB is ready" in result.stdout


@pytest.fixture
def db_connection():
    """Provide a database connection for tests."""
    import psycopg2

    conn = psycopg2.connect(
        host="localhost", port=5433, user="opa_user", password="opa_password", database="opa_quotes"
    )
    yield conn
    conn.close()
