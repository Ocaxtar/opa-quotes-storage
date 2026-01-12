# AGENTS.md - Guía para Agentes de IA (opa-quotes-storage)

## Información del Repositorio

**Nombre**: opa-quotes-storage  
**Función**: Storage layer para cotizaciones de mercado en tiempo real  
**Módulo**: Módulo 5 (Cotización)  
**Fase**: Fase 1  
**Tipo**: Storage service (TimescaleDB)  
**Repositorio GitHub**: https://github.com/Ocaxtar/opa-quotes-storage  
**Proyecto Linear**: opa-quotes-storage

## 🔧 Gestión de Tools MCP

Este repositorio utiliza **Model Context Protocol (MCP)** para integración con Linear y GitHub.

### Activación de Tools

**REGLA CRÍTICA**: Tools MCP se activan **on-demand** por categoría funcional. NO están disponibles por defecto.

#### Linear Tools

Para trabajar con issues, comentarios, proyectos o equipos:

```python
# ✅ CORRECTO: Activar categoría necesaria
<invoke name="activate_issue_management_tools">  # Para crear/editar issues
<invoke name="activate_workspace_overview_tools"> # Para listar proyectos/equipos
<invoke name="activate_issue_tracking_tools">    # Para consultar estado de issues

# ❌ INCORRECTO: Intentar usar tool sin activar categoría
<invoke name="mcp_linear_create_issue">  # Error: Tool no disponible
```

#### GitHub Tools

Para trabajar con PRs, branches, commits o archivos remotos:

```python
# ✅ CORRECTO: Activar categoría necesaria
<invoke name="activate_repository_management_tools">  # Para crear branches/PRs
<invoke name="activate_file_management_tools">        # Para leer/editar archivos remotos

# ❌ INCORRECTO: Asumir que tools están disponibles
<invoke name="mcp_github-mcp_create_or_update_file">  # Error: Tool no disponible
```

### Categorías Disponibles

**Linear**:
- `activate_issue_management_tools`: Crear/editar issues, comentarios, labels, proyectos
- `activate_document_management_tools`: Gestionar documentos de Linear
- `activate_issue_tracking_tools`: Consultar estado, adjuntos, branches asociados
- `activate_workspace_overview_tools`: Listar proyectos, equipos, usuarios, labels
- `activate_team_and_user_management_tools`: Info detallada de equipos y usuarios

**GitHub**:
- `activate_repository_management_tools`: Crear repos, branches, PRs, merge
- `activate_pull_request_review_tools`: Gestionar reviews de PRs
- `activate_file_management_tools`: Leer/editar/eliminar archivos remotos
- `activate_repository_information_tools`: Info de commits, releases, issues
- `activate_branch_and_commit_tools`: Listar branches, historial de commits

### Workflow Típico

```python
# 1. Usuario pide: "Resuelve OPA-234"

# 2. Activar Linear tools para leer issue
<invoke name="activate_issue_tracking_tools">

# 3. Leer issue (ahora disponible)
<invoke name="mcp_linear_get_issue">
  <parameter name="id">OPA-234</parameter>
</invoke>

# 4. Trabajar en la issue
# ... implementación ...

# 5. Actualizar estado en Linear
<invoke name="mcp_linear_update_issue">
  <parameter name="id">OPA-234</parameter>
  <parameter name="state">Done</parameter>
</invoke>
```

### Recuperación de Errores

Si un tool falla por no estar activado:

```python
# Error: "Tool mcp_linear_create_issue not available"

# Solución:
<invoke name="activate_issue_management_tools"></invoke>
# Ahora reintentar
<invoke name="mcp_linear_create_issue">...</invoke>
```

## 🛡️ Validación de Convenciones

Antes de ejecutar cualquier acción que pueda violar convenciones del repositorio, **DETENTE** y verifica:

### Checkpoint Obligatorio Pre-Acción

Antes de:
- Crear/editar archivos
- Ejecutar comandos
- Hacer commits
- Mergear branches

**VERIFICA**:

1. **Naming conventions** (archivo AGENTS.md actual)
   - ¿El nombre de archivo sigue las reglas?
   - ¿La estructura de carpetas es correcta?

2. **Workflow de issues** (sección "Para Issues")
   - ¿La branch tiene el formato correcto?
   - ¿El commit message sigue la convención?
   - ¿Es necesario mergear a main antes de cerrar?

3. **Testing requirements**
   - ¿Los tests pasan antes del commit?
   - ¿El coverage es >80%?

4. **Contratos de integración**
   - ¿Los cambios afectan interfaces compartidas?
   - ¿Se actualizó el contrato en supervisor?

### Ejemplo de Validación

```python
# Usuario: "Crea un archivo para validaciones"

# ❌ INCORRECTO: Crear directamente sin validar
<invoke name="create_file">
  <parameter name="filePath">validator.py</parameter>  # ¿Dónde va este archivo?
</invoke>

# ✅ CORRECTO: Validar estructura primero
# 1. Leer AGENTS.md sección "Estructura de Archivos"
<invoke name="read_file">
  <parameter name="filePath">AGENTS.md</parameter>
  <parameter name="startLine">100</parameter>
  <parameter name="endLine">120</parameter>
</invoke>

# 2. Confirmar ubicación correcta: src/opa_quotes_storage/validators.py
<invoke name="create_file">
  <parameter name="filePath">src/opa_quotes_storage/validators.py</parameter>
  ...
</invoke>
```

### Recovery Workflow

Si detectas que violaste una convención:

1. **PAUSAR** inmediatamente
2. **REVERTIR** cambios incorrectos
3. **RE-VALIDAR** contra AGENTS.md
4. **REINTENTAR** con enfoque correcto

```python
# Detectaste: archivo creado en ubicación incorrecta

# 1. Eliminar archivo incorrecto
<invoke name="run_in_terminal">
  <parameter name="command">rm validators.py</parameter>
</invoke>

# 2. Crear en ubicación correcta
<invoke name="create_file">
  <parameter name="filePath">src/opa_quotes_storage/validators.py</parameter>
  ...
</invoke>
```

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
4. Trabajar en rama: `oscarcalvovaquero/OPA-XXX-descripcion-corta`
5. Ejecutar tests antes de commit
6. Commit con mensaje: `OPA-XXX: Descripción clara`
7. Push a GitHub
8. **OBLIGATORIO: Mergear a main al completar la issue (antes de mover a Done)**
   ```bash
   # 1. Asegurar que todos los cambios están commiteados
   git status  # Debe estar limpio
   
   # 2. Actualizar main local
   git checkout main
   git pull origin main
   
   # 3. Mergear branch a main (squash para historia limpia)
   git merge --squash oscarcalvovaquero/OPA-XXX-descripcion-corta
   
   # 4. Commit final con mensaje de issue
   git commit -m "OPA-XXX: Descripción completa de la feature/fix"
   
   # 5. Pushear a GitHub
   git push origin main
   
   # 6. Eliminar branch local y remota
   git branch -d oscarcalvovaquero/OPA-XXX-descripcion-corta
   git push origin --delete oscarcalvovaquero/OPA-XXX-descripcion-corta 2>/dev/null || true
   ```
9. **Añadir comentario de cierre** con prefijo `🤖 Agente opa-quotes-storage:`
10. **Solo ENTONCES**: Mover a "Done" en Linear

**⚠️ REGLA CRÍTICA**: NO cerrar issue si la branch no está mergeada. Ramas sin mergear = trabajo perdido.

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
