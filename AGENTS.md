# AGENTS.md - opa-quotes-storage

> 🎯 **Guía para agentes IA** - Repositorio operativo del ecosistema OPA_Machine.  
> **Documentación completa**: [Supervisor OPA_Machine](https://github.com/Ocaxtar/OPA_Machine)

---

## 🚦 Pre-Flight Checklist (OBLIGATORIO)

**Antes de cualquier operación**:

| Acción | Recurso | Cuándo |
|--------|---------|--------|
| Verificar puertos/Docker | [service-inventory.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/infrastructure/service-inventory.md) | ⚠️ Antes de Docker |
| Cargar skill necesario | [Skills INDEX](https://github.com/Ocaxtar/OPA_Machine/blob/main/.github/skills/INDEX.md) | Antes de tarea compleja |
| Trabajar en issue | Skill `git-linear-workflow` | Antes de branch/commit |
| Usar Linear MCP tools | Skill `linear-mcp-tool` | Si tool falla |

---

## 📋 Información del Proyecto

**Nombre**: opa-quotes-storage  
**Módulo**: Cotización (Módulo 2)  
**Tipo**: storage (TimescaleDB)  
**Fase**: 1  
**Equipo Linear**: OPA  
**Repositorio**: https://github.com/Ocaxtar/opa-quotes-storage  
**Puerto asignado**: 5433

### Rol en el Ecosistema

Almacenamiento de cotizaciones en tiempo real usando TimescaleDB. Recibe datos del streamer y los persiste en hypertables optimizadas para series temporales.

### Dependencias

| Servicio | Puerto | Propósito |
|----------|--------|-----------|
| TimescaleDB | 5433 | Base de datos principal |

---

## ⚠️ Reglas Críticas

### 1. Prefijo en Comentarios Linear

```
🤖 Agente opa-quotes-storage: [mensaje]
```

**Obligatorio** en todo comentario. Auditoría supervisor detecta violaciones.

### 2. Commits con Referencia a Issue

```
❌ git commit -m "Fix bug"
✅ git commit -m "OPA-XXX: Fix bug description"
```

### 3. Puerto 5433 (NO 5432)

```
❌ localhost:5432 → Conflicto con PostgreSQL local Windows
✅ localhost:5433 → Puerto asignado a este servicio
```

### 4. Pre-Done Checklist

Antes de mover issue a Done:
- [ ] Código commiteado y pusheado
- [ ] Tests pasan (si aplica)
- [ ] Comentario de cierre con prefijo
- [ ] Verificar archivos en GitHub web (no solo local)

---

## 🔧 Convenciones

| Elemento | Convención |
|----------|------------|
| Idioma código | Inglés |
| Idioma comentarios | Español |
| Commits | `OPA-XXX: Descripción` |
| Python | 3.12 (NO 3.13) |
| DB | TimescaleDB (PostgreSQL 14) |

---

## 📚 Skills Disponibles

| Skill | Propósito |
|-------|-----------|
| `git-linear-workflow` | Workflow Git+Linear |
| `linear-mcp-tool` | Errores MCP Linear |
| `run-efficiency` | Gestión tokens |

> Ver [INDEX.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/.github/skills/INDEX.md) para lista completa.

---

## 🔗 Referencias Supervisor

| Documento | Propósito |
|-----------|-----------|
| [AGENTS.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/AGENTS.md) | Guía maestra |
| [service-inventory.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/infrastructure/service-inventory.md) | Puertos y conflictos |
| [ROADMAP.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/ROADMAP.md) | Fases del proyecto |
| [Contratos](https://github.com/Ocaxtar/OPA_Machine/tree/main/docs/contracts) | APIs y schemas |

---

*Actualizado por OPA-277 Context-Driven Architecture initiative. 2026-01-19*
