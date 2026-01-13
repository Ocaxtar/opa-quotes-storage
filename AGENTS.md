# AGENTS.md - Guía para Agentes de IA (opa-quotes-storage)

## Información del Repositorio

**Nombre**: opa-quotes-storage  
**Función**: Storage layer para cotizaciones de mercado en tiempo real  
**Módulo**: Módulo 5 (Cotización)  
**Fase**: Fase 1  
**Tipo**: Storage service (TimescaleDB)  
**Repositorio GitHub**: https://github.com/Ocaxtar/opa-quotes-storage  
**Proyecto Linear**: opa-quotes-storage  
**Label Linear**: `opa-quotes-storage`

## 📚 Guías Especializadas (CONSULTAR PRIMERO)

Antes de implementar cualquier cambio, consultar estas guías del repositorio supervisor:

| Guía | Propósito | Cuándo consultar |
|------|-----------|------------------|
| **[workflow-git-linear.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/guides/workflow-git-linear.md)** | Workflow Git+Linear completo | Al trabajar en issues (branch, commit, merge, cierre) |
| **[multi-workspace-guide.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/guides/multi-workspace-guide.md)** | Arquitectura 20 repos, coordinación | Al crear repos, issues cross-repo, labels Linear |
| **[code-conventions.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/guides/code-conventions.md)** | Estándares código, testing, CI/CD | Al escribir código, configurar tests, Docker |
| **[technology-stack.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/guides/technology-stack.md)** | Stack tecnológico consolidado | Al elegir librerías, evaluar rendimiento |
| **[linear-mcp-quickstart.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/guides/linear-mcp-quickstart.md)** | Errores comunes Linear MCP | Al usar mcp_linear tools (errores, fixes) |

## 🔧 Gestión de Tools MCP (Linear, GitHub)

**REGLA CRÍTICA**: Muchas tools de Linear/GitHub requieren activación explícita antes de uso.

### Workflow de Activación

Si intentas usar una tool y fallas con:
```
Tool mcp_linear_create_issue is currently disabled by the user, and cannot be called.
ERROR: Tool not found or not activated
```

**NO continúes sin la tool**. Debes:
1. ✅ Activar el grupo de tools correspondiente
2. ✅ Reintentar la operación original
3. ❌ NUNCA saltar el paso o usar alternativa

**Ejemplo**:
```markdown
# Detectar fallo
Tool mcp_linear_create_comment failed: currently disabled

# 1. Activar grupo
activate_issue_management_tools()

# 2. Reintentar operación EXACTA
mcp_linear_create_comment(issueId="OPA-XXX", body="...")
```

### Tools que Requieren Activación

| Grupo | Tool de Activación | Cuándo Usar |
|-------|-------------------|-------------|
| Linear Issues | `activate_issue_management_tools()` | Crear/actualizar issues, labels |
| Linear Docs | `activate_document_management_tools()` | Crear/actualizar documentos |
| Linear Tracking | `activate_issue_tracking_tools()` | Consultar estado, attachments, branches |
| GitHub PRs | `activate_pull_request_review_tools()` | Crear/revisar PRs |
| GitHub Repos | `activate_repository_management_tools()` | Crear repos, branches |
| GitHub Files | `activate_file_management_tools()` | Leer/editar/eliminar archivos remotos |

**Ver**: `OPA_Machine/AGENTS.md` sección "Gestión de Tools MCP" para tabla completa.

## 🛡️ Validación de Convenciones

**REGLA CRÍTICA**: Antes de ejecutar acciones que modifican estado, validar convenciones.

### Convenciones Obligatorias para opa-quotes-storage

1. **Commits**: DEBEN incluir referencia a issue (`OPA-XXX`)
2. **Issues**: DEBEN crearse en Linear ANTES de implementar
3. **Branches**: DEBEN seguir patrón `oscarcalvovaquero/OPA-XXX-descripcion`
4. **Tests**: DEBEN ejecutarse antes de marcar Done (coverage >80%)
5. **Merges**: OBLIGATORIO mergear a main antes de cerrar issue

### 📝 Comentarios vs Descripción en Issues

**PRINCIPIO**: La **descripción** de una issue es la **especificación inicial**. Los **comentarios** son el **registro de progreso**.

| Acción | Tool Correcta | Tool Incorrecta |
|--------|---------------|-----------------|
| Reportar avance parcial | `mcp_linear_create_comment()` | ❌ `mcp_linear_update_issue(body=...)` |
| Reactivar issue cerrada | `mcp_linear_create_comment()` + `update_issue(state="In Progress")` | ❌ Solo modificar descripción |
| Documentar error encontrado | `mcp_linear_create_comment()` | ❌ Editar descripción |
| Añadir diagnóstico | `mcp_linear_create_comment()` | ❌ Modificar descripción |
| Cerrar con resumen | `mcp_linear_create_comment()` + `update_issue(state="Done")` | ❌ Solo cambiar estado |

**¿Por qué?**:
- **Trazabilidad**: Comentarios tienen timestamps automáticos → historial auditable
- **Notificaciones**: Comentarios notifican a watchers → mejor colaboración
- **Reversibilidad**: Descripción original preservada → contexto no se pierde

**¿Cuándo SÍ modificar descripción?**:
- ✅ Corregir typos en la especificación original
- ✅ Añadir criterios de aceptación faltantes (antes de empezar trabajo)
- ❌ NUNCA para reportar progreso, errores o reactivaciones

### Checkpoint Pre-Acción

Si detectas violación, **DETENER** y devolver control al usuario:

```markdown
⚠️ **Acción Bloqueada - Violación de Convención**

**Acción planeada**: `git commit -m "Fix bug"`
**Violación**: Commit sin referencia a issue (OPA-XXX)

**Opciones**:
1. Crear issue en Linear primero → Usar OPA-XXX en commit
2. Si issue existe → Añadir referencia al mensaje

¿Cómo deseas proceder?
```

**El agente debe esperar respuesta del usuario antes de continuar.**

## Contexto del Módulo

Este repositorio es el **storage layer** del Módulo 5 (Cotización), que maneja almacenamiento persistente de cotizaciones de mercado en tiempo real usando TimescaleDB. Es la base de datos compartida para:

1. **opa-quotes-streamer** (upstream): Alimenta quotes en tiempo real
2. **opa-capacity-compute** (downstream): Consume quotes históricas para Event Vectors
3. **opa-prediction-features** (downstream): Feature engineering desde series de precios
4. **opa-quotes-api** (downstream): Servicio REST para consultas de quotes

**Ver**: `docs/ECOSYSTEM_CONTEXT.md` para diagrama completo de posición en el ecosistema.

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
├── docs/
│   └── ECOSYSTEM_CONTEXT.md   # Posición en ecosistema
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
**Última sincronización con supervisor**: 2026-01-13
