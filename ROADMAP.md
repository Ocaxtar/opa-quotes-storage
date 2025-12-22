# Roadmap opa-quotes-storage

## 🎯 Contexto del Repositorio

**Repositorio**: opa-quotes-storage  
**Función**: Storage layer TimescaleDB para cotizaciones de mercado en tiempo real  
**Módulo**: Módulo 5 (Cotización)  
**Fase actual**: Fase 1  
**Estado**: 🟡 In Development (scaffolding completado)

Este repositorio implementa el **almacenamiento persistente** del Módulo de Cotización con hypertable TimescaleDB optimizada para time-series.

## 📊 Estado Actual (2025-12-22)

**Progreso Módulo Cotización**: 5%

**opa-quotes-storage** - Storage Layer:
- [x] Scaffolding base (OPA-149) ✅
- [ ] SQLAlchemy models (OPA-182) ⏳
- [ ] Migraciones Alembic (OPA-186) ⏳
- [ ] QuoteRepository (OPA-187) ⏳
- [ ] Docker Compose (OPA-185) ⏳
- [ ] Health checks (OPA-183) ⏳
- [ ] CI/CD (OPA-184) ⏳

**Métricas actuales**:
- Tests: 0 (pending)
- Coverage: 0%
- Último commit: [508dfc9](https://github.com/Ocaxtar/opa-quotes-storage/commit/508dfc9) (OPA-149, 22/dic)
- Estado: 🟡 Scaffold completo, desarrollo pendiente

## 🗺️ Roadmap Detallado

### Fase 1: Infraestructura Base (Actual)

**OPA-185** - Configurar Docker Compose con TimescaleDB (P2)
- [x] Scaffolding docker-compose.yml básico
- [ ] docker-compose.test.yml con DB en memoria
- [ ] Health checks (pg_isready)
- [ ] PostgreSQL optimizado para time-series
- [ ] Script check_health.py
- [ ] Makefile con comandos dev-up/test-up

**OPA-182** - Implementar SQLAlchemy models (P2)
- [ ] Modelo RealTimeQuote con schema quotes.real_time
- [ ] Primary key compuesta (symbol, timestamp)
- [ ] Connection management con variables de entorno
- [ ] Tests unitarios >80% coverage

**OPA-186** - Crear migraciones Alembic (P2)
- [ ] Inicializar Alembic
- [ ] Migración 001: Crear hypertable
- [ ] Migración 002: Políticas compresión (30 días) y retención (2 años)
- [ ] Índices optimizados (timestamp DESC)
- [ ] Script init_database.sh

### Fase 1: Capa de Acceso a Datos

**OPA-187** - Implementar QuoteRepository (P2)
- [ ] Método bulk_insert con validación Pydantic
- [ ] Método get_quotes (símbolo + rango temporal)
- [ ] Método get_latest_quote
- [ ] Método get_intraday_quotes
- [ ] Tests unitarios (mock session)
- [ ] Tests integración (TimescaleDB real)
- [ ] Benchmark >10K quotes/segundo

**OPA-183** - Implementar health checks (P2)
- [ ] HealthChecker con checks: database, timescaledb, hypertable
- [ ] CLI ejecutable (python -m opa_quotes_storage)
- [ ] Exit code 0/1 según estado
- [ ] Integración con supervisor (report_health.py)
- [ ] Tests unitarios y de integración

### Fase 1: CI/CD

**OPA-184** - Configurar CI/CD con GitHub Actions (P3)
- [ ] Workflow CI: linting + tests
- [ ] Tests unitarios (sin DB)
- [ ] Tests integración (TimescaleDB service)
- [ ] Cobertura >80% obligatoria
- [ ] Pre-commit hooks
- [ ] Badges en README
- [ ] Dependabot

### Fase 2: Optimizaciones y Agregados

- [ ] Continuous aggregates (1min → 1hour → 1day)
- [ ] Compresión automática >30 días (ratio 10:1)
- [ ] Políticas de retención activas
- [ ] Materialized views para queries comunes
- [ ] Read replicas para analytics

### Fase 3: Monitorización Avanzada

- [ ] Métricas Prometheus (write throughput, query latency)
- [ ] Dashboard Grafana
- [ ] Alertas para degradación de performance
- [ ] Integración con opa-shared-monitoring

## 🔗 Dependencias

### Upstream (alimentan datos)
- **opa-quotes-streamer** (pendiente OPA-146): Feeds real-time quotes

### Downstream (consumen datos)
- **opa-capacity-compute** (operativo): Quotes históricas para Event Vectors
- **opa-prediction-features** (pendiente): Feature engineering desde series de precios
- **opa-quotes-api** (pendiente OPA-145): REST API para consultas

## 📈 Métricas de Éxito

### Fase 1 (Completitud)
- ✅ Hypertable quotes.real_time operativa
- ✅ Migraciones Alembic funcionales
- ✅ QuoteRepository con bulk_insert >10K quotes/s
- ✅ Health checks integrados con supervisor
- ✅ CI/CD con tests >80% coverage

### Fase 2 (Performance)
- ✅ Write throughput: >50K quotes/segundo
- ✅ Query latency: <20ms p95 (símbolo + rango temporal)
- ✅ Storage compression: ratio 10:1 para chunks >30 días
- ✅ Continuous aggregates operativos

### Fase 3 (Monitorización)
- ✅ Métricas Prometheus expuestas
- ✅ Dashboard Grafana operativo
- ✅ Alertas configuradas (latency >100ms, errors >1%)

## 🚧 Bloqueantes Actuales

**Para iniciar desarrollo**:
- ✅ Scaffolding completado (OPA-149)
- ⏳ TimescaleDB local operativo (docker-compose up)

**Para integración con streamer**:
- ⏳ OPA-146 (opa-quotes-streamer) creado y operativo
- ⏳ Contrato de integración definido en supervisor

**Para integración con APIs**:
- ⏳ OPA-145 (opa-quotes-api) creado
- ⏳ Contrato de consultas definido

## 🔗 Referencias

**Documentación supervisor**: `OPA_Machine/docs/services/module-5-quotes/storage.md`  
**Contratos**: `OPA_Machine/docs/contracts/data-models/quotes.md`  
**ADRs relevantes**: 
- ADR-007 (multi-workspace architecture)

**Roadmap completo**: [OPA_Machine/ROADMAP.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/ROADMAP.md)

---

**Última sincronización con supervisor**: 2025-12-22 (commit bdd0c01)
