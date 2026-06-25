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
from contextlib import asynccontextmanager
from datetime import datetime

# Configuración del logger para el servidor
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] SERVER - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ServidorCentral")

import uvicorn  # noqa: E402
from fastapi import (  # noqa: E402
    Depends,
    FastAPI,
    HTTPException,
    Security,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        from config import settings
    except ImportError:
        from servidor.config import settings

    if credentials.credentials != settings.secret_key:
        raise HTTPException(status_code=403, detail="Invalid token")
    return credentials.credentials


try:
    import scheduler as sched
    from database import PC, Event, Metric, SessionLocal, get_db
    from generar_excel_logic import build_excel_workbook
except ImportError:
    from servidor import scheduler as sched
    from servidor.database import PC, Event, Metric, SessionLocal, get_db
    from servidor.generar_excel_logic import build_excel_workbook

try:
    from openpyxl import Workbook  # noqa: F401
    from openpyxl.styles import Alignment, Font, PatternFill  # noqa: F401
except ImportError as e:
    logger.warning("Falta openpyxl. La exportación a Excel no estará disponible: %s", e)

pending_commands = {}
command_results = {}

# ──────────────────────────────────────────
# App
# ──────────────────────────────────────────
try:
    from config import settings  # noqa: E402
except ImportError:
    from servidor.config import settings  # noqa: E402

IS_TESTING = os.environ.get("TESTING") == "1"
global_loop = None


class ConnectionManager:
    def __init__(self) -> None:
        self.active: dict[WebSocket, asyncio.Lock] = {}

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active[ws] = asyncio.Lock()

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self.active:
            del self.active[ws]

    async def broadcast(self, message: dict) -> None:
        dead = []
        # Iterar sobre una copia para evitar RuntimeError si el dict cambia
        for ws, lock in list(self.active.items()):
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(
                    "Error transmitiendo a WebSocket. Cliente desconectado abruptamente: %s", e
                )
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

manager = ConnectionManager()


def udp_discovery_server() -> None:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("", 8002))
        while True:
            data, addr = s.recvfrom(1024)
            if b"CODERE_DISCOVERY_REQUEST" in data:
                s.sendto(b"CODERE_SERVER", addr)
    except Exception as e:
        logger.error("[UDP] Error fatal en discovery server: %s", e, exc_info=True)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global global_loop
    global_loop = asyncio.get_running_loop()
    if not IS_TESTING:
        sched.init(global_loop, manager.broadcast)
        sched.start()
        threading.Thread(target=udp_discovery_server, daemon=True).start()
        print(
            f"[Server] Servidor Central iniciado en http://{settings.server_host}:{settings.server_port}"
        )
    yield
    if not IS_TESTING:
        sched.stop()


app = FastAPI(
    title="PC Monitor Central",
    version="2.0.0",
    description="Sistema de monitoreo de PCs en red — Servidor Central",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────
# WebSocket endpoint
# ──────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await manager.connect(ws)
    try:
        # Enviar estado inicial completo
        db = SessionLocal()
        pcs = db.query(PC).all()
        events = db.query(Event).order_by(Event.timestamp.desc()).limit(50).all()
        db.close()

        await ws.send_json(
            {
                "type": "initial_state",
                "data": {
                    "pcs": [_pc_to_dict(pc) for pc in pcs],
                    "events": [_event_to_dict(e) for e in events],
                },
            }
        )

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

    pc = PC(ip=ip, name=name, status="unknown", agent_id=f"manual-{uuid.uuid4().hex}")
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
def get_metrics(pc_id: int, limit: int = 60, db: Session = Depends(get_db)):
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
def get_pc_events(pc_id: int, limit: int = 100, db: Session = Depends(get_db)):
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
    rows = db.query(Event).order_by(Event.timestamp.desc()).limit(limit).all()
    return [_event_to_dict(e) for e in rows]


# ──────────────────────────────────────────
# REST API — Comandos remotos
# ──────────────────────────────────────────
@app.post("/api/pcs/{pc_id}/execute")
async def execute_command(
    pc_id: int, body: dict, db: Session = Depends(get_db), token: str = Depends(verify_token)
):
    pc = db.query(PC).filter(PC.id == pc_id).first()
    if not pc:
        raise HTTPException(404, "PC no encontrada")
    if pc.status != "online":
        raise HTTPException(503, f"La PC {pc.name} no está online")

    if not pc.agent_id:
        raise HTTPException(400, "La PC no tiene agente asociado")

    command = body.get("command", "").strip()
    if not command:
        raise HTTPException(400, "Comando vacío")

    cmd_id = str(uuid.uuid4())
    if pc.agent_id not in pending_commands:
        pending_commands[pc.agent_id] = []

    pending_commands[pc.agent_id].append({"id": cmd_id, "command": command})

    # Simular polling bloqueante (para la UI actual)
    for _ in range(60):  # 30 seg (0.5 * 60)
        if cmd_id in command_results:
            res = command_results.pop(cmd_id)
            return res
        await asyncio.sleep(0.5)

    raise HTTPException(504, "Timeout: el agente no recogió ni respondió el comando")


# ──────────────────────────────────────────
# REST API — Escaneo de red
# ──────────────────────────────────────────
@app.post("/api/agent/push")
def agent_push(body: dict, db: Session = Depends(get_db), token: str = Depends(verify_token)):
    agent_id = body.get("agent_id")
    ip = body.get("ip")
    name = body.get("name")
    hostname = body.get("hostname")
    os_info = body.get("os")
    metrics_data = body.get("metrics")

    if not agent_id or not ip or not metrics_data:
        raise HTTPException(400, "Faltan datos requeridos (agent_id, ip, metrics)")

    pc = db.query(PC).filter(PC.agent_id == agent_id).first()
    now = datetime.now().isoformat()

    went_online = False
    downtime_secs = None

    if not pc:
        # Auto-registro
        pc = PC(
            agent_id=agent_id,
            ip=ip,
            name=name,
            hostname=hostname,
            os=os_info,
            status="online",
            registered_at=now,
            last_seen=now,
        )
        db.add(pc)
        db.commit()
        db.refresh(pc)
        if global_loop:
            asyncio.run_coroutine_threadsafe(
                manager.broadcast({"type": "pc_registered", "data": _pc_to_dict(pc)}), global_loop
            )
        went_online = True
    else:
        if pc.status != "online":
            went_online = True
            if pc.last_offline:
                try:
                    last_off = datetime.fromisoformat(pc.last_offline)
                    downtime_secs = (datetime.now() - last_off).total_seconds()
                except Exception as e:
                    logger.warning(
                        "Fallo al calcular downtime_secs para %s. Detalle: %s", pc.name, e
                    )

        pc.status = "online"
        pc.last_seen = now
        pc.ip = ip
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
        event = Event(
            pc_id=pc.id,
            pc_name=pc.name,
            pc_ip=pc.ip,
            type="online",
            timestamp=now,
            downtime_seconds=downtime_secs,
        )
        db.add(event)
        try:
            from notificaciones import notify_online
        except ImportError:
            from servidor.notificaciones import notify_online

        notify_online(pc.name, pc.ip, downtime_secs)
        if global_loop:
            asyncio.run_coroutine_threadsafe(
                manager.broadcast(
                    {
                        "type": "event",
                        "data": {
                            "pc_id": pc.id,
                            "pc_name": pc.name,
                            "ip": pc.ip,
                            "event_type": "online",
                            "timestamp": now,
                        },
                    }
                ),
                global_loop,
            )
            asyncio.run_coroutine_threadsafe(
                manager.broadcast(
                    {
                        "type": "status_change",
                        "data": {"pc_id": pc.id, "ip": pc.ip, "status": "online", "timestamp": now},
                    }
                ),
                global_loop,
            )

    db.commit()

    if global_loop:
        asyncio.run_coroutine_threadsafe(
            manager.broadcast(
                {
                    "type": "metrics_update",
                    "data": {
                        "pc_id": pc.id,
                        "ip": pc.ip,
                        "name": pc.name,
                        "status": "online",
                        "last_seen": now,
                        "metrics": metrics_data,
                    },
                }
            ),
            global_loop,
        )

    # Entregar comandos pendientes
    cmds = pending_commands.pop(pc.agent_id, [])

    return {"status": "ok", "pending_commands": cmds}


@app.post("/api/agent/command_result")
def agent_command_result(body: dict, token: str = Depends(verify_token)):
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
    # Eliminado el import local porque rompía PyInstaller
    pass

    wb = build_excel_workbook(db, target_ip=ip)

    import tempfile
    filename = f"monitor_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join(tempfile.gettempdir(), filename)
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
if getattr(sys, "frozen", False):
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
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")

    print("=" * 55)
    print("  PC MONITOR v2.0 — SERVIDOR CENTRAL (GUI)")
    print("=" * 55)

    def run_server() -> None:
        try:
            from config import settings
        except ImportError:
            from servidor.config import settings

        # log_config=None para que uvicorn no busque isatty en --noconsole
        uvicorn.run(
            app,
            host=settings.server_host,
            port=settings.server_port,
            log_config=None,
            access_log=False,
        )

    # Iniciar servidor FastAPI en segundo plano
    t = threading.Thread(target=run_server, daemon=True)
    t.start()

    class Api:
        def __init__(self) -> None:
            self.window = None

        def dummy(self) -> None:
            pass

        def save_excel(self, target_ip: str | None = None) -> bool:
            import webview
            from datetime import datetime
            
            filename = f"monitor_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            result = self.window.create_file_dialog(
                webview.SAVE_DIALOG,
                directory='',
                save_filename=filename,
                file_types=('Excel Files (*.xlsx)', 'All files (*.*)')
            )
            
            if result and len(result) > 0:
                filepath = result[0]
                try:
                    from servidor.database import get_db
                    try:
                        from generar_excel_logic import build_excel_workbook
                    except ImportError:
                        from servidor.generar_excel_logic import build_excel_workbook

                    db_gen = get_db()
                    db = next(db_gen)
                    
                    wb = build_excel_workbook(db, target_ip=target_ip)
                    wb.save(filepath)
                    
                    try:
                        next(db_gen)
                    except StopIteration:
                        pass
                    return True
                except Exception as e:
                    print("Error exportando excel:", e)
            return False

    # Iniciar WebView en el hilo principal
    # Apuntamos al localhost:8000 donde corre nuestro dashboard montado en FastAPI
    api = Api()
    try:
        from config import settings
    except ImportError:
        from servidor.config import settings

    import time
    import socket
    def wait_for_server(port: int, host: str = "127.0.0.1", timeout: float = 5.0) -> None:
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with socket.create_connection((host, port), timeout=0.2):
                    return
            except OSError:
                time.sleep(0.1)
                
    # Esperamos a que uvicorn esté listo antes de levantar EdgeChromium
    # Esto evita picos de CPU simultáneos que "traban" la ventana en Windows.
    wait_for_server(settings.server_port)

    window = webview.create_window(
        "Codere PC Monitor",
        f"http://127.0.0.1:{settings.server_port}",
        width=1200,
        height=800,
        js_api=api,
    )
    api.window = window
    webview.start(private_mode=False)

    # Al cerrar la ventana, matamos forzadamente el proceso para que uvicorn se apague
    os._exit(0)
