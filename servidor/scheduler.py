"""
scheduler.py — APScheduler heartbeat
Verifica todas las PCs registradas cada 15 segundos.
Detecta cambios de estado (online/offline) y los broadcastea por WebSocket.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Callable, Optional

import requests
from apscheduler.schedulers.background import BackgroundScheduler

from database import PC, Event, Metric, SessionLocal
from notificaciones import notify_offline, notify_online

logger = logging.getLogger("scheduler")

_scheduler = BackgroundScheduler(timezone="UTC")
_broadcast_callback: Optional[Callable] = None
_event_loop: Optional[asyncio.AbstractEventLoop] = None

HEARTBEAT_INTERVAL = 15  # segundos
REQUEST_TIMEOUT = 5       # segundos por request al agente


def init(loop: asyncio.AbstractEventLoop, broadcast_cb: Callable):
    """Inicializa el scheduler con el event loop y el callback de broadcast"""
    global _event_loop, _broadcast_callback
    _event_loop = loop
    _broadcast_callback = broadcast_cb


def _broadcast(message: dict):
    """Envía un mensaje a todos los WebSocket clientes conectados (thread-safe)"""
    if _broadcast_callback and _event_loop:
        asyncio.run_coroutine_threadsafe(_broadcast_callback(message), _event_loop)


def _heartbeat():
    """Job principal: verifica todas las PCs registradas"""
    db = SessionLocal()
    try:
        pcs = db.query(PC).all()
        for pc in pcs:
            _check_pc(db, pc)
    except Exception as e:
        logger.error(f"Error en heartbeat: {e}")
    finally:
        db.close()


def _check_pc(db, pc: PC):
    """Verifica una PC individual y actualiza su estado en la DB"""
    try:
        resp = requests.get(
            f"http://{pc.ip}:8001/metrics",
            timeout=REQUEST_TIMEOUT
        )
        if resp.status_code != 200:
            raise ConnectionError("Status != 200")

        metrics_data = resp.json()
        now = datetime.now().isoformat()

        was_offline = (pc.status == "offline")
        went_online_now = was_offline or (pc.status == "unknown")

        # Calcular downtime si volvio online
        downtime_secs = None
        if was_offline and pc.last_offline:
            try:
                last_off = datetime.fromisoformat(pc.last_offline)
                downtime_secs = (datetime.now() - last_off).total_seconds()
            except Exception:
                pass

        # Actualizar PC en DB
        pc.status = "online"
        pc.last_seen = now

        # Snapshot de ultima metrica
        disk_percent = 0.0
        disk_data = metrics_data.get("disk", {})
        if disk_data:
            first_disk = next(iter(disk_data.values()), {})
            disk_percent = first_disk.get("percent", 0.0)

        pc.last_metrics = json.dumps(metrics_data)

        # Guardar snapshot en tabla metrics
        metric = Metric(
            pc_id=pc.id,
            timestamp=now,
            cpu_percent=metrics_data["cpu"]["percent"],
            ram_percent=metrics_data["memory"]["percent"],
            ram_used_gb=metrics_data["memory"]["used_gb"],
            ram_total_gb=metrics_data["memory"]["total_gb"],
            disk_percent=disk_percent,
            processes_count=metrics_data["processes"]["total"],
            network_connections=metrics_data["network"].get("connections", 0),
            uptime_seconds=metrics_data.get("uptime_seconds", 0),
        )
        db.add(metric)

        # Si volvio online, registrar evento
        if went_online_now:
            event = Event(
                pc_id=pc.id,
                pc_name=pc.name,
                pc_ip=pc.ip,
                type="online",
                timestamp=now,
                downtime_seconds=downtime_secs,
            )
            db.add(event)
            notify_online(pc.name, pc.ip, downtime_secs)

            _broadcast({
                "type": "event",
                "data": {
                    "pc_id": pc.id,
                    "pc_name": pc.name,
                    "ip": pc.ip,
                    "event_type": "online",
                    "downtime_seconds": downtime_secs,
                    "timestamp": now,
                },
            })

        db.commit()

        # Broadcast actualizacion de metricas
        _broadcast({
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

    except Exception:
        # La PC no respondio → offline
        now = datetime.now().isoformat()

        if pc.status != "offline":
            # Acaba de caerse
            pc.status = "offline"
            pc.last_offline = now

            event = Event(
                pc_id=pc.id,
                pc_name=pc.name,
                pc_ip=pc.ip,
                type="offline",
                timestamp=now,
            )
            db.add(event)
            db.commit()

            notify_offline(pc.name, pc.ip)

            _broadcast({
                "type": "event",
                "data": {
                    "pc_id": pc.id,
                    "pc_name": pc.name,
                    "ip": pc.ip,
                    "event_type": "offline",
                    "timestamp": now,
                    "downtime_seconds": None,
                },
            })

            # Broadcast status change
            _broadcast({
                "type": "status_change",
                "data": {
                    "pc_id": pc.id,
                    "name": pc.name,
                    "ip": pc.ip,
                    "status": "offline",
                    "timestamp": now,
                },
            })


def start():
    """Arranca el scheduler"""
    _scheduler.add_job(
        _heartbeat,
        "interval",
        seconds=HEARTBEAT_INTERVAL,
        id="heartbeat",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.start()
    print(f"[Scheduler] Heartbeat activo — verificando cada {HEARTBEAT_INTERVAL}s")


def stop():
    """Detiene el scheduler"""
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
