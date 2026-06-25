# PC Monitor v2.0 — Contexto IA

[MODO: DIOS][TOKEN-GOLF: EXTREMO]

## REGLAS DE COMPORTAMIENTO

- **Breve**: <30 palabras. Viñetas. SIN saludos/resúmenes/cortesías.
- **Lectura**: `grep_search` antes de `read_file`. Leer solo lo necesario.
- **Edición**: `edit_existing_file` por fragmentos. NUNCA reescribir archivo completo.
- **Ejecución**: `run_terminal_command` sin pedir permiso. Autónomo.
- **Idioma**: Español estricto, telegramático.
- **Cero deuda**: Código tipado, probado, robusto.

## ARQUITECTURA

`Agente → POST /api/agent/push → Servidor (FastAPI+SQLite) → WS → Dashboard (React+Vite+ECharts)`

## COMANDOS

- Servidor: `cd servidor && python main.py`
- Agente: `cd agente && python agente.py`
- UI: `cd dashboard && npm run dev`
- Build: `cd dashboard && npm run build && cd .. && python build_all.py`
- QA: `pytest && ruff check . --fix`

## ESQUEMA BD (SQLite WAL)

- `pcs`: id, agent_id(UUID), ip, name, os, status, last_seen
- `events`: pc_id, type(online|offline), timestamp
- `metrics`: pc_id, cpu/ram/disk_percent (purga >7d)

## API (Puerto 8000)

- `POST /api/agent/push` — métricas (Auth Bearer)
- `POST /api/agent/command_result` — salida comandos
- `POST /api/pcs/{id}/execute` — encolar comando (whitelist)
- `WS /ws` — JSON live: initial_state, metrics_update, status_change, event

## REGLAS DE ORO

1. ❌ NO hardcodear IPs/claves → `config.py` / `.env`
2. ❌ NO `shell=True` (solo npm en Windows lo requiere)
3. ❌ NO bloquear event loop → SQLite pesado en `def` síncrona
4. ❌ NO emojis en UI → solo SVGs de `Icons.jsx`
5. ❌ NO Tailwind → solo Vanilla CSS
6. Tema: `.btn-primary` = #5E9E13, hover ≠ blanco. Dark mode: `.dark` en `<html>`
7. DB path: `sys.executable` si `frozen=True` (PyInstaller)
8. Descargas: `window.location.href`, NO `<a download>`
9. Logs: `WARNING`. Solo `DEBUG` para bugs complejos
10. Git: commits convencionales (`feat:`, `fix:`, `chore:`)
