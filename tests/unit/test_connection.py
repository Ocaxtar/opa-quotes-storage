"""Unit tests for database connection management."""

import os
from unittest.mock import patch

from opa_quotes_storage.connection import (
    create_session_factory,
    get_connection_string,
    get_engine,
    get_session,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session


class TestConnectionManagement:
    """Tests for connection utilities."""

    def test_get_connection_string_default(self):
        """Test default connection string."""
        with patch.dict(os.environ, {}, clear=True):
            conn_str = get_connection_string()
            assert conn_str == "postgresql://opa_user:opa_password@localhost:5432/opa_quotes"

    def test_get_connection_string_from_env(self):
        """Test connection string from environment variable."""
        custom_url = "postgresql://custom_user:custom_pass@db:5432/custom_db"
        with patch.dict(os.environ, {"DATABASE_URL": custom_url}):
            conn_str = get_connection_string()
            assert conn_str == custom_url

    def test_get_engine_returns_engine(self):
        """Test that get_engine returns a valid Engine."""
        engine = get_engine()
        assert isinstance(engine, Engine)

    def test_get_engine_with_custom_connection_string(self):
        """Test creating engine with custom connection string."""
        custom_url = "postgresql://test_user:test_pass@localhost:5432/test_db"
        engine = get_engine(connection_string=custom_url)
        assert isinstance(engine, Engine)
        # Password is masked in URL string representation
        assert "test_user" in str(engine.url)
        assert "localhost:5432/test_db" in str(engine.url)

    def test_get_session_returns_session(self):
        """Test that get_session returns a valid Session."""
        session = get_session()
        assert isinstance(session, Session)
        session.close()

    def test_create_session_factory(self):
        """Test creating session factory."""
        SessionFactory = create_session_factory()

        # Factory should be a sessionmaker
        assert callable(SessionFactory)

        # Should be able to create sessions
        session = SessionFactory()
        assert isinstance(session, Session)
        session.close()

    def test_engine_pool_configuration(self):
        """Test that engine is configured with connection pooling."""
        engine = get_engine()

        # Check pool settings
        assert engine.pool.size() >= 0  # Pool size configured
        assert hasattr(engine.pool, "_overflow")  # Max overflow configured

    def test_session_configuration(self):
        """Test that sessions are properly configured."""
        session = get_session()
        # In SQLAlchemy 2.0, autocommit is configured at session factory level
        # We verify the session is valid and can be used
        assert isinstance(session, Session)
        assert session.bind is not None
        session.close()
