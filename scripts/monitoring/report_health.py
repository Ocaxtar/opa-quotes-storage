#!/usr/bin/env python3
"""Report health to supervisor monitoring system."""

import json
import sys
from pathlib import Path

# Add src to path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from opa_quotes_storage.health import HealthChecker


def report_to_supervisor():
    """Report health in format compatible with supervisor monitoring."""
    checker = HealthChecker()
    health = checker.check_all()
    
    # Format for supervisor's ecosystem_status.py
    output = {
        "repository": "opa-quotes-storage",
        "status": health["overall_status"],
        "timestamp": health["timestamp"],
        "checks": health["checks"]
    }
    
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    report_to_supervisor()
