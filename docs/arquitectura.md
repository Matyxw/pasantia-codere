# Arquitectura
> Consultar `AGENTS.md` para detalles completos.

**Flujo PUSH**:
`Agente` --(Métricas + IP + UUID)--> `FastAPI (:8000)` --(Graba DB SQLite WAL)--> `WebSocket` --(Broadcast JSON)--> `React (:5173)`

**Seguridad**:
- Token Bearer en headers.
- Cero `shell=True` en Agente (RCE mitigado).
