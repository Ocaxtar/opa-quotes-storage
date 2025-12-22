#!/usr/bin/env python3
"""Health check script for TimescaleDB connection."""

import sys
import time

import psycopg2


def check_timescaledb_health(retries: int = 5) -> bool:
    """
    Verify TimescaleDB is ready and extension is loaded.

    Args:
        retries: Number of connection attempts

    Returns:
        True if healthy, False otherwise
    """
    for i in range(retries):
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                user="opa_user",
                password="opa_password",
                database="opa_quotes",
            )
            cursor = conn.cursor()

            # Verify TimescaleDB extension
            cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'timescaledb'")
            if cursor.fetchone():
                print("✅ TimescaleDB is ready")
                conn.close()
                return True

            conn.close()
        except Exception as e:
            print(f"⏳ Waiting for TimescaleDB (attempt {i+1}/{retries}): {e}")
            time.sleep(2)

    print("❌ TimescaleDB not ready")
    return False


if __name__ == "__main__":
    sys.exit(0 if check_timescaledb_health() else 1)
