#!/usr/bin/env python3
"""CLI for opa-quotes-storage health checks."""

import json
import sys

from .health import HealthChecker


def main():
    """Run health checks and print results."""
    checker = HealthChecker()
    health = checker.check_all()
    
    # Pretty print JSON
    print(json.dumps(health, indent=2))
    
    # Exit code based on overall status
    if health["overall_status"] == "healthy":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
