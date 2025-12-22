"""Health checks for opa-quotes-storage."""

from datetime import UTC, datetime
from typing import Any

import psycopg2

from .connection import get_connection_string


class HealthChecker:
    """Health check system for TimescaleDB storage."""

    def __init__(self):
        """Initialize with database connection string."""
        self.connection_string = get_connection_string()

    def check_database_connection(self) -> dict[str, Any]:
        """
        Verify PostgreSQL/TimescaleDB connection.

        Returns:
            Dict with status, message, and version info
        """
        try:
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()

            return {
                "status": "healthy",
                "message": "Database connected",
                "version": version.split()[0:2],  # "PostgreSQL 14.0"
            }
        except Exception as e:
            return {"status": "unhealthy", "message": f"Database connection failed: {str(e)}"}

    def check_timescaledb_extension(self) -> dict[str, Any]:
        """
        Verify TimescaleDB extension is loaded.

        Returns:
            Dict with status, message, and version info
        """
        try:
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT extname, extversion
                FROM pg_extension
                WHERE extname = 'timescaledb'
            """
            )
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result:
                return {
                    "status": "healthy",
                    "message": "TimescaleDB extension loaded",
                    "version": result[1],
                }
            else:
                return {"status": "unhealthy", "message": "TimescaleDB extension not found"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"Extension check failed: {str(e)}"}

    def check_hypertable(self) -> dict[str, Any]:
        """
        Verify quotes.real_time hypertable exists.

        Returns:
            Dict with status, message, and chunk count
        """
        try:
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT hypertable_name, num_chunks
                FROM timescaledb_information.hypertables
                WHERE hypertable_name = 'real_time'
            """
            )
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result:
                return {
                    "status": "healthy",
                    "message": "Hypertable operational",
                    "chunks": result[1],
                }
            else:
                return {"status": "unhealthy", "message": "Hypertable not found"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"Hypertable check failed: {str(e)}"}

    def check_all(self) -> dict[str, Any]:
        """
        Run all health checks.

        Returns:
            Complete health report with all checks and overall status
        """
        checks = {
            "database": self.check_database_connection(),
            "timescaledb": self.check_timescaledb_extension(),
            "hypertable": self.check_hypertable(),
        }

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "service": "opa-quotes-storage",
            "checks": checks,
            "overall_status": self._get_overall_status(checks),
        }

    def _get_overall_status(self, checks: dict[str, dict[str, Any]]) -> str:
        """
        Determine overall health status from individual checks.

        Args:
            checks: Dict of check results

        Returns:
            "healthy", "unhealthy", or "degraded"
        """
        statuses = [check["status"] for check in checks.values()]

        if all(s == "healthy" for s in statuses):
            return "healthy"
        elif any(s == "unhealthy" for s in statuses):
            return "unhealthy"
        else:
            return "degraded"
