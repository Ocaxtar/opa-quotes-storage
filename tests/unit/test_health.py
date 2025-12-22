"""Unit tests for health checks with mocked database."""

from unittest.mock import Mock, patch

import pytest
from psycopg2 import OperationalError

from opa_quotes_storage.health import HealthChecker


class TestHealthChecker:
    """Test HealthChecker with mocked database connections."""
    
    def test_check_database_connection_success(self):
        """Test successful database connection check."""
        with patch('psycopg2.connect') as mock_connect:
            mock_cursor = Mock()
            mock_cursor.fetchone.return_value = ["PostgreSQL 14.0 on x86_64-linux"]
            mock_conn = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            
            checker = HealthChecker()
            result = checker.check_database_connection()
            
            assert result["status"] == "healthy"
            assert result["message"] == "Database connected"
            assert "version" in result
            assert mock_cursor.execute.called
            assert mock_cursor.close.called
            assert mock_conn.close.called
    
    def test_check_database_connection_failure(self):
        """Test database connection failure."""
        with patch('psycopg2.connect', side_effect=OperationalError("Connection refused")):
            checker = HealthChecker()
            result = checker.check_database_connection()
            
            assert result["status"] == "unhealthy"
            assert "Connection refused" in result["message"]
    
    def test_check_timescaledb_extension_loaded(self):
        """Test TimescaleDB extension is loaded."""
        with patch('psycopg2.connect') as mock_connect:
            mock_cursor = Mock()
            mock_cursor.fetchone.return_value = ("timescaledb", "2.12.0")
            mock_conn = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            
            checker = HealthChecker()
            result = checker.check_timescaledb_extension()
            
            assert result["status"] == "healthy"
            assert result["message"] == "TimescaleDB extension loaded"
            assert result["version"] == "2.12.0"
    
    def test_check_timescaledb_extension_not_found(self):
        """Test TimescaleDB extension not found."""
        with patch('psycopg2.connect') as mock_connect:
            mock_cursor = Mock()
            mock_cursor.fetchone.return_value = None
            mock_conn = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            
            checker = HealthChecker()
            result = checker.check_timescaledb_extension()
            
            assert result["status"] == "unhealthy"
            assert "not found" in result["message"]
    
    def test_check_timescaledb_extension_error(self):
        """Test extension check with database error."""
        with patch('psycopg2.connect', side_effect=OperationalError("Table not found")):
            checker = HealthChecker()
            result = checker.check_timescaledb_extension()
            
            assert result["status"] == "unhealthy"
            assert "Table not found" in result["message"]
    
    def test_check_hypertable_exists(self):
        """Test hypertable exists and is operational."""
        with patch('psycopg2.connect') as mock_connect:
            mock_cursor = Mock()
            mock_cursor.fetchone.return_value = ("real_time", 5)
            mock_conn = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            
            checker = HealthChecker()
            result = checker.check_hypertable()
            
            assert result["status"] == "healthy"
            assert result["message"] == "Hypertable operational"
            assert result["chunks"] == 5
    
    def test_check_hypertable_not_found(self):
        """Test hypertable not found."""
        with patch('psycopg2.connect') as mock_connect:
            mock_cursor = Mock()
            mock_cursor.fetchone.return_value = None
            mock_conn = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            
            checker = HealthChecker()
            result = checker.check_hypertable()
            
            assert result["status"] == "unhealthy"
            assert "not found" in result["message"]
    
    def test_check_hypertable_error(self):
        """Test hypertable check with error."""
        with patch('psycopg2.connect', side_effect=OperationalError("Schema error")):
            checker = HealthChecker()
            result = checker.check_hypertable()
            
            assert result["status"] == "unhealthy"
            assert "Schema error" in result["message"]
    
    def test_check_all_healthy(self):
        """Test all checks return healthy status."""
        with patch('psycopg2.connect') as mock_connect:
            mock_cursor = Mock()
            # Setup responses for all 3 checks
            mock_cursor.fetchone.side_effect = [
                ["PostgreSQL 14.0"],  # database
                ("timescaledb", "2.12.0"),  # extension
                ("real_time", 3)  # hypertable
            ]
            mock_conn = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            
            checker = HealthChecker()
            result = checker.check_all()
            
            assert result["service"] == "opa-quotes-storage"
            assert "timestamp" in result
            assert result["overall_status"] == "healthy"
            assert result["checks"]["database"]["status"] == "healthy"
            assert result["checks"]["timescaledb"]["status"] == "healthy"
            assert result["checks"]["hypertable"]["status"] == "healthy"
    
    def test_check_all_unhealthy(self):
        """Test checks with failures."""
        with patch('psycopg2.connect', side_effect=OperationalError("Connection lost")):
            checker = HealthChecker()
            result = checker.check_all()
            
            assert result["overall_status"] == "unhealthy"
            assert result["checks"]["database"]["status"] == "unhealthy"
            assert result["checks"]["timescaledb"]["status"] == "unhealthy"
            assert result["checks"]["hypertable"]["status"] == "unhealthy"
    
    def test_overall_status_degraded(self):
        """Test degraded status when some checks fail."""
        checks = {
            "database": {"status": "healthy"},
            "timescaledb": {"status": "degraded"},
            "hypertable": {"status": "healthy"}
        }
        
        checker = HealthChecker()
        status = checker._get_overall_status(checks)
        
        assert status == "degraded"
    
    def test_overall_status_all_healthy(self):
        """Test healthy status when all checks pass."""
        checks = {
            "database": {"status": "healthy"},
            "timescaledb": {"status": "healthy"},
            "hypertable": {"status": "healthy"}
        }
        
        checker = HealthChecker()
        status = checker._get_overall_status(checks)
        
        assert status == "healthy"
    
    def test_overall_status_any_unhealthy(self):
        """Test unhealthy status when any check fails."""
        checks = {
            "database": {"status": "healthy"},
            "timescaledb": {"status": "unhealthy"},
            "hypertable": {"status": "healthy"}
        }
        
        checker = HealthChecker()
        status = checker._get_overall_status(checks)
        
        assert status == "unhealthy"
