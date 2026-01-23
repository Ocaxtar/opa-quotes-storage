# opa-quotes-storage

![CI Status](https://github.com/Ocaxtar/opa-quotes-storage/workflows/CI/badge.svg)
[![codecov](https://codecov.io/gh/Ocaxtar/opa-quotes-storage/branch/main/graph/badge.svg)](https://codecov.io/gh/Ocaxtar/opa-quotes-storage)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**TimescaleDB storage layer for real-time market quotes**

Part of [OPA_Machine](https://github.com/Ocaxtar/opa-supervisor) ecosystem - Módulo 5 (Cotización)

## 🎯 Purpose

Persistent storage service for high-frequency market quotes using TimescaleDB (PostgreSQL extension for time-series data). Handles:

- Real-time quote ingestion from `opa-quotes-streamer`
- Hypertable storage optimized for time-series queries
- Historical quote retrieval for `opa-capacity-compute` and `opa-prediction-features`
- Retention policies (compress data >30 days, drop >2 years)

## 🏗️ Architecture

**Repository**: `opa-quotes-storage`  
**Type**: Storage service  
**Phase**: Fase 1  
**Stack**: Python 3.12, SQLAlchemy 2.0+, TimescaleDB 2.12+, Alembic

### Database Schema

**Hypertable**: `quotes.real_time` (partitioned by time)
- `ticker` (VARCHAR) - Ticker symbol
- `timestamp` (TIMESTAMPTZ) - Quote timestamp (partition key)
- `open`, `high`, `low`, `close` (NUMERIC) - OHLC data
- `volume` (BIGINT) - Trading volume
- `bid`, `ask` (NUMERIC) - Bid/Ask prices
- `source` (TEXT) - Data provider (yfinance, Tiingo, etc.)

**Hypertable**: `quotes.ohlcv_daily` (partitioned by date)
- `ticker` (VARCHAR) - Ticker symbol
- `date` (DATE) - Quote date (partition key)
- `open`, `high`, `low`, `close` (FLOAT) - OHLC data
- `adj_close` (FLOAT) - Adjusted close (splits/dividends)
- `volume` (BIGINT) - Trading volume

**Indexes**:
- Primary: `(ticker, timestamp DESC)` for real_time
- Primary: `(ticker, date)` for ohlcv_daily
- Secondary: `(timestamp DESC)` for time-range queries

**Retention**:
- Compress chunks >30 days (save 90% storage)
- Drop chunks >2 years

## 🚀 Setup

### Prerequisites
- Docker 20+ with Compose
- Python 3.12 (fijado a <3.13 por psycopg2-binary)
- Poetry 1.7+

### Quick Start

```bash
# 1. Install dependencies
poetry install

# 2. Start TimescaleDB (development)
make dev-up

# Alternative: Manual start
docker-compose up -d
poetry run python scripts/setup/check_health.py
poetry run alembic upgrade head

# 3. Verify setup
poetry run python -m opa_quotes_storage.health
```

### Testing Environment

```bash
# Start test database (in-memory, port 5433)
make test-up

# Run integration tests
make test

# Stop test database
make test-down
```

### Available Make Commands

- `make dev-up`: Start development environment (TimescaleDB + migrations)
- `make dev-down`: Stop development environment
- `make test-up`: Start test environment
- `make test-down`: Stop test environment
- `make test`: Run full integration test suite
- `make clean`: Remove all containers and volumes

## 📊 Usage

### Ingesting Quotes (from streamer)

```python
from opa_quotes_storage import QuoteRepository

repo = QuoteRepository(conn_string="postgresql://...")

# Batch insert from streamer
quotes = [
    {"symbol": "AAPL", "timestamp": "2025-12-22T10:00:00Z", "close": 180.50, ...},
    {"symbol": "MSFT", "timestamp": "2025-12-22T10:00:00Z", "close": 420.25, ...},
]
repo.bulk_insert(quotes)
```

### Querying Historical Data

```python
# Get last 30 days of AAPL quotes
quotes = repo.get_quotes(
    symbol="AAPL",
    start_date="2025-11-22",
    end_date="2025-12-22"
)

# Get minute-by-minute data for intraday analysis
quotes = repo.get_intraday_quotes(
    symbol="TSLA",
    date="2025-12-22",
    interval="1m"
)
```

## 🧪 Testing

```bash
# Unit tests (no database)
poetry run pytest tests/unit -v

# Integration tests (requires TimescaleDB)
make test

# Alternative: Manual testing
docker-compose -f docker-compose.test.yml up -d
poetry run pytest tests/integration -v
docker-compose -f docker-compose.test.yml down -v

# Run health check script
poetry run python scripts/setup/check_health.py
```

## 📈 Performance

**Expected metrics** (Fase 1 - Python implementation):
- Write throughput: ~10K quotes/second (batch inserts)
- Query latency: <50ms (symbol + time range)
- Storage: ~500GB for 1000 tickers × 2 years × 1-minute data
- Compression ratio: 10:1 after 30 days

**Optimizations** (Fase 2+):
- Continuous aggregates for OHLC resampling
- Materialized views for common queries
- Read replicas for analytics workloads

## 🔗 Integration

### Upstream Dependencies
- `opa-quotes-streamer`: Feeds real-time quotes

### Downstream Consumers
- `opa-capacity-compute`: Historical quotes for Event Vector construction
- `opa-prediction-features`: Feature engineering from price series
- `opa-quotes-api`: Real-time quote serving

## 📝 Development

### Database Migrations

```bash
# Create new migration
poetry run alembic revision -m "Add quotes_daily aggregate"

# Apply migrations
poetry run alembic upgrade head

# Rollback
poetry run alembic downgrade -1
```

### Historical Data Backfill

Load historical OHLCV data (2017-2024) for S&P 500 companies:

```bash
# Install yfinance dependency
poetry install

# Run migrations to create ohlcv_daily table
poetry run alembic upgrade head

# Start database
make dev-up

# Run backfill (uses S&P 500 by default)
poetry run python scripts/backfill/backfill_ohlcv_daily.py

# Custom date range
poetry run python scripts/backfill/backfill_ohlcv_daily.py --start-date 2020-01-01 --end-date 2024-12-31

# Custom ticker list (one per line in file)
poetry run python scripts/backfill/backfill_ohlcv_daily.py --tickers-file my_tickers.txt

# Resume from checkpoint after interruption
poetry run python scripts/backfill/backfill_ohlcv_daily.py  # Automatically resumes

# Start fresh (ignore checkpoint)
poetry run python scripts/backfill/backfill_ohlcv_daily.py --no-resume
```

**Features**:
- ✅ Rate limiting (0.5s between requests)
- ✅ Checkpoint recovery (resume after interruption)
- ✅ Data quality validation (gaps, coverage)
- ✅ Logs saved to `logs/backfill_ohlcv.log`

**Expected time**: ~4-5 hours for 500 tickers × 7 years (with rate limiting)

### Adding New Fields

1. Update `src/opa_quotes_storage/models.py`
2. Create Alembic migration
3. Update repository methods
4. Add tests
5. Update contracts in supervisor (`OPA_Machine/docs/contracts/data-models/quotes.md`)

## 📋 Roadmap

**Fase 1** (Current):
- [x] Basic scaffolding (OPA-149)
- [x] Docker Compose con TimescaleDB (OPA-185)
- [ ] SQLAlchemy models + Alembic migrations (OPA-182, OPA-186)
- [ ] QuoteRepository with bulk insert (OPA-187)
- [ ] Health checks and monitoring (OPA-183)
- [ ] CI/CD (OPA-184)

**Fase 2**:
- [ ] Continuous aggregates (1min → 1hour → 1day)
- [ ] Compression policies
- [ ] Read replicas for analytics
- [ ] Query performance benchmarks

## 🛠️ Troubleshooting

**Issue**: `psycopg2.OperationalError: could not connect to server`
- **Fix**: Verify TimescaleDB is running: `docker-compose ps`

**Issue**: `alembic.util.exc.CommandError: Can't locate revision`
- **Fix**: Initialize Alembic: `poetry run alembic init alembic`

**Issue**: Slow queries on large time ranges
- **Fix**: Add index on `(timestamp DESC)` or use continuous aggregates

## 📚 References

**Supervisor documentation**: `OPA_Machine/docs/services/module-5-quotes/storage.md`  
**Contracts**: `OPA_Machine/docs/contracts/data-models/quotes.md`  
**ADRs**: 
- ADR-007 (multi-workspace architecture)
- TimescaleDB vs InfluxDB (pending ADR)

## 🤝 Contributing

See `OPA_Machine/AGENTS.md` for agente workflow and conventions.

---

**Last updated**: 2025-12-22  
**Status**: 🟡 In Development  
**Phase**: Fase 1  
**Tests**: Pending  
**Coverage**: 0%
