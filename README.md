# PC Monitor v2.0
> Contexto técnico: Leer `AGENTS.md` (formato denso).

**Inicio Rápido**:
```bash
# Servidor
cd servidor && python main.py
# Agente
cd agente && python agente.py
# Dashboard
cd dashboard && npm run dev
```
Arquitectura Push: Agentes -> POST /api/agent/push -> FastAPI -> WebSocket -> React.
