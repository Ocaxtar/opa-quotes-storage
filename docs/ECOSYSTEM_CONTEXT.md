# ECOSYSTEM_CONTEXT.md - opa-quotes-storage

## Posición en el Ecosistema

Este servicio es el **storage layer** del **Módulo 5 (Cotización)**, responsable del almacenamiento persistente de cotizaciones de mercado en tiempo real usando TimescaleDB.

```
                            ┌─────────────────────────────────────┐
                            │       OPA_Machine (Supervisor)      │
                            │  Documentación, ADRs, Contratos     │
                            └──────────────────┬──────────────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
         ┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
         │  Módulo 1        │       │  Módulo 5        │       │  Módulo 4        │
         │  Capacidad       │       │  Cotización      │       │  Predicción      │
         └──────────────────┘       └────────┬─────────┘       └──────────────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
                    ▼                        ▼                        ▼
         ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
         │ quotes-streamer  │────▶│ quotes-storage   │────▶│   quotes-api     │
         │   (upstream)     │     │  ★ ESTE REPO ★   │     │  (downstream)    │
         └──────────────────┘     └──────────────────┘     └──────────────────┘
               yfinance                TimescaleDB              FastAPI REST
```

## Flujo de Datos

1. **Entrada** (desde `opa-quotes-streamer`):
   - Endpoint: `POST /v1/quotes/batch`
   - Formato: JSON batch con quotes normalizadas
   - Contrato: `docs/contracts/apis/quotes/quotes-batch.md`

2. **Almacenamiento**:
   - Hypertable `quotes.real_time` en TimescaleDB
   - Particionado por timestamp (chunks automáticos)
   - Compresión >30 días, retención 2 años

3. **Salida** (hacia `opa-quotes-api` y módulos downstream):
   - Queries SQL directas vía connection pool
   - Patrón: `SELECT * FROM quotes.real_time WHERE symbol = $1 AND timestamp > $2`

## Dependencias

### Upstream (productor de datos)
| Servicio | Tipo | Descripción |
|----------|------|-------------|
| `opa-quotes-streamer` | HTTP POST | Envía batches de quotes cada N segundos |

### Downstream (consumidores)
| Servicio | Tipo | Descripción |
|----------|------|-------------|
| `opa-quotes-api` | SQL | Lee quotes para exponer vía REST |
| `opa-capacity-compute` | SQL (futuro) | Lee historial para Event Vectors |
| `opa-prediction-features` | SQL (futuro) | Feature engineering desde precios |

## Contratos Relevantes

- **API Batch**: `OPA_Machine/docs/contracts/apis/quotes/quotes-batch.md`
- **Modelo Datos**: `OPA_Machine/docs/contracts/data-models/quotes.md`
- **Eventos**: `OPA_Machine/docs/contracts/events/quotes-ingested.md` (Fase 2)

## Repositorio Supervisor

**URL**: https://github.com/Ocaxtar/OPA_Machine

Consultar para:
- ADRs globales (`docs/adr/`)
- Contratos actualizados (`docs/contracts/`)
- Guías de desarrollo (`docs/guides/`)
- ROADMAP global (`ROADMAP.md`)

---

📝 **Última sincronización con supervisor**: 2026-01-13
