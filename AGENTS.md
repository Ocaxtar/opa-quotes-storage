# AGENTS.md - opa-quotes-storage

> 🎯 **Guía específica para agentes IA** en este repo operativo.  
> **Supervisión**: [OPA_Machine/AGENTS.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/AGENTS.md)

---

## 🚦 Pre-Flight Checklist (OBLIGATORIO)

| Acción | Documento/Skill | Cuándo |
|--------|-----------------|--------|
| Consultar infraestructura | [opa-infrastructure-state](https://github.com/Ocaxtar/opa-infrastructure-state/blob/main/state.yaml) | ANTES de Docker/DB/Redis |
| **Consultar schema DB** | **[state.yaml → schemas](https://github.com/Ocaxtar/opa-infrastructure-state/blob/main/state.yaml)** + **Skill `infrastructure-lookup`** | ⚠️ **ANTES** de crear/modificar modelos SQLAlchemy, Pydantic, migraciones SQL |
| Sincronizar workspace | Skill `workspace-sync` (supervisor) | Inicio sesión |
| Verificar estado repos | [DASHBOARD.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/DASHBOARD.md) | Inicio sesión |
| Trabajar en issue | Skill `git-linear-workflow` | Antes branch/commit |
| Usar Linear MCP | Skill `linear-mcp-tool` | Si tool falla/UUID |
| Operaciones Docker seguras | Skill `docker-safe-operations` | Antes docker-compose down -v, gestión volúmenes |

### ⏭️ Cuándo NO Consultar Schemas

**Evitar overhead** en estos casos:

| Situación | Acción |
|-----------|---------|
| 🔍 Leer código existente | NO consultar (solo lectura) |
| 🧪 Ejecutar tests | NO consultar (ya validados) |
| 📝 Actualizar documentación | NO consultar (no toca DB) |
| 🔧 Refactors sin cambios de DB | NO consultar (lógica interna) |
| 🚀 Deploy sin cambios de schema | NO consultar (infraestructura) |

**OBLIGATORIO consultar** cuando:
- ✅ Crear nueva tabla (migration + model)
- ✅ Añadir/modificar columnas (ALTER TABLE)
- ✅ Crear modelos SQLAlchemy/Pydantic de tablas existentes
- ✅ Validar tipos de datos antes de query

> **Guía completa**: Skill `infrastructure-lookup` v2.0 en supervisor (Caso 2: Operaciones con Schemas).

---

## 📋 Info del Repositorio

**Nombre**: opa-quotes-storage  
**Tipo**: Storage (TimescaleDB)  
**Propósito**: Almacenamiento de cotizaciones en tiempo real con compresión automática  
**Puerto**: 5433 (PostgreSQL)  
**Team Linear**: OPA  
**Tecnologías**: TimescaleDB, PostgreSQL 14, Hypertables, Continuous Aggregates

**Funcionalidad**:
- Hypertable `quotes.real_time` con particionamiento por tiempo
- VIEW alias `quotes.quotes` para compatibilidad con componentes externos
- Hypertable `quotes.ohlcv_daily` para históricos OHLCV (2017+)
- Compresión automática datos >30 días
- Continuous aggregates para estadísticas (OHLCV)
- Retención: raw data 30 días, agregados 1 año

**Dependencias**:
- Ninguna (es el storage de quotes)

---

## ⚠️ Reglas Críticas Específicas

### 1. Puerto PostgreSQL = 5433 (NO 5432)

```
❌ Puerto 5432 en docker-compose.yml
✅ Puerto 5433 (Windows local ocupa 5432)
```

**Motivo**: Ver [service-inventory.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/infrastructure/service-inventory.md).

### 2. Migrations obligatorias para TODA modificación de schema

```
❌ ALTER TABLE directo en psql
✅ Crear migration en database/migrations/
```

**Workflow**:
1. Crear `XXX_descripcion.sql` en `database/migrations/`
2. Ejecutar en dev: `psql -U postgres -d opa_quotes -f migrations/XXX_descripcion.sql`
3. Actualizar schema en supervisor (ver workflow más abajo)

### 3. Hypertables con chunk_time_interval = 1 día

```sql
-- ✅ Correcto (real_time es la hypertable real)
SELECT create_hypertable(
    'quotes.real_time',
    'timestamp',
    chunk_time_interval => INTERVAL '1 day'
);
```

**Motivo**: Balance entre compresión y query performance.

---

## 🔄 Workflows Especiales

### Actualizar Schemas DB (OPA-343)

**Al crear/modificar tablas en TimescaleDB**:

1. Implementar migration en `database/migrations/`
2. Ejecutar migration en dev
3. Desde supervisor: 
   ```bash
   cd ../opa-supervisor
   python scripts/infrastructure/extract-db-schema.py schema.table \
       --created-by opa-quotes-storage \
       --created-issue OPA-XXX
   ```
4. Actualizar `docs/infrastructure/state-db-schemas.yaml.md` en supervisor
5. Commit en supervisor: `OPA-XXX: Document schema.table`

**Por qué**: [state-db-schemas.yaml.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/infrastructure/state-db-schemas.yaml.md) es el **source of truth** de schemas reales.

**Tablas a documentar**:
- `quotes.real_time` (hypertable principal - tiempo real)
- `quotes.quotes` (VIEW alias de real_time - compatibilidad)
- `quotes.ohlcv_daily` (hypertable históricos - OHLCV 2017+)

---

## 🔧 Operaciones de Infraestructura

> **OBLIGATORIO**: Ejecutar ANTES de cualquier operación Docker/DB/Redis.

### Workflow de 3 Pasos

#### Paso 1: Ejecutar Preflight Check

```bash
# Desde este repo
python ../opa-supervisor/scripts/infrastructure/preflight_check.py --module quotes --operation docker-compose
```

#### Paso 2: Evaluar Resultado

| Resultado | Acción |
|-----------|--------|
| ✅ PREFLIGHT PASSED | Continuar con la tarea |
| ❌ PREFLIGHT FAILED | **NO continuar**. Reportar al usuario qué servicios faltan |

#### Paso 3: Configurar usando state.yaml

**Source of Truth**: `opa-infrastructure-state/state.yaml`

```python
# ✅ CORRECTO: Variables de entorno con fallback
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://opa_user:opa_password@localhost:5433/opa_quotes")

# ❌ INCORRECTO: Hardcodear valores
DATABASE_URL = "postgresql://opa_user:opa_password@localhost:5433/opa_quotes"
```

### Anti-Patrones (PROHIBIDO)

| Anti-Patrón | Por qué está mal |
|-------------|------------------|
| ❌ Consultar `service-inventory.md` como fuente | Es documento AUTO-GENERADO, no editable |
| ❌ Hardcodear puertos/credenciales | Dificulta mantenimiento y causa bugs |
| ❌ Asumir que servicio existe sin validar | Causa "Connection refused" en deploy |
| ❌ Usar puerto 5432 para Docker | PostgreSQL local Windows lo ocupa |
| ❌ Continuar si preflight falla | Propaga configuración inválida |

### Quick Reference: Puertos

| Servicio | Puerto | Módulo |
|----------|--------|--------|
| TimescaleDB Quotes | 5433 | Quotes |
| TimescaleDB Capacity | 5434 | Capacity |
| Redis Dev | 6381 | Shared |
| quotes-api | 8000 | Quotes |
| capacity-api | 8001 | Capacity |

> **Source of Truth**: [opa-infrastructure-state/state.yaml](https://github.com/Ocaxtar/opa-infrastructure-state/blob/main/state.yaml)

---

## 🔧 Convenciones

| Elemento | Convención |
|----------|------------|
| **Idioma código** | Inglés |
| **Idioma interacción** | Español |
| **Formato commit** | `OPA-XXX: Descripción imperativa` |
| **Branches** | `username/opa-xxx-descripcion` |
| **Labels issues** | `Feature/Bug` + `opa-quotes-storage` |

---

## 🎯 Skills Disponibles (carga bajo demanda)

| Skill | Ubicación | Triggers |
|-------|-----------|----------|
| `git-linear-workflow` | `~/.copilot/skills/` | issue, branch, commit, PR |
| `linear-mcp-tool` | `~/.copilot/skills/` | error Linear, UUID |
| `run-efficiency` | `~/.copilot/skills/` | tokens, context |

**Skills supervisor** (consultar desde [supervisor](https://github.com/Ocaxtar/OPA_Machine)):
- `multi-workspace`, `contract-validator`, `ecosystem-auditor`, `infrastructure-lookup`

---

## 📚 Referencias

| Recurso | URL |
|---------|-----|
| Supervisor AGENTS.md | https://github.com/Ocaxtar/OPA_Machine/blob/main/AGENTS.md |
| opa-infrastructure-state | https://github.com/Ocaxtar/opa-infrastructure-state/blob/main/state.yaml |
| DB Schemas Source of Truth | https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/infrastructure/state-db-schemas.yaml.md |
| Service Inventory | https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/infrastructure/service-inventory.md |
| DASHBOARD | https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/DASHBOARD.md |

---

*Documento sincronizado con supervisor v2.1 (2026-01-26) - OPA-369*
