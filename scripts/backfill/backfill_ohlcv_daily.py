"""Backfill script for historical OHLCV daily quotes (2017-2024).

Loads 7 years of daily OHLCV data for S&P 500 companies using yfinance.
Includes rate limiting, checkpoint recovery, and data quality validation.

Usage:
    python scripts/backfill/backfill_ohlcv_daily.py [--tickers-file tickers.txt] [--start-date 2017-01-01]
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import psycopg2
import yfinance as yf
from psycopg2.extras import execute_values

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/backfill_ohlcv.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_START_DATE = "2017-01-01"
DEFAULT_END_DATE = datetime.now().strftime("%Y-%m-%d")
RATE_LIMIT_DELAY = 0.5  # seconds between requests
BATCH_SIZE = 50  # Number of tickers to process before checkpoint
CHECKPOINT_FILE = "logs/backfill_checkpoint.json"

# Database connection (use environment variables in production)
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "opa_quotes",
    "user": "opa_user",
    "password": "opa_password",
}


class BackfillCheckpoint:
    """Manages checkpoint state for resumable backfill operations."""

    def __init__(self, checkpoint_file: str = CHECKPOINT_FILE):
        self.checkpoint_file = Path(checkpoint_file)
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict:
        """Load checkpoint state from file."""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, "r") as f:
                return json.load(f)
        return {"completed_tickers": [], "failed_tickers": [], "last_updated": None}

    def save(self, state: dict) -> None:
        """Save checkpoint state to file."""
        state["last_updated"] = datetime.now().isoformat()
        with open(self.checkpoint_file, "w") as f:
            json.dump(state, f, indent=2)

    def mark_completed(self, ticker: str) -> None:
        """Mark ticker as successfully completed."""
        state = self.load()
        if ticker not in state["completed_tickers"]:
            state["completed_tickers"].append(ticker)
        self.save(state)

    def mark_failed(self, ticker: str, error: str) -> None:
        """Mark ticker as failed with error message."""
        state = self.load()
        state["failed_tickers"].append({"ticker": ticker, "error": error})
        self.save(state)


def get_sp500_tickers() -> list[str]:
    """Get list of S&P 500 tickers from Wikipedia.

    Returns:
        List of ticker symbols
    """
    try:
        import pandas as pd

        table = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
        sp500_table = table[0]
        tickers = sp500_table["Symbol"].tolist()
        # Clean tickers (replace '.' with '-' for yfinance compatibility)
        tickers = [ticker.replace(".", "-") for ticker in tickers]
        logger.info(f"Loaded {len(tickers)} S&P 500 tickers")
        return tickers
    except Exception as e:
        logger.error(f"Failed to load S&P 500 tickers: {e}")
        raise


def load_tickers_from_file(file_path: str) -> list[str]:
    """Load tickers from a text file (one ticker per line).

    Args:
        file_path: Path to file containing tickers

    Returns:
        List of ticker symbols
    """
    tickers = []
    with open(file_path, "r") as f:
        for line in f:
            ticker = line.strip()
            if ticker and not ticker.startswith("#"):
                tickers.append(ticker)
    logger.info(f"Loaded {len(tickers)} tickers from {file_path}")
    return tickers


def fetch_ohlcv_data(
    ticker: str, start_date: str, end_date: str
) -> Optional[list[tuple]]:
    """Fetch OHLCV data for a single ticker using yfinance.

    Args:
        ticker: Stock ticker symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        List of tuples (ticker, date, open, high, low, close, adj_close, volume)
        or None if fetch fails
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)

        if df.empty:
            logger.warning(f"No data returned for {ticker}")
            return None

        # Convert to list of tuples for batch insert
        data = []
        for date, row in df.iterrows():
            # yfinance returns 'Close' as adjusted close by default
            data.append(
                (
                    ticker,
                    date.date(),
                    float(row["Open"]),
                    float(row["High"]),
                    float(row["Low"]),
                    float(row["Close"]),
                    float(row["Close"]),  # adj_close = close (already adjusted)
                    int(row["Volume"]),
                )
            )

        logger.info(f"Fetched {len(data)} records for {ticker}")
        return data

    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {e}")
        return None


def insert_ohlcv_data(conn, data: list[tuple]) -> int:
    """Insert OHLCV data into quotes.ohlcv_daily table.

    Args:
        conn: psycopg2 connection
        data: List of tuples (ticker, date, open, high, low, close, adj_close, volume)

    Returns:
        Number of records inserted
    """
    if not data:
        return 0

    insert_query = """
        INSERT INTO quotes.ohlcv_daily (ticker, date, open, high, low, close, adj_close, volume)
        VALUES %s
        ON CONFLICT (ticker, date) DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            adj_close = EXCLUDED.adj_close,
            volume = EXCLUDED.volume
    """

    with conn.cursor() as cursor:
        execute_values(cursor, insert_query, data)
        conn.commit()
        return len(data)


def validate_data_quality(conn, ticker: str, start_date: str) -> dict:
    """Validate data quality for a ticker.

    Args:
        conn: psycopg2 connection
        ticker: Stock ticker symbol
        start_date: Expected start date

    Returns:
        Dict with validation metrics
    """
    with conn.cursor() as cursor:
        # Count records
        cursor.execute(
            "SELECT COUNT(*) FROM quotes.ohlcv_daily WHERE ticker = %s", (ticker,)
        )
        record_count = cursor.fetchone()[0]

        # Check date range
        cursor.execute(
            "SELECT MIN(date), MAX(date) FROM quotes.ohlcv_daily WHERE ticker = %s",
            (ticker,),
        )
        min_date, max_date = cursor.fetchone()

        # Check for gaps (>5 trading days)
        cursor.execute(
            """
            SELECT date, LEAD(date) OVER (ORDER BY date) as next_date
            FROM quotes.ohlcv_daily
            WHERE ticker = %s
            ORDER BY date
        """,
            (ticker,),
        )
        gaps = []
        for row in cursor.fetchall():
            if row[1] and (row[1] - row[0]).days > 7:  # ~5 trading days = 7 calendar
                gaps.append((row[0], row[1]))

        return {
            "ticker": ticker,
            "record_count": record_count,
            "min_date": min_date,
            "max_date": max_date,
            "gaps": gaps,
        }


def run_backfill(
    tickers: list[str],
    start_date: str = DEFAULT_START_DATE,
    end_date: str = DEFAULT_END_DATE,
    resume: bool = True,
) -> dict:
    """Run backfill operation for all tickers.

    Args:
        tickers: List of ticker symbols
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        resume: Whether to resume from checkpoint

    Returns:
        Summary statistics
    """
    checkpoint = BackfillCheckpoint()
    state = checkpoint.load() if resume else {"completed_tickers": [], "failed_tickers": []}

    # Filter out already completed tickers
    pending_tickers = [
        t for t in tickers if t not in state["completed_tickers"]
    ]
    logger.info(f"Starting backfill: {len(pending_tickers)} tickers pending")

    # Connect to database
    conn = psycopg2.connect(**DB_CONFIG)
    logger.info("Connected to database")

    stats = {
        "total_tickers": len(tickers),
        "completed": len(state["completed_tickers"]),
        "failed": len(state["failed_tickers"]),
        "total_records": 0,
    }

    try:
        for i, ticker in enumerate(pending_tickers, 1):
            logger.info(
                f"Processing {ticker} ({i}/{len(pending_tickers)} pending, "
                f"{stats['completed']}/{stats['total_tickers']} total)"
            )

            # Fetch data
            data = fetch_ohlcv_data(ticker, start_date, end_date)

            if data is None:
                checkpoint.mark_failed(ticker, "No data returned")
                stats["failed"] += 1
            else:
                # Insert data
                inserted = insert_ohlcv_data(conn, data)
                stats["total_records"] += inserted
                checkpoint.mark_completed(ticker)
                stats["completed"] += 1
                logger.info(f"✅ {ticker}: {inserted} records inserted")

            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)

            # Checkpoint every batch
            if i % BATCH_SIZE == 0:
                logger.info(f"Checkpoint: {stats['completed']}/{stats['total_tickers']} completed")

    except KeyboardInterrupt:
        logger.warning("Backfill interrupted by user. Progress saved to checkpoint.")
    except Exception as e:
        logger.error(f"Backfill failed: {e}")
        raise
    finally:
        conn.close()

    return stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Backfill historical OHLCV data")
    parser.add_argument(
        "--tickers-file",
        type=str,
        help="Path to file with ticker symbols (one per line). If not provided, uses S&P 500.",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=DEFAULT_START_DATE,
        help="Start date (YYYY-MM-DD). Default: 2017-01-01",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=DEFAULT_END_DATE,
        help="End date (YYYY-MM-DD). Default: today",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Start fresh (ignore checkpoint)",
    )

    args = parser.parse_args()

    # Load tickers
    if args.tickers_file:
        tickers = load_tickers_from_file(args.tickers_file)
    else:
        tickers = get_sp500_tickers()

    # Run backfill
    logger.info(f"Starting backfill: {args.start_date} to {args.end_date}")
    stats = run_backfill(
        tickers,
        start_date=args.start_date,
        end_date=args.end_date,
        resume=not args.no_resume,
    )

    # Print summary
    logger.info("=" * 60)
    logger.info("BACKFILL SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total tickers: {stats['total_tickers']}")
    logger.info(f"Completed: {stats['completed']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"Total records: {stats['total_records']}")
    logger.info(f"Completion rate: {stats['completed']/stats['total_tickers']*100:.1f}%")


if __name__ == "__main__":
    main()
