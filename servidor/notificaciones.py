"""
notificaciones.py — Gestor de notificaciones nativas de escritorio.

Este módulo se encarga de emitir alertas nativas (Toasts en Windows) para notificar
a los operadores sobre el estado de conexión de los equipos remotos.
Se utiliza `plyer.notification` y se incorpora un sistema de logging avanzado para evitar
que excepciones internas o rechazos del sistema operativo afecten el hilo principal.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Configuración del fallback de Plyer
try:
    from plyer import notification as plyer_notify
    _PLYER_OK = True
except ImportError as e:
    _PLYER_OK = False
    logger.warning("Librería plyer no encontrada. Las notificaciones nativas estarán desactivadas. Detalle: %s", e)


def _format_downtime(seconds: float | None) -> str:
    """
    Convierte los segundos de inactividad a una cadena de tiempo legible (minutos y segundos).

    Args:
        seconds (float | None): Cantidad de segundos que el equipo estuvo offline.

    Returns:
        str: Tiempo formateado (e.g., '2m 14s') o string vacío si seconds es None.
    """
    if seconds is None:
        return ""

    mins = int(seconds // 60)
    secs = int(seconds % 60)

    if mins > 0:
        return f"{mins}m {secs}s"
    return f"{secs}s"


def notify_offline(pc_name: str, ip: str) -> None:
    """
    Alerta a través del sistema operativo local cuando un equipo remoto se desconecta.

    Se registra el evento por consola usando secuencias de escape ANSI para el color rojo,
    y se delega la tarea de renderizar un OS Toast Notification a plyer.
    
    Args:
        pc_name (str): Nombre resoluble o lógico del equipo.
        ip (str): Dirección IP v4 local del equipo que perdió conexión.
    """
    ts = datetime.now().strftime("%H:%M:%S")
    # Logueamos siempre el evento a nivel del logger, aparte de imprimirlo.
    logger.info("Equipo Offline detectado: %s (%s)", pc_name, ip)
    print(f"\033[91m[{ts}] OFFLINE: {pc_name} ({ip})\033[0m")

    from config import settings
    if not _PLYER_OK or not settings.desktop_notifications:
        return

    try:
        plyer_notify.notify(
            title="⚠️  PC DESCONECTADA",
            message=f"{pc_name} ({ip}) se desconectó de la red",
            app_name="PC Monitor v2",
            timeout=8,
        )
    except NotImplementedError:
        logger.debug("La plataforma actual no soporta notificaciones de plyer.")
    except Exception as e:
        logger.error(
            "Fallo inesperado al enviar notificación de Windows (PC DESCONECTADA: %s). "
            "Excepción: %s",
            pc_name, e, exc_info=True
        )


def notify_online(pc_name: str, ip: str, downtime_seconds: float | None = None) -> None:
    """
    Alerta a través del sistema operativo local cuando un equipo remoto vuelve a conectarse.

    Args:
        pc_name (str): Nombre resoluble o lógico del equipo.
        ip (str): Dirección IP v4 local del equipo que recuperó la conexión.
        downtime_seconds (float, opcional): Tiempo en segundos que el equipo estuvo offline.
    """
    ts = datetime.now().strftime("%H:%M:%S")
    downtime_str = ""

    if downtime_seconds is not None:
        downtime_str = f" (offline {_format_downtime(downtime_seconds)})"

    logger.info("Equipo Online detectado: %s (%s) %s", pc_name, ip, downtime_str)
    print(f"\033[92m[{ts}] ONLINE:  {pc_name} ({ip}){downtime_str}\033[0m")

    from config import settings
    if not _PLYER_OK or not settings.desktop_notifications:
        return

    try:
        plyer_notify.notify(
            title="✅  PC RECONECTADA",
            message=f"{pc_name} ({ip}) volvió a estar online{downtime_str}",
            app_name="PC Monitor v2",
            timeout=5,
        )
    except NotImplementedError:
        logger.debug("La plataforma actual no soporta notificaciones de plyer.")
    except Exception as e:
        logger.error(
            "Fallo inesperado al enviar notificación de Windows (PC RECONECTADA: %s). "
            "Excepción: %s",
            pc_name, e, exc_info=True
        )
