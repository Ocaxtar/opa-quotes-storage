# AGENTS.md - Guía para Agentes de IA (opa-quotes-storage)

## Información del Repositorio

**Nombre**: opa-quotes-storage  
**Función**: Storage layer para cotizaciones de mercado en tiempo real  
**Módulo**: Módulo 5 (Cotización)  
**Fase**: Fase 1  
**Tipo**: Storage service (TimescaleDB)  
**Repositorio GitHub**: https://github.com/Ocaxtar/opa-quotes-storage  
**Proyecto Linear**: opa-quotes-storage

## Contexto del Módulo

Este repositorio es el **storage layer** del Módulo 5 (Cotización), que maneja almacenamiento persistente de cotizaciones de mercado en tiempo real usando TimescaleDB. Es la base de datos compartida para:

1. **opa-quotes-streamer** (upstream): Alimenta quotes en tiempo real
2. **opa-capacity-compute** (downstream): Consume quotes históricas para Event Vectors
3. **opa-prediction-features** (downstream): Feature engineering desde series de precios
4. **opa-quotes-api** (downstream): Servicio REST para consultas de quotes

## Responsabilidades

### Almacenamiento y Consulta
- Hypertable de TimescaleDB optimizada para time-series (`quotes.real_time`)
- Bulk insert de quotes desde streamer (>10K quotes/segundo)
- Consultas rápidas por símbolo + rango temporal (<50ms p95)
- Retención automatizada (compress >30 días, drop >2 años)

### Migraciones y Esquema
- Alembic para gestión de migraciones
- Definición de modelos SQLAlchemy
- Continuous aggregates (Fase 2: resampling OHLC)
- Índices optimizados para patrones de consulta

### Integración
- Interfaz QuoteRepository para abstraer acceso a datos
- Contratos de integración definidos en supervisor (`OPA_Machine/docs/contracts/data-models/quotes.md`)
- Health checks para monitorización de estado

## Stack Tecnológico

| Componente | Versión | Propósito |
|------------|---------|-----------|
| Python | 3.12.x | Lenguaje principal (fijado a <3.13 por psycopg2-binary) |
| SQLAlchemy | 2.0+ | ORM y database toolkit |
| Alembic | 1.12+ | Database migrations |
| psycopg2-binary | 2.9+ | PostgreSQL adapter |
| TimescaleDB | 2.12+ | Time-series extension para PostgreSQL |
| PostgreSQL | 14+ | Base de datos relacional |
| Docker Compose | 2.23+ | Orquestación local |
| pytest | 7+ | Testing framework |

## Arquitectura de Datos

### Hypertable Principal

```sql
-- quotes.real_time (partitioned by timestamp)
CREATE TABLE quotes.real_time (
    symbol TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open NUMERIC(10,2),
    high NUMERIC(10,2),
    low NUMERIC(10,2),
    close NUMERIC(10,2),
    volume BIGINT,
    bid NUMERIC(10,2),
    ask NUMERIC(10,2),
    source TEXT,
    PRIMARY KEY (symbol, timestamp)
);

SELECT create_hypertable('quotes.real_time', 'timestamp');
CREATE INDEX idx_timestamp_desc ON quotes.real_time (timestamp DESC);
```

### Políticas de Retención

```sql
-- Comprimir chunks >30 días (ahorra 90% storage)
ALTER TABLE quotes.real_time SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol',
    timescaledb.compress_orderby = 'timestamp DESC'
);

SELECT add_compression_policy('quotes.real_time', INTERVAL '30 days');

-- Eliminar chunks >2 años
SELECT add_retention_policy('quotes.real_time', INTERVAL '2 years');
```

## Flujo de Trabajo

### Para Desarrollo

```bash
# 1. Instalar dependencias
poetry install

# 2. Iniciar TimescaleDB local
docker-compose up -d

# 3. Verificar conexión
poetry run python -c "from opa_quotes_storage import get_db_connection; get_db_connection().execute('SELECT version()')"

# 4. Ejecutar migraciones
poetry run alembic upgrade head

# 5. Ejecutar tests
poetry run pytest tests/unit -v           # Sin DB
poetry run pytest tests/integration -v    # Con DB
```

### Para Issues

1. **Leer TODOS los comentarios** de la issue antes de comenzar
2. Verificar dependencias con otros repositorios (contratos en supervisor)
3. Mover issue a "In Progress" en Linear
4. Trabajar en rama: `oscarcalvo/OPA-XXX-descripcion-corta`
5. Ejecutar tests antes de commit
6. Commit con mensaje: `OPA-XXX: Descripción clara`
7. Push a GitHub
8. **Añadir comentario de cierre** con prefijo `🤖 Agente opa-quotes-storage:`
9. Mover a "Done" solo DESPUÉS de verificar archivos en GitHub

## Convenciones de Código

### Estructura de Archivos

```
opa-quotes-storage/
├── src/opa_quotes_storage/
│   ├── __init__.py
│   ├── models.py              # SQLAlchemy models
│   ├── repository.py          # QuoteRepository class
│   ├── connection.py          # Database connection management
│   └── health.py              # Health check endpoint
├── database/
│   └── migrations/
│       └── versions/          # Alembic migrations
├── tests/
│   ├── unit/                  # Tests sin DB
│   └── integration/           # Tests con TimescaleDB
├── docker-compose.yml         # TimescaleDB local
├── pyproject.toml             # Dependencies
└── README.md                  # Documentación
```

### Naming Conventions

```python
# Modelos SQLAlchemy (singular, PascalCase)
class RealTimeQuote(Base):
    __tablename__ = "real_time"
    __table_args__ = {"schema": "quotes"}

# Repository methods (verbo + sustantivo)
class QuoteRepository:
    def bulk_insert(self, quotes: List[Dict]) -> int:
        """Insert batch of quotes."""
        pass
    
    def get_quotes(self, symbol: str, start_date: str, end_date: str) -> List[RealTimeQuote]:
        """Retrieve quotes for symbol in date range."""
        pass
```

### Testing

```python
# tests/unit/test_repository.py (mock DB)
def test_bulk_insert_validates_schema():
    repo = QuoteRepository(connection=Mock())
    
    with pytest.raises(ValidationError):
        repo.bulk_insert([{"symbol": "AAPL"}])  # Missing required fields

# tests/integration/test_timescaledb.py (real DB)
def test_hypertable_partitioning(db_connection):
    repo = QuoteRepository(connection=db_connection)
    repo.bulk_insert([
        {"symbol": "AAPL", "timestamp": "2025-12-22T10:00:00Z", "close": 180.50, ...}
    ])
    
    # Verify chunk creation
    chunks = db_connection.execute("SELECT * FROM timescaledb_information.chunks").fetchall()
    assert len(chunks) > 0
```

## Contratos de Integración

### Input: Desde opa-quotes-streamer

**Formato**: JSON batch con quotes
```json
[
  {
    "symbol": "AAPL",
    "timestamp": "2025-12-22T10:00:00Z",
    "open": 180.25,
    "high": 181.00,
    "low": 179.50,
    "close": 180.50,
    "volume": 1234567,
    "bid": 180.48,
    "ask": 180.52,
    "source": "yfinance"
  }
]
```

**Validación**:
- `symbol`: TEXT, obligatorio
- `timestamp`: TIMESTAMPTZ ISO 8601, obligatorio
- OHLC: NUMERIC, opcional
- `volume`: BIGINT, opcional
- `bid`, `ask`: NUMERIC, opcional

### Output: Hacia opa-capacity-compute

**Método**: `get_quotes(symbol, start_date, end_date)`

**Retorno**: Lista de quotes ordenadas por timestamp ASC
```python
[
    RealTimeQuote(symbol="AAPL", timestamp=datetime(...), close=180.50, ...),
    ...
]
```

**Performance**: <50ms para queries de 30 días

## Métricas de Éxito

### Fase 1 (Actual)
- ✅ Hypertable `quotes.real_time` creada
- ✅ Migraciones Alembic funcionales
- ✅ QuoteRepository con bulk_insert
- ✅ Health check operativo
- ⏳ Tests integration con TimescaleDB (coverage >80%)

### Fase 2
- Continuous aggregates (1min → 1hour → 1day)
- Compression policies activas (>90% ahorro storage)
- Read replicas para analytics
- Query performance <20ms p95

## Referencias Críticas

**Documentación supervisor**:
- Arquitectura: `OPA_Machine/docs/architecture/ecosystem-overview.md`
- Contrato quotes: `OPA_Machine/docs/contracts/data-models/quotes.md`
- ADR-007: Arquitectura multi-workspace

**Repositorios relacionados**:
- Upstream: [opa-quotes-streamer](https://github.com/Ocaxtar/opa-quotes-streamer)
- Downstream: [opa-capacity-compute](https://github.com/Ocaxtar/opa-capacity-compute)
- Downstream: [opa-quotes-api](https://github.com/Ocaxtar/opa-quotes-api)

**Linear**: https://linear.app/opa-machine/team/OPA/project/opa-quotes-storage

## Troubleshooting

### Error: `psycopg2.OperationalError: could not connect to server`

**Diagnóstico**:
```bash
docker-compose ps
docker-compose logs timescaledb
```

**Fix**: Verificar que TimescaleDB está ejecutándose en puerto 5432

### Error: `alembic.util.exc.CommandError: Can't locate revision`

**Diagnóstico**: Alembic no está inicializado

**Fix**:
```bash
poetry run alembic init alembic
poetry run alembic revision -m "Initial schema"
```

### Performance: Queries lentas en rangos temporales grandes

**Diagnóstico**: Índices faltantes o chunks no comprimidos

**Fix**:
```sql
-- Verificar uso de índices
EXPLAIN ANALYZE SELECT * FROM quotes.real_time 
WHERE symbol = 'AAPL' AND timestamp > now() - INTERVAL '30 days';

-- Forzar compresión manual
SELECT compress_chunk(i) FROM show_chunks('quotes.real_time') i;
```

## Comandos Útiles

### Desarrollo
```bash
# Activar entorno
poetry shell

# Ejecutar tests
poetry run pytest -v

# Formatear y linting
poetry run ruff format .
poetry run ruff check .

# Migraciones
poetry run alembic revision -m "Add field"
poetry run alembic upgrade head
```

### Database
```bash
# Conectar a TimescaleDB
docker-compose exec timescaledb psql -U opa_user -d opa_quotes

# Ver chunks
SELECT * FROM timescaledb_information.chunks;

# Forzar compresión
SELECT compress_chunk(i, if_not_compressed => true) FROM show_chunks('quotes.real_time') i;

# Ver espacio usado
SELECT * FROM timescaledb_information.hypertable;
```

---

📝 **Este documento debe actualizarse conforme evolucione el repositorio**  
**Última sincronización con supervisor**: 2025-12-22
