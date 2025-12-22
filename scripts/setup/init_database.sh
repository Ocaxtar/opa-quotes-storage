#!/bin/bash
# Initialize TimescaleDB and run migrations

set -e  # Exit on error

echo "🚀 Starting TimescaleDB..."
docker-compose up -d

echo "⏳ Waiting for TimescaleDB to be ready..."
sleep 5

# Run health check
echo "🔍 Checking database connection..."
poetry run python scripts/setup/check_health.py

# Run migrations
echo "📦 Running Alembic migrations..."
poetry run alembic upgrade head

echo "✅ Database initialized with hypertable and retention policies"
