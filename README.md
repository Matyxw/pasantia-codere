# PC Monitor v2.0

[![CI](https://github.com/Matyxw/pasantia-codere/actions/workflows/ci.yml/badge.svg)](https://github.com/Matyxw/pasantia-codere/actions/workflows/ci.yml)
[![Release](https://github.com/Matyxw/pasantia-codere/actions/workflows/release.yml/badge.svg)](https://github.com/Matyxw/pasantia-codere/releases)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> Sistema de monitoreo en tiempo real de PCs en red corporativa.
> Diseñado para 200+ nodos, con detección automática de on/off, métricas en vivo,
> gráficos históricos, ejecución de comandos remotos y exportación a Excel.

---

## Arquitectura

```
┌──────────────────┐    Heartbeat (15s)    ┌───────────────────┐
│  AGENTE (cada PC) │ ◄──────────────────► │  SERVIDOR CENTRAL │
│  FastAPI :8001   │     HTTP REST          │  FastAPI :8000    │
│  psutil metrics  │                        │  SQLite + WAL     │
└──────────────────┘                        └───────────────────┘
                                                      │
                                               WebSocket (/ws)
                                                      │
                                           ┌──────────┴──────────┐
                                           │     DASHBOARD       │
                                           │  React + Vite :5173 │
                                           │  Apache ECharts     │
                                           └─────────────────────┘
```

## Quick Start — 3 pasos

```bash
# 1. Clonar e instalar
git clone https://github.com/Matyxw/pasantia-codere.git
cd pasantia-codere
Instalar_v2.bat                    # Instala todo

# 2. Iniciar el sistema completo
Iniciar_TODO.bat                   # Abre servidor + agente + dashboard

# 3. Abrir el panel
# → http://localhost:5173
```

## Features

| Feature | Estado |
|---|---|
| 🟢 Detección online/offline en tiempo real | ✅ |
| 📊 Métricas CPU / RAM / Disco en vivo | ✅ |
| 📈 Gráficos históricos con ECharts | ✅ |
| ⚡ WebSockets — sin polling | ✅ |
| 🔍 Escaneo automático de red | ✅ |
| 🖥 Terminal remota (whitelist de comandos) | ✅ |
| 📥 Exportación a Excel (.xlsx) | ✅ |
| 🔔 Notificaciones de escritorio Windows | ✅ |
| 🚀 Auto-start en Windows (Task Scheduler) | ✅ |
| 📦 Build a .exe standalone | ✅ (CI) |
| 🔐 Autenticación JWT + roles | 🔜 |
| 🏢 Integración Active Directory | 🔜 |
| 📧 Alertas por email / Teams | 🔜 |

## Documentación

- [Arquitectura detallada](docs/arquitectura.md)
- [Referencia API](docs/api-reference.md)
- [Guía de despliegue](docs/deployment.md)
- [Troubleshooting](docs/troubleshooting.md)

## Para Desarrolladores

Ver [AGENTS.md](AGENTS.md) para contexto completo de arquitectura, convenciones y comandos.

```bash
# Setup de desarrollo
pip install -e ".[dev]"
pre-commit install

# Tests
pytest

# Lint
ruff check . --fix
```

## Licencia

MIT © 2024 Matyxw
