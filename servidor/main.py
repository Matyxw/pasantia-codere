"""
main.py — Servidor Central FastAPI
REST API + WebSockets + Heartbeat Scheduler
Puerto: 8000
"""

import asyncio
import json
import logging
import os
import socket
import sys
import threading
import uuid
from datetime import datetime

# Configuración del logger para el servidor
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] SERVER - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ServidorCentral")

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

import scheduler as sched
from database import PC, Event, Metric, SessionLocal, get_db

try:
    from openpyxl import Workbook  # noqa: F401
    from openpyxl.styles import Alignment, Font, PatternFill  # noqa: F401
except ImportError:
    pass

pending_commands = {}
command_results = {}

# ──────────────────────────────────────────
# App
# ──────────────────────────────────────────
app = FastAPI(
    title="PC Monitor Central",
    version="2.0.0",
    description="Sistema de monitoreo de PCs en red — Servidor Central",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────
# WebSocket Manager
# ──────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, message: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error("Error transmitiendo a WebSocket. Cliente desconectado abruptamente: %s", e)
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


# ──────────────────────────────────────────
# Lifecycle
# ──────────────────────────────────────────
def udp_discovery_server():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(('', 8002))
        while True:
            data, addr = s.recvfrom(1024)
            if b"CODERE_DISCOVERY_REQUEST" in data:
                s.sendto(b"CODERE_SERVER", addr)
    except Exception as e:
        logger.error("[UDP] Error fatal en discovery server: %s", e, exc_info=True)

@app.on_event("startup")
async def on_startup():
    loop = asyncio.get_event_loop()
    sched.init(loop, manager.broadcast)
    sched.start()

    t = threading.Thread(target=udp_discovery_server, daemon=True)
    t.start()

    print("[Server] Servidor Central iniciado en http://0.0.0.0:8000")


@app.on_event("shutdown")
async def on_shutdown():
    sched.stop()


# ──────────────────────────────────────────
# WebSocket endpoint
# ──────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        # Enviar estado inicial completo
        db = SessionLocal()
        pcs = db.query(PC).all()
        events = db.query(Event).order_by(Event.timestamp.desc()).limit(50).all()
        db.close()

        await ws.send_json({
            "type": "initial_state",
            "data": {
                "pcs": [_pc_to_dict(pc) for pc in pcs],
                "events": [_event_to_dict(e) for e in events],
            },
        })

        # Mantener conexion viva (recibir pings del cliente)
        while True:
            await ws.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception as e:
        logger.error("Error inesperado en WebSocket endpoint: %s", e, exc_info=True)
        manager.disconnect(ws)


# ──────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────
def _pc_to_dict(pc: PC) -> dict:
    last_metrics = None
    if pc.last_metrics:
        try:
            last_metrics = json.loads(pc.last_metrics)
        except json.JSONDecodeError as e:
            logger.error("Corrupción de datos JSON detectada para PC ID %s. Detalle: %s", pc.id, e)
    return {
        "id": pc.id,
        "ip": pc.ip,
        "name": pc.name,
        "hostname": pc.hostname,
        "os": pc.os,
        "registered_at": pc.registered_at,
        "status": pc.status,
        "last_seen": pc.last_seen,
        "last_offline": pc.last_offline,
        "last_metrics": last_metrics,
    }


def _event_to_dict(e: Event) -> dict:
    return {
        "id": e.id,
        "pc_id": e.pc_id,
        "pc_name": e.pc_name,
        "ip": e.pc_ip,
        "type": e.type,
        "timestamp": e.timestamp,
        "downtime_seconds": e.downtime_seconds,
    }


def _metric_to_dict(m: Metric) -> dict:
    return {
        "timestamp": m.timestamp,
        "cpu": m.cpu_percent,
        "ram": m.ram_percent,
        "ram_used_gb": m.ram_used_gb,
        "ram_total_gb": m.ram_total_gb,
        "disk": m.disk_percent,
        "processes": m.processes_count,
        "connections": m.network_connections,
        "uptime": m.uptime_seconds,
    }


# ──────────────────────────────────────────
# REST API — PCs
# ──────────────────────────────────────────
@app.get("/api/pcs")
def get_pcs(db: Session = Depends(get_db)):
    return [_pc_to_dict(pc) for pc in db.query(PC).all()]


@app.post("/api/pcs", status_code=201)
async def register_pc(body: dict, db: Session = Depends(get_db)):
    # Mantener retrocompatibilidad o registro manual
    ip = body.get("ip", "").strip()
    name = body.get("name", "").strip()

    if not ip or not name:
        raise HTTPException(400, "IP y nombre son requeridos")

    pc = db.query(PC).filter(PC.ip == ip).first()
    if pc:
        raise HTTPException(409, f"La IP {ip} ya está registrada")

    pc = PC(ip=ip, name=name, status="unknown")
    db.add(pc)
    db.commit()
    db.refresh(pc)

    await manager.broadcast({"type": "pc_registered", "data": _pc_to_dict(pc)})
    return _pc_to_dict(pc)


@app.get("/api/pcs/{pc_id}")
def get_pc(pc_id: int, db: Session = Depends(get_db)):
    pc = db.query(PC).filter(PC.id == pc_id).first()
    if not pc:
        raise HTTPException(404, "PC no encontrada")
    return _pc_to_dict(pc)


@app.delete("/api/pcs/{pc_id}")
async def delete_pc(pc_id: int, db: Session = Depends(get_db)):
    pc = db.query(PC).filter(PC.id == pc_id).first()
    if not pc:
        raise HTTPException(404, "PC no encontrada")
    db.delete(pc)
    db.commit()
    await manager.broadcast({"type": "pc_deleted", "data": {"pc_id": pc_id}})
    return {"message": f"PC {pc_id} eliminada"}


# ──────────────────────────────────────────
# REST API — Métricas e historial
# ──────────────────────────────────────────
@app.get("/api/pcs/{pc_id}/metrics")
def get_metrics(
    pc_id: int, limit: int = 60, db: Session = Depends(get_db)
):
    """Últimas N métricas de una PC (por defecto 60 = 15 minutos)"""
    rows = (
        db.query(Metric)
        .filter(Metric.pc_id == pc_id)
        .order_by(Metric.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [_metric_to_dict(m) for m in reversed(rows)]


@app.get("/api/pcs/{pc_id}/events")
def get_pc_events(
    pc_id: int, limit: int = 100, db: Session = Depends(get_db)
):
    rows = (
        db.query(Event)
        .filter(Event.pc_id == pc_id)
        .order_by(Event.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [_event_to_dict(e) for e in rows]


@app.get("/api/events")
def get_all_events(limit: int = 100, db: Session = Depends(get_db)):
    rows = (
        db.query(Event)
        .order_by(Event.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [_event_to_dict(e) for e in rows]


# ──────────────────────────────────────────
# REST API — Comandos remotos
# ──────────────────────────────────────────
@app.post("/api/pcs/{pc_id}/execute")
async def execute_command(
    pc_id: int, body: dict, db: Session = Depends(get_db)
):
    pc = db.query(PC).filter(PC.id == pc_id).first()
    if not pc:
        raise HTTPException(404, "PC no encontrada")
    if pc.status != "online":
        raise HTTPException(503, f"La PC {pc.name} no está online")

    command = body.get("command", "").strip()
    if not command:
        raise HTTPException(400, "Comando vacío")

    cmd_id = str(uuid.uuid4())
    if pc.ip not in pending_commands:
        pending_commands[pc.ip] = []

    pending_commands[pc.ip].append({
        "id": cmd_id,
        "command": command
    })

    # Simular polling bloqueante (para la UI actual)
    for _ in range(60): # 30 seg (0.5 * 60)
        if cmd_id in command_results:
            res = command_results.pop(cmd_id)
            return res
        await asyncio.sleep(0.5)

    raise HTTPException(504, "Timeout: el agente no recogió ni respondió el comando")


# ──────────────────────────────────────────
# REST API — Escaneo de red
# ──────────────────────────────────────────
@app.post("/api/agent/push")
async def agent_push(body: dict, db: Session = Depends(get_db)):
    ip = body.get("ip")
    name = body.get("name")
    hostname = body.get("hostname")
    os_info = body.get("os")
    metrics_data = body.get("metrics")

    if not ip or not metrics_data:
        raise HTTPException(400, "Faltan datos")

    pc = db.query(PC).filter(PC.ip == ip).first()
    now = datetime.now().isoformat()

    went_online = False
    downtime_secs = None

    if not pc:
        # Auto-registro
        pc = PC(ip=ip, name=name, hostname=hostname, os=os_info, status="online", registered_at=now, last_seen=now)
        db.add(pc)
        db.commit()
        db.refresh(pc)
        await manager.broadcast({"type": "pc_registered", "data": _pc_to_dict(pc)})
        went_online = True
    else:
        if pc.status != "online":
            went_online = True
            if pc.last_offline:
                try:
                    last_off = datetime.fromisoformat(pc.last_offline)
                    downtime_secs = (datetime.now() - last_off).total_seconds()
                except Exception as e:
                    logger.warning("Fallo al calcular downtime_secs para %s. Detalle: %s", pc.name, e)

        pc.status = "online"
        pc.last_seen = now
        pc.hostname = hostname or pc.hostname
        pc.os = os_info or pc.os

    disk_percent = 0.0
    disk_data = metrics_data.get("disk", {})
    if disk_data:
        first_disk = next(iter(disk_data.values()), {})
        disk_percent = first_disk.get("percent", 0.0)

    pc.last_metrics = json.dumps(metrics_data)

    metric = Metric(
        pc_id=pc.id,
        timestamp=now,
        cpu_percent=metrics_data.get("cpu", {}).get("percent", 0),
        ram_percent=metrics_data.get("memory", {}).get("percent", 0),
        ram_used_gb=metrics_data.get("memory", {}).get("used_gb", 0),
        ram_total_gb=metrics_data.get("memory", {}).get("total_gb", 0),
        disk_percent=disk_percent,
        processes_count=metrics_data.get("processes", {}).get("total", 0),
        network_connections=metrics_data.get("network", {}).get("connections", 0),
        uptime_seconds=metrics_data.get("uptime_seconds", 0),
    )
    db.add(metric)

    if went_online:
        event = Event(pc_id=pc.id, pc_name=pc.name, pc_ip=pc.ip, type="online", timestamp=now, downtime_seconds=downtime_secs)
        db.add(event)
        from notificaciones import notify_online
        notify_online(pc.name, pc.ip, downtime_secs)
        await manager.broadcast({
            "type": "event",
            "data": {"pc_id": pc.id, "pc_name": pc.name, "ip": pc.ip, "event_type": "online", "timestamp": now}
        })
        await manager.broadcast({"type": "status_change", "data": {"pc_id": pc.id, "ip": pc.ip, "status": "online", "timestamp": now}})

    db.commit()

    await manager.broadcast({
        "type": "metrics_update",
        "data": {
            "pc_id": pc.id,
            "ip": pc.ip,
            "name": pc.name,
            "status": "online",
            "last_seen": now,
            "metrics": metrics_data,
        },
    })

    # Entregar comandos pendientes
    cmds = pending_commands.pop(pc.ip, [])

    return {"status": "ok", "pending_commands": cmds}


@app.post("/api/agent/command_result")
async def agent_command_result(body: dict):
    cmd_id = body.get("command_id")
    result = body.get("result")
    if cmd_id:
        command_results[cmd_id] = result
    return {"status": "ok"}


# ──────────────────────────────────────────
# REST API — Export Excel
# ──────────────────────────────────────────
@app.get("/api/export/excel")
def export_excel(ip: str | None = None, db: Session = Depends(get_db)):
    from generar_excel_logic import build_excel_workbook
    wb = build_excel_workbook(db, target_ip=ip)

    filename = f"monitor_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join(os.path.dirname(__file__), filename)
    wb.save(filepath)

    return FileResponse(
        filepath,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ──────────────────────────────────────────
# Stats endpoint
# ──────────────────────────────────────────
@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    pcs = db.query(PC).all()
    return {
        "total": len(pcs),
        "online": sum(1 for p in pcs if p.status == "online"),
        "offline": sum(1 for p in pcs if p.status == "offline"),
        "unknown": sum(1 for p in pcs if p.status == "unknown"),
        "total_events": db.query(Event).count(),
        "total_metrics": db.query(Metric).count(),
        "ws_clients": len(manager.active),
    }


# ──────────────────────────────────────────
# Frontend estático (PyInstaller o Dev)
# ──────────────────────────────────────────
if getattr(sys, 'frozen', False):
    dist_path = os.path.join(sys._MEIPASS, "dashboard_dist")
else:
    dist_path = os.path.join(os.path.dirname(__file__), "..", "dashboard", "dist")

if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="dashboard")

# ──────────────────────────────────────────
# Run
# ──────────────────────────────────────────
if __name__ == "__main__":
    import os
    import sys
    import threading

    import webview

    # Evitamos crashes en modo noconsole mockeando sys.stdout
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')

    print("=" * 55)
    print("  PC MONITOR v2.0 — SERVIDOR CENTRAL (GUI)")
    print("=" * 55)

    def run_server():
        # log_config=None para que uvicorn no busque isatty en --noconsole
        uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)

    # Iniciar servidor FastAPI en segundo plano
    t = threading.Thread(target=run_server, daemon=True)
    t.start()

    class Api:
        def __init__(self):
            self.window = None

        def dummy(self):
            pass

    # Iniciar WebView en el hilo principal
    # Apuntamos al localhost:8000 donde corre nuestro dashboard montado en FastAPI
    api = Api()
    window = webview.create_window('Codere PC Monitor', 'http://127.0.0.1:8000', width=1200, height=800, js_api=api)
    api.window = window
    webview.start(private_mode=False)

    # Al cerrar la ventana, matamos forzadamente el proceso para que uvicorn se apague
    os._exit(0)

