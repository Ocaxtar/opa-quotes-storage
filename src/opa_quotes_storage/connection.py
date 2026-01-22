"""Database connection management for opa-quotes-storage."""

import os
# OPA-325: Import for state.yaml loading
import sys

from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def get_connection_string() -> str:
    """Get database connection string from environment.
    
    OPA-325: Loads from state.yaml first, then env, then fallback
    
    Returns:
        PostgreSQL connection string
    """
    # OPA-325: Try loading from state.yaml
    default_url = "postgresql://opa_user:opa_password@localhost:5433/opa_quotes"
    
    try:
        infra_state_path = Path(__file__).parent.parent.parent / 'opa-infrastructure-state'
        if infra_state_path.exists():
            sys.path.insert(0, str(infra_state_path))
            from config_loader import get_db_config
            config = get_db_config('quotes')
            default_url = f"postgresql://{{config['user']}}:{{config['password']}}@{{config['host']}}:{{config['port']}}/{{config['database']}}"
            print(f"✓ OPA-325: Loaded DB config from state.yaml: port={{config['port']}}")
    except Exception:
        pass  # Fallback to hardcoded default
    
    return os.getenv("DATABASE_URL", default_url)


def get_engine(connection_string: Optional[str] = None) -> Engine:
    """
    Create SQLAlchemy engine.

    Args:
        connection_string: Optional custom connection string

    Returns:
        SQLAlchemy Engine instance
    """
    conn_str = connection_string or get_connection_string()
    return create_engine(
        conn_str,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,  # Verify connections before using
        echo=False,  # Set to True for SQL debugging
    )


def get_session(engine: Optional[Engine] = None) -> Session:
    """
    Create database session.

    Args:
        engine: Optional custom engine instance

    Returns:
        SQLAlchemy Session instance
    """
    eng = engine or get_engine()
    SessionLocal = sessionmaker(bind=eng, autocommit=False, autoflush=False)
    return SessionLocal()


def create_session_factory(engine: Optional[Engine] = None) -> sessionmaker:
    """
    Create session factory for dependency injection.

    Args:
        engine: Optional custom engine instance

    Returns:
        Session factory (sessionmaker)
    """
    eng = engine or get_engine()
    return sessionmaker(bind=eng, autocommit=False, autoflush=False)
