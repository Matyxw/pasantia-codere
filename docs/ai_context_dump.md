# AI Context Dump — PC Monitor v2.0
*Auto-generado el: 2026-06-23T02:42:51.767772*

Este archivo es un snapshot automático del proyecto. Léelo para actualizar tu contexto.

## Estructura de Archivos
```text
AGENTS.md
Iniciar_Agente.bat
Iniciar_TODO.bat
Instalar_v2.bat
README.md
agente/agente.py
agente/instalar_servicio.ps1
agente/requirements.txt
build/build_agent.py
build/build_server.py
dashboard/.gitignore
dashboard/README.md
dashboard/eslint.config.js
dashboard/index.html
dashboard/package-lock.json
dashboard/package.json
dashboard/public/favicon.svg
dashboard/public/icons.svg
dashboard/src/App.css
dashboard/src/App.jsx
dashboard/src/__tests__/PCCard.test.jsx
dashboard/src/__tests__/setup.js
dashboard/src/assets/hero.png
dashboard/src/assets/react.svg
dashboard/src/assets/vite.svg
dashboard/src/components/AlertToast.jsx
dashboard/src/components/Header.jsx
dashboard/src/components/MetricsChart.jsx
dashboard/src/components/PCCard.jsx
dashboard/src/components/PCGrid.jsx
dashboard/src/components/PCModal.jsx
dashboard/src/components/RegisterModal.jsx
dashboard/src/components/ScanModal.jsx
dashboard/src/components/Sidebar.jsx
dashboard/src/index.css
dashboard/src/main.jsx
dashboard/vite.config.js
docs/arquitectura.md
docs/deployment.md
docs/troubleshooting.md
pyproject.toml
servidor/config.py
servidor/database.py
servidor/main.py
servidor/monitor.db-shm
servidor/monitor.db-wal
servidor/notificaciones.py
servidor/requirements.txt
servidor/scheduler.py
tests/conftest.py
tests/test_agente.py
tests/test_api_pcs.py
```

## Dependencias Instaladas
### Python (pyproject.toml)
```toml
[project]
name = "pc-monitor"
version = "2.0.0"
description = "Enterprise PC monitoring system — real-time, WebSocket-first, 200+ nodes"
authors = [
    { name = "Matyxw", email = "" },
]
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.11"

# ─────────────────────────────────────
#  DEPENDENCIAS DE PRODUCCION
# ─────────────────────────────────────
dependencies = [
    # Servidor central
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "apscheduler>=3.10.0",
  
```

### Node (package.json)
```json
{
  "echarts": "^6.1.0",
  "echarts-for-react": "^3.0.6",
  "react": "^19.2.6",
  "react-dom": "^19.2.6",
  "@eslint/js": "^10.0.1",
  "@testing-library/dom": "^10.4.1",
  "@testing-library/jest-dom": "^6.9.1",
  "@testing-library/react": "^16.3.2",
  "@types/react": "^19.2.14",
  "@types/react-dom": "^19.2.3",
  "@vitejs/plugin-react": "^6.0.1",
  "eslint": "^10.3.0",
  "eslint-plugin-react-hooks": "^7.1.1",
  "eslint-plugin-react-refresh": "^0.5.2",
  "globals": "^17.6.0",
  "jsdom": "^29.1.1",
  "vite": "^8.0.12",
  "vitest": "^4.1.9"
}
```

