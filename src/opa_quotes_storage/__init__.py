"""opa-quotes-storage - TimescaleDB storage for real-time market quotes."""

from .connection import (
    create_session_factory,
    get_connection_string,
    get_engine,
    get_session,
)
from .models import Base, RealTimeQuote
from .repository import QuoteRepository, QuoteSchema

__version__ = "0.1.0"

__all__ = [
    "Base",
    "RealTimeQuote",
    "get_connection_string",
    "get_engine",
    "get_session",
    "create_session_factory",
    "QuoteRepository",
    "QuoteSchema",
]
