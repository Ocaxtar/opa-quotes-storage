**Nombre**: OPA_Quotes_Storage  
**Equipo**: OPA  
**Repositorio**: https://github.com/Ocaxtar/opa-quotes-storage  
**Workspace**: `opa-quotes-storage`  
**Rol**: Almacenamiento de cotizaciones históricas y en tiempo real

## Contexto del Servicio

Este servicio es responsable de almacenar y servir cotizaciones de acciones (ticks) capturadas por el streamer. Utiliza TimescaleDB para gestión eficiente de series temporales.

## 📚 Guías Especializadas (CONSULTAR PRIMERO)

**Ver guías en repositorio supervisor**: [OPA_Machine/docs/guides/](https://github.com/Ocaxtar/OPA_Machine/tree/main/docs/guides)

| Guía | Propósito | Cuándo consultar |
|------|-----------|------------------|
| **[workflow-git-linear.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/guides/workflow-git-linear.md)** | Workflow Git+Linear completo | Al trabajar en issues (branch, commit, merge, cierre) |
| **[code-conventions.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/guides/code-conventions.md)** | Estándares código, testing, CI/CD | Al escribir código, configurar tests, Docker |
| **[linear-mcp-quickstart.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/guides/linear-mcp-quickstart.md)** | Errores comunes Linear MCP | Al usar mcp_linear tools (errores, fixes) |

**Convención idiomática**:
- **Código y nombres técnicos** (clases, funciones, commits): **Inglés**
- **Interacción con usuarios** (comentarios Linear, PRs, docs narrativa): **Español**

## 🛡️ Validación de Convenciones - Checkpoint Obligatorio

**REGLA CRÍTICA**: Antes de ejecutar acciones que modifican estado (commits, PRs, issues Done), validar cumplimiento de convenciones.

### Convenciones No Negociables

| Convención | Requisito | Documento |
|------------|-----------|-----------|
| **Commits** | DEBEN incluir referencia a issue (`OPA-XXX`) en mensaje | [workflow-git-linear.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/guides/workflow-git-linear.md) |
| **Issues** | DEBEN crearse en Linear ANTES de implementar fix | [workflow-git-linear.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/guides/workflow-git-linear.md) |
| **Branches** | DEBEN seguir patrón `username/opa-xxx-descripcion` | [workflow-git-linear.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/guides/workflow-git-linear.md) |
| **PRs** | DEBEN enlazar a issue en descripción | [workflow-git-linear.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/guides/workflow-git-linear.md) |
| **Issues Done** | DEBEN tener tests ejecutados y pasando | [code-conventions.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/guides/code-conventions.md) |

## 📝 Regla Crítica: Comentarios vs Descripción en Issues

**PRINCIPIO**: La **descripción** de una issue es la **especificación inicial**. Los **comentarios** son el **registro de progreso**.

**Comportamiento requerido**:

| Acción | Tool Correcta | Tool Incorrecta |
|--------|---------------|-----------------|
| Reportar avance parcial | `mcp_linear_create_comment()` | ❌ `mcp_linear_update_issue(body=...)` |
| Reactivar issue cerrada | `mcp_linear_create_comment()` + `update_issue(state="In Progress")` | ❌ Solo modificar descripción |
| Documentar error encontrado | `mcp_linear_create_comment()` | ❌ Editar descripción |
| Añadir diagnóstico | `mcp_linear_create_comment()` | ❌ Modificar descripción |
| Cerrar con resumen | `mcp_linear_create_comment()` + `update_issue(state="Done")` | ❌ Solo cambiar estado |

## 🔧 Gestión de Tools MCP (Linear, GitHub, Pylance)

**REGLA CRÍTICA**: Muchas tools de Linear/GitHub/Pylance requieren activación explícita antes de uso.

### Tools que Requieren Activación

| Grupo Linear | Tool de Activación | Cuándo Usar |
|--------------|-------------------|-------------|
| **Issues/Labels/Proyectos** | `activate_issue_management_tools()` | Crear/actualizar issues, labels, proyectos |
| **Documentos** | `activate_document_management_tools()` | Crear/actualizar documentos Linear |
| **Tracking** | `activate_issue_tracking_tools()` | Obtener status, attachments, branches |
| **Workspace** | `activate_workspace_overview_tools()` | Listar proyectos, labels, teams, users |
| **Teams/Users** | `activate_team_and_user_management_tools()` | Info de teams, users, ciclos |

| Grupo GitHub | Tool de Activación | Cuándo Usar |
|--------------|-------------------|-------------|
| **PRs Review** | `activate_pull_request_review_tools()` | Crear/revisar PRs, comentarios review |
| **Repos/Branches** | `activate_repository_management_tools()` | Crear repos, branches, PRs, merges |

**Ver**: [workflow-git-linear.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/guides/workflow-git-linear.md) para workflow completo de activación y recuperación automática.

## ⚠️ Validación Pre-cierre de Issue (CRÍTICO)

**REGLA CRÍTICA**: Antes de `mcp_linear_update_issue(state="Done")`, OBLIGATORIO ejecutar checklist.

### Checklist Pre-cierre (TODOS los items)

```markdown
- [ ] 1. Tests ejecutados localmente (`poetry run pytest`) → PASS
- [ ] 2. Commits incluyen referencia issue (`OPA-XXX`) → Verificado
- [ ] 3. Branch mergeada a main → Confirmado
- [ ] 4. PR tiene descripción con enlace a issue → Verificado
- [ ] 5. Documentación actualizada (si aplica) → Confirmado
- [ ] 6. Contrato/API respetado (si aplica) → Verificado
- [ ] 7. Health check pasando (si servicio) → Confirmado
- [ ] 8. COMENTARIO con resumen añadido → Ejecutado
```

### Template Comentario Pre-cierre

**OBLIGATORIO**: Añadir comentario con este formato ANTES de cambiar estado:

```markdown
## 🤖 Agente opa-quotes-storage: Resumen de Cierre

### ✅ Completado
- [Descripción concisa de lo implementado]
- [Tests ejecutados y resultado]
- [Commits relevantes con SHAs]

### 🔍 Validaciones
- [ ] Tests pasando: [Comando ejecutado]
- [ ] Commits con OPA-XXX: [Lista de commits]
- [ ] Documentación actualizada: [Archivos modificados]

### 📎 Referencias
- PR: [Link si aplica]
- Commits: [SHAs]
- Contratos respetados: [Links si aplica]

**Fecha sincronización normativa**: 2026-01-14  
**Versión normativa**: 1.0.0
```

### Workflow Correcto de Cierre

```python
# 1. PRIMERO: Añadir comentario con resumen
mcp_linear_create_comment(
    issueId="OPA-XXX",
    body="## 🤖 Agente opa-quotes-storage: Resumen de Cierre\n\n..."
)

# 2. SEGUNDO: Cambiar estado a Done
mcp_linear_update_issue(
    id="OPA-XXX",
    state="Done"
)
```

### ❌ Errores Comunes

| Error | Consecuencia | Corrección |
|-------|--------------|------------|
| Cambiar estado sin comentario | Pérdida de contexto del trabajo | Añadir comentario primero |
| Tests no ejecutados | Merge rompe main | `poetry run pytest` antes |
| Commit sin OPA-XXX | No se linkea automáticamente | Rehacer commit con referencia |
| Modificar descripción en vez de comentar | Pérdida de historial | Usar `create_comment()` siempre |
| No verificar branch mergeada | Issue Done sin código en main | Verificar merge primero |

### Validación Automática

Si el agente detecta que intentas cerrar issue sin cumplir checklist:

```markdown
⚠️ **Acción Bloqueada - Checklist Pre-cierre Incompleta**

He detectado que intentas cerrar OPA-XXX sin:
- [ ] Tests ejecutados
- [ ] Comentario de resumen añadido

**Acción requerida**: Completar checklist antes de `state="Done"`.
```

## Tecnologías Clave

- **Base de datos**: PostgreSQL + TimescaleDB
- **Framework**: FastAPI
- **Testing**: pytest
- **Container**: Docker

## Contacto y Escalación

**Para decisiones de arquitectura**: Mencionar en el canal del equipo  
**Para bugs críticos**: Usar label `urgent` en Linear  

---

📝 **Este documento debe actualizarse conforme evolucione el servicio**