"""
scheduler.py — APScheduler heartbeat
Verifica todas las PCs registradas cada 15 segundos.
Detecta cambios de estado (online/offline) y los broadcastea por WebSocket.
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

try:
    from database import PC, Event, Metric, Session, SessionLocal
    from notificaciones import notify_offline
except ImportError:
    from servidor.database import PC, Event, Metric, Session, SessionLocal
    from servidor.notificaciones import notify_offline

logger = logging.getLogger("scheduler")

_scheduler = BackgroundScheduler(timezone="UTC")
_broadcast_callback: Callable | None = None
_event_loop: asyncio.AbstractEventLoop | None = None

try:
    from config import settings  # noqa: E402
except ImportError:
    from servidor.config import settings  # noqa: E402

HEARTBEAT_INTERVAL = settings.heartbeat_interval  # segundos
REQUEST_TIMEOUT = settings.agent_timeout  # segundos por request al agente


def init(loop: asyncio.AbstractEventLoop, broadcast_cb: Callable) -> None:
    """Inicializa el scheduler con el event loop y el callback de broadcast"""
    global _event_loop, _broadcast_callback
    _event_loop = loop
    _broadcast_callback = broadcast_cb


def _broadcast(message: dict) -> None:
    """Envía un mensaje a todos los WebSocket clientes conectados (thread-safe)"""
    if _broadcast_callback and _event_loop:
        asyncio.run_coroutine_threadsafe(_broadcast_callback(message), _event_loop)


def _heartbeat() -> None:
    """Job principal: verifica todas las PCs registradas"""
    db = SessionLocal()
    try:
        pcs = db.query(PC).all()
        for pc in pcs:
            _check_pc(db, pc)
    except Exception as e:
        logger.error("Error crítico en la transacción de heartbeat contra BD: %s", e, exc_info=True)
    finally:
        db.close()


def _check_pc(db: Session, pc: PC) -> None:
    """Verifica el timeout de una PC usando last_seen"""
    now = datetime.now()
    try:
        last_seen = datetime.fromisoformat(pc.last_seen) if pc.last_seen else None
    except ValueError as e:
        logger.warning("Error de formato al parsear ISO date para PC %s: %s", pc.id, e)
        last_seen = None
    except Exception as e:
        logger.error("Fallo inesperado extrayendo last_seen para PC %s: %s", pc.id, e)
        last_seen = None

    is_timeout = False
    if not last_seen or (now - last_seen).total_seconds() > 20:
        is_timeout = True

    if is_timeout and pc.status != "offline":
        pc.status = "offline"
        pc.last_offline = now.isoformat()

        event = Event(
            pc_id=pc.id,
            pc_name=pc.name,
            pc_ip=pc.ip,
            type="offline",
            timestamp=now.isoformat(),
        )
        db.add(event)
        db.commit()

        notify_offline(pc.name, pc.ip)

        _broadcast(
            {
                "type": "event",
                "data": {
                    "pc_id": pc.id,
                    "pc_name": pc.name,
                    "ip": pc.ip,
                    "event_type": "offline",
                    "timestamp": now.isoformat(),
                    "downtime_seconds": None,
                },
            }
        )

        _broadcast(
            {
                "type": "status_change",
                "data": {
                    "pc_id": pc.id,
                    "name": pc.name,
                    "ip": pc.ip,
                    "status": "offline",
                    "timestamp": now.isoformat(),
                },
            }
        )


def _purge_old_metrics() -> None:
    """Job secundario: elimina métricas y eventos con más de 7 días de antigüedad (P2 - Data Retention)"""
    db = SessionLocal()
    try:
        cutoff = datetime.now() - timedelta(days=7)
        cutoff_iso = cutoff.isoformat()

        deleted_metrics = db.query(Metric).filter(Metric.timestamp < cutoff_iso).delete()
        deleted_events = db.query(Event).filter(Event.timestamp < cutoff_iso).delete()

        if deleted_metrics > 0 or deleted_events > 0:
            db.commit()
            logger.info(
                "[Scheduler] Purga completada: %s métricas, %s eventos eliminados (más antiguos de 7 días).",
                deleted_metrics,
                deleted_events,
            )
    except Exception as e:
        logger.error("Error crítico purgado datos viejos de BD: %s", e, exc_info=True)
    finally:
        db.close()


def start() -> None:
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
    _scheduler.add_job(
        _purge_old_metrics,
        "interval",
        hours=24,  # Se ejecuta una vez al día
        id="purge_metrics",
        replace_existing=True,
        max_instances=1,
    )
    logger.info(
        "[Scheduler] Heartbeat activo — verificando estado de PCs cada %ss", HEARTBEAT_INTERVAL
    )
    logger.info("[Scheduler] Data Retention activo — purgando datos de >7 días diariamente.")


def stop() -> None:
    """Detiene el scheduler"""
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
