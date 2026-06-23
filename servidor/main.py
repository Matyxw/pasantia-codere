"""
main.py — Servidor Central FastAPI
REST API + WebSockets + Heartbeat Scheduler
Puerto: 8000
"""

import asyncio
import concurrent.futures
import json
import os
import socket
import sys
from datetime import datetime

import requests
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

import scheduler as sched
from database import PC, Event, Metric, SessionLocal, get_db

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
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


# ──────────────────────────────────────────
# Lifecycle
# ──────────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    loop = asyncio.get_event_loop()
    sched.init(loop, manager.broadcast)
    sched.start()
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
    except Exception:
        manager.disconnect(ws)


# ──────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────
def _pc_to_dict(pc: PC) -> dict:
    last_metrics = None
    if pc.last_metrics:
        try:
            last_metrics = json.loads(pc.last_metrics)
        except Exception:
            pass
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
async def get_pcs(db: Session = Depends(get_db)):
    return [_pc_to_dict(pc) for pc in db.query(PC).all()]


@app.post("/api/pcs", status_code=201)
async def register_pc(body: dict, db: Session = Depends(get_db)):
    ip = body.get("ip", "").strip()
    name = body.get("name", "").strip()

    if not ip or not name:
        raise HTTPException(400, "IP y nombre son requeridos")

    if db.query(PC).filter(PC.ip == ip).first():
        raise HTTPException(409, f"La IP {ip} ya está registrada")

    # Intentar obtener info del agente
    hostname, os_info = None, None
    try:
        resp = requests.get(f"http://{ip}:8001/info", timeout=5)
        if resp.status_code == 200:
            info = resp.json()
            hostname = info.get("hostname")
            os_info = f"{info.get('os', '')} {info.get('os_version', '')}".strip()
    except Exception:
        pass

    pc = PC(ip=ip, name=name, hostname=hostname, os=os_info)
    db.add(pc)
    db.commit()
    db.refresh(pc)

    # Broadcast a los dashboards
    await manager.broadcast({"type": "pc_registered", "data": _pc_to_dict(pc)})

    return _pc_to_dict(pc)


@app.get("/api/pcs/{pc_id}")
async def get_pc(pc_id: int, db: Session = Depends(get_db)):
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
async def get_metrics(
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
async def get_pc_events(
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
async def get_all_events(limit: int = 100, db: Session = Depends(get_db)):
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

    try:
        resp = requests.post(
            f"http://{pc.ip}:8001/execute",
            json={"command": command},
            timeout=35,
        )
        return resp.json()
    except requests.Timeout:
        raise HTTPException(504, "Timeout: el agente no respondió en 35 segundos")
    except Exception as e:
        raise HTTPException(500, str(e))


# ──────────────────────────────────────────
# REST API — Escaneo de red
# ──────────────────────────────────────────
@app.get("/api/scan")
async def scan_network():
    """Escanea la red local en busca de agentes activos en el puerto 8001"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        raise HTTPException(500, "No se pudo obtener la IP local")

    parts = local_ip.split(".")
    prefix = f"{parts[0]}.{parts[1]}.{parts[2]}"

    def _check(ip: str):
        try:
            r = requests.get(f"http://{ip}:8001/health", timeout=1.0)
            if r.status_code == 200:
                data = r.json()
                return {
                    "ip": ip,
                    "hostname": data.get("hostname", ""),
                    "agent_version": data.get("agent_version", ""),
                    "status": "agent_active",
                }
        except Exception:
            pass
        return None

    ips = [f"{prefix}.{i}" for i in range(1, 255)]
    found = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=60) as executor:
        results = executor.map(_check, ips)
        found = [r for r in results if r is not None]

    return {
        "local_ip": local_ip,
        "network": f"{prefix}.0/24",
        "found": sorted(found, key=lambda x: x["ip"]),
        "total": len(found),
    }


# ──────────────────────────────────────────
# REST API — Export Excel
# ──────────────────────────────────────────
@app.get("/api/export/excel")
async def export_excel(db: Session = Depends(get_db)):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    wb = Workbook()

    # ── Hoja 1: PCs ──
    ws = wb.active
    ws.title = "PCs"

    headers = ["ID", "IP", "Nombre", "Hostname", "SO", "Estado", "Último visto", "Registrado"]
    ws.append(headers)

    h_fill = PatternFill(start_color="0d1b2a", end_color="0d1b2a", fill_type="solid")
    h_font = Font(bold=True, color="00ff87", size=11)
    for cell in ws[1]:
        cell.fill = h_fill
        cell.font = h_font
        cell.alignment = Alignment(horizontal="center")

    for pc in db.query(PC).all():
        ws.append([
            pc.id, pc.ip, pc.name, pc.hostname or "",
            pc.os or "", pc.status, pc.last_seen or "", pc.registered_at,
        ])

    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].auto_size = True

    # ── Hoja 2: Eventos ──
    ws2 = wb.create_sheet("Historial Eventos")
    ws2.append(["PC", "IP", "Evento", "Timestamp", "Downtime (seg)"])
    for cell in ws2[1]:
        cell.fill = h_fill
        cell.font = h_font
        cell.alignment = Alignment(horizontal="center")

    for e in db.query(Event).order_by(Event.timestamp.desc()).limit(5000).all():
        ws2.append([e.pc_name, e.pc_ip, e.type, e.timestamp, e.downtime_seconds or ""])

    # ── Hoja 3: Métricas ──
    ws3 = wb.create_sheet("Metricas")
    ws3.append(["PC_ID", "Timestamp", "CPU %", "RAM %", "Disco %", "Procesos", "Conexiones"])
    for cell in ws3[1]:
        cell.fill = h_fill
        cell.font = h_font
        cell.alignment = Alignment(horizontal="center")

    for m in db.query(Metric).order_by(Metric.timestamp.desc()).limit(10000).all():
        ws3.append([m.pc_id, m.timestamp, m.cpu_percent, m.ram_percent,
                    m.disk_percent, m.processes_count, m.network_connections])

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
async def get_stats(db: Session = Depends(get_db)):
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

        def export_excel_dialog(self):
            import webview
            from datetime import datetime
            from database import SessionLocal, PC, Event, Metric
            from openpyxl import Workbook
            from openpyxl.styles import Alignment, Font, PatternFill

            if not self.window:
                return {"error": "Ventana no cargada"}

            default_filename = f"monitor_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            result = self.window.create_file_dialog(
                webview.SAVE_DIALOG, 
                directory='', 
                save_filename=default_filename,
                file_types=('Excel Files (*.xlsx)', 'All files (*.*)')
            )
            
            if not result:
                return {"cancelled": True}
                
            filepath = result[0] if isinstance(result, tuple) else result
            
            try:
                import json
                db = SessionLocal()
                wb = Workbook()

                # ── Hoja 1: Resumen de Flota (PCs) ──
                ws = wb.active
                ws.title = "Resumen de Flota"
                
                headers = [
                    "ID", "IP", "Nombre", "Hostname", "SO", "Estado", 
                    "CPU %", "RAM Total (GB)", "RAM Uso (GB)", "RAM %",
                    "Disco %", "Temp ºC", "Conexiones", "Procesos", 
                    "Último visto", "Registrado"
                ]
                ws.append(headers)
                
                # Codere Branding Headers
                h_fill = PatternFill(start_color="7EBB28", end_color="7EBB28", fill_type="solid")
                h_font = Font(bold=True, color="FFFFFF", size=11)
                for cell in ws[1]:
                    cell.fill = h_fill
                    cell.font = h_font
                    cell.alignment = Alignment(horizontal="center", vertical="center")

                for pc in db.query(PC).all():
                    # Parsear last_metrics si existe
                    cpu, ram_tot, ram_use, ram_pct, disk_pct, temp, conns, procs = ("", "", "", "", "", "", "", "")
                    if pc.last_metrics:
                        try:
                            m = json.loads(pc.last_metrics)
                            cpu = f"{m.get('cpu', {}).get('percent', '')}%"
                            ram_tot = m.get('memory', {}).get('total_gb', '')
                            ram_use = m.get('memory', {}).get('used_gb', '')
                            ram_pct = f"{m.get('memory', {}).get('percent', '')}%"
                            
                            disks = m.get('disk', {})
                            if disks:
                                first_disk = list(disks.values())[0]
                                disk_pct = f"{first_disk.get('percent', '')}%"
                                
                            temp = m.get('temperature', {}).get('cpu_avg', '')
                            conns = m.get('network', {}).get('connections', '')
                            procs = m.get('processes', {}).get('total', '')
                        except:
                            pass
                            
                    ws.append([
                        pc.id, pc.ip, pc.name, pc.hostname or "",
                        pc.os or "", pc.status, 
                        cpu, ram_tot, ram_use, ram_pct, disk_pct, temp, conns, procs,
                        pc.last_seen or "", pc.registered_at
                    ])

                for col in ws.columns:
                    max_len = 0
                    for cell in col:
                        if cell.value:
                            max_len = max(max_len, len(str(cell.value)))
                    ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

                # ── Hoja 2: Eventos ──
                ws2 = wb.create_sheet("Historial Eventos")
                ws2.append(["PC", "IP", "Evento", "Timestamp", "Downtime (seg)"])
                for cell in ws2[1]:
                    cell.fill = h_fill
                    cell.font = h_font
                    cell.alignment = Alignment(horizontal="center")

                for e in db.query(Event).order_by(Event.timestamp.desc()).limit(5000).all():
                    ws2.append([e.pc_name, e.pc_ip, e.type, e.timestamp, e.downtime_seconds or ""])

                for col in ws2.columns:
                    ws2.column_dimensions[col[0].column_letter].width = 25

                # ── Hoja 3: Métricas Crudas ──
                ws3 = wb.create_sheet("Métricas Históricas")
                ws3.append(["PC_ID", "Timestamp", "CPU %", "RAM %", "Disco %", "Procesos", "Conexiones"])
                for cell in ws3[1]:
                    cell.fill = h_fill
                    cell.font = h_font
                    cell.alignment = Alignment(horizontal="center")

                for m in db.query(Metric).order_by(Metric.timestamp.desc()).limit(10000).all():
                    ws3.append([m.pc_id, m.timestamp, m.cpu_percent, m.ram_percent,
                                m.disk_percent, m.processes_count, m.network_connections])

                wb.save(filepath)
                db.close()
                return {"success": True, "filepath": filepath}
            except Exception as e:
                return {"error": str(e)}

    # Iniciar WebView en el hilo principal
    # Apuntamos al localhost:8000 donde corre nuestro dashboard montado en FastAPI
    api = Api()
    window = webview.create_window('Codere PC Monitor', 'http://127.0.0.1:8000', width=1200, height=800, js_api=api)
    api.window = window
    webview.start(private_mode=False)

    # Al cerrar la ventana, matamos forzadamente el proceso para que uvicorn se apague
    os._exit(0)

