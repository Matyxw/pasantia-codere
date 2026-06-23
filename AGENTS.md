# AGENTS.md — Contexto para Agentes IA

> Este archivo le dice a cualquier agente IA (Antigravity IDE, Claude Code, GitHub Copilot,
> Cursor, Continue.dev) exactamente cómo funciona este proyecto, qué convenciones seguir,
> y qué **no** hacer. Léelo antes de cualquier tarea.

---

## ¿Qué es este proyecto?

**PC Monitor v2.0** — Sistema de monitoreo en tiempo real de PCs en red corporativa.
Diseñado para escalar a 200+ nodos en entornos empresariales con Active Directory.

- **Arquitectura**: Push/Heartbeat (no pull)
- **Comunicación en tiempo real**: WebSockets
- **Almacenamiento**: SQLite con WAL mode (SQLAlchemy)
- **Stack Python**: FastAPI + uvicorn + APScheduler + psutil
- **Stack Frontend**: React 18 + Vite 5 + Apache ECharts

---

## Arquitectura del Sistema

```
┌─────────────────────┐        HTTP :8001        ┌──────────────────┐
│   AGENTE (cada PC)  │ ◄────────────────────── │                  │
│   FastAPI :8001     │ ─────────────────────► │  SERVIDOR CENTRAL │
│   psutil metrics    │    APScheduler 15s       │  FastAPI :8000   │
└─────────────────────┘                          │  SQLite + WAL    │
                                                 │  WebSocket       │
┌─────────────────────┐                          └──────────────────┘
│   DASHBOARD         │ ◄── WebSocket ws://      │
│   React + Vite      │ ──── REST API /api/      │
│   Puerto :5173      │                          │
│   ECharts           │                          │
└─────────────────────┘
```

---

## Comandos más importantes

```bash
# Arrancar el sistema completo
Iniciar_TODO.bat                         # Windows — abre todo

# Solo el servidor central
cd servidor && python main.py            # http://localhost:8000

# Solo el agente
cd agente && python agente.py            # http://localhost:8001

# Dashboard
cd dashboard && npm run dev              # http://localhost:5173

# Correr tests
pytest                                   # Suite completa con coverage
pytest tests/test_api_pcs.py -v         # Solo un archivo
pytest -k "test_register" -v            # Solo tests que matcheen el nombre

# Linting
ruff check . --fix                       # Lint + autofix Python
ruff format .                            # Formato Python
cd dashboard && npm run lint             # Lint JS/JSX

# Pre-commit (calidad antes de commitear)
pre-commit run --all-files               # Correr todos los hooks manualmente

# Build .exe
python build/build_agent.py              # Empaquetar agente
python build/build_server.py             # Empaquetar servidor

# Git convencional
git commit -m "feat: agregar autenticación JWT"
git commit -m "fix: corregir timeout del heartbeat"
git commit -m "docs: actualizar API reference"
```

---

## Estructura de Carpetas

```
pasantia-codere/
│
├── agente/                         # Agente FastAPI — corre en cada PC
│   ├── agente.py                   # App principal FastAPI (puerto 8001)
│   ├── requirements.txt            # Dependencias del agente
│   └── instalar_servicio.ps1       # Registro en Windows Task Scheduler
│
├── servidor/                       # Servidor Central
│   ├── main.py                     # App FastAPI + WebSocket Manager
│   ├── database.py                 # SQLAlchemy models + engine (WAL)
│   ├── scheduler.py                # APScheduler heartbeat (cada 15s)
│   ├── notificaciones.py           # Alertas de escritorio (plyer)
│   └── config.py                   # Configuración tipada (pydantic-settings)
│
├── dashboard/                      # Frontend React + Vite
│   └── src/
│       ├── App.jsx                 # Root + WebSocket connection manager
│       ├── App.css                 # Design system (dark mode glassmorphism)
│       └── components/
│           ├── Header.jsx          # Stats + botones de acción
│           ├── PCGrid.jsx          # Grid de cards de PCs
│           ├── PCCard.jsx          # Card individual con barras de métricas
│           ├── PCModal.jsx         # Modal detalle (4 tabs)
│           ├── MetricsChart.jsx    # Gráficos ECharts CPU/RAM/Disk
│           ├── Sidebar.jsx         # Timeline de eventos en vivo
│           ├── RegisterModal.jsx   # Formulario registrar PC
│           ├── ScanModal.jsx       # Escaneo de red + registro masivo
│           └── AlertToast.jsx      # Notificaciones toast
│
├── tests/                          # Tests Python (pytest)
├── docs/                           # Documentación técnica
├── build/                          # Scripts de empaquetado PyInstaller
│
├── .github/workflows/              # GitHub Actions
│   ├── ci.yml                      # CI en cada push
│   └── release.yml                 # Build .exe + GitHub Release en tags
│
├── pyproject.toml                  # Config Python unificada (Ruff, pytest, mypy)
├── .env.example                    # Template de variables de entorno
├── .pre-commit-config.yaml         # Hooks de calidad automática
├── .editorconfig                   # Formato consistente entre editores
├── .gitignore                      # Archivos a excluir del repo
└── .gitattributes                  # Line endings por tipo de archivo
```

---

## Base de Datos — Modelos SQLAlchemy

```python
# Tabla: pcs
PC(id, ip, name, hostname, os, registered_at, status, last_seen, last_offline, last_metrics)

# Tabla: events
Event(id, pc_id, pc_name, pc_ip, type, timestamp, downtime_seconds)
# type = "online" | "offline"

# Tabla: metrics
Metric(id, pc_id, timestamp, cpu_percent, ram_percent, ram_used_gb, ram_total_gb,
       disk_percent, processes_count, network_connections, uptime_seconds)
```

---

## API REST del Servidor (puerto 8000)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/pcs` | Lista todas las PCs registradas |
| POST | `/api/pcs` | Registrar nueva PC `{ip, name}` |
| GET | `/api/pcs/{id}` | Detalle de una PC |
| DELETE | `/api/pcs/{id}` | Eliminar PC |
| GET | `/api/pcs/{id}/metrics?limit=60` | Historial de métricas |
| GET | `/api/pcs/{id}/events` | Historial de eventos |
| POST | `/api/pcs/{id}/execute` | Ejecutar comando remoto `{command}` |
| GET | `/api/events` | Todos los eventos (las últimas 100) |
| GET | `/api/scan` | Escanear red local buscando agentes |
| GET | `/api/stats` | Estadísticas globales |
| GET | `/api/export/excel` | Exportar datos a .xlsx |
| WS | `/ws` | WebSocket de tiempo real |

## API REST del Agente (puerto 8001)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Health check (usado por heartbeat) |
| GET | `/info` | Info estática del sistema |
| GET | `/metrics` | Métricas en tiempo real |
| POST | `/execute` | Ejecutar comando (whitelist: dir, ipconfig...) |

---

## Eventos WebSocket

El servidor emite estos tipos de mensajes JSON:

```json
// Al conectar: estado completo
{"type": "initial_state", "data": {"pcs": [...], "events": [...]}}

// Cada 15s: actualización de métricas de una PC
{"type": "metrics_update", "data": {"pc_id": 1, "ip": "...", "name": "...", "status": "online", "metrics": {...}}}

// Cuando una PC cambia de estado
{"type": "status_change", "data": {"pc_id": 1, "name": "...", "ip": "...", "status": "offline"}}

// Cuando ocurre un evento de on/off
{"type": "event", "data": {"pc_id": 1, "pc_name": "...", "event_type": "offline", "timestamp": "..."}}

// Cuando se registra una nueva PC
{"type": "pc_registered", "data": {...pc completo...}}

// Cuando se elimina una PC
{"type": "pc_deleted", "data": {"pc_id": 1}}
```

---

## Convenciones de Código

### Python
- **Formato**: Ruff (Black-compatible, 100 chars por línea)
- **Imports**: ordenados automáticamente por Ruff (isort)
- **Type hints**: obligatorios en funciones públicas
- **Docstrings**: estilo Google para módulos y funciones complejas
- **Async**: usar `async def` siempre en endpoints FastAPI
- **Errores**: usar `HTTPException` de FastAPI, no raises directos

### JavaScript / React
- **Formato**: Prettier (2 espacios, comillas simples)
- **Componentes**: funcionales con hooks, no class components
- **Estado**: `useState` + `useCallback` + `useEffect` — sin Redux por ahora
- **CSS**: Vanilla CSS en `App.css` con design tokens (CSS variables)
- **Nombrado**: PascalCase para componentes, camelCase para funciones y variables

### Git — Conventional Commits (OBLIGATORIO)
```
feat: nueva funcionalidad
fix: corrección de bug
docs: solo documentación
style: formato, sin cambios de lógica
refactor: refactor sin nueva func ni fix
perf: mejora de performance
test: agregar o modificar tests
build: sistema de build, dependencias
ci: cambios en GitHub Actions
chore: otras tareas de mantenimiento
```

---

## Reglas Críticas — Nunca Hacer

1. **No hardcodear IPs, puertos ni claves** en el código — usar `config.py` / `.env`
2. **No commitear el archivo `.env`** — solo `.env.example`
3. **No commitear directamente a `main`** — usar branches + PR
4. **No usar `shell=True` en subprocess** sin validar contra la whitelist del agente
5. **No cambiar el nombre de los modelos SQLAlchemy** sin migración de datos
6. **No usar `import *`** en ningún archivo
7. **No ignorar errores silenciosamente** (`except: pass`) — loguear siempre
8. **No bloquear el event loop** de FastAPI con llamadas síncronas lentas

---

## Roadmap (futuro)

- [ ] **Autenticación JWT** con roles (admin / viewer)
- [ ] **Integración Active Directory** (SSO con LDAP/AD)
- [ ] **Alertas por email** (SMTP) cuando una PC se cae
- [ ] **Alertas por Teams/Slack** webhook
- [ ] **Umbral de alertas**: CPU > 90%, RAM > 95%, Disco > 95%
- [ ] **Historiales largos**: migrar a InfluxDB o TimescaleDB para 1 año+
- [ ] **Mapa de red visual** (nodos y conexiones)
- [ ] **Dashboard mobile** (PWA)
- [ ] **Actualizaciones remotas** del agente desde el servidor

---

## Variables de Entorno Disponibles

Ver `.env.example` para la lista completa con descripciones.
En código, importar siempre desde `servidor/config.py`:

```python
from config import settings

print(settings.server_port)         # 8000
print(settings.heartbeat_interval)  # 15
print(settings.cors_origins_list)   # ["http://localhost:5173"]
print(settings.database_url)        # "sqlite:///./monitor.db"
```
