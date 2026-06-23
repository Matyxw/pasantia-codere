"""
notificaciones.py — Desktop notifications con plyer
Alertas nativas de Windows cuando una PC se cae o vuelve online
"""

from datetime import datetime

try:
    from plyer import notification as plyer_notify
    _PLYER_OK = True
except ImportError:
    _PLYER_OK = False


def _format_downtime(seconds: float) -> str:
    if seconds is None:
        return ""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    if mins > 0:
        return f"{mins}m {secs}s"
    return f"{secs}s"


def notify_offline(pc_name: str, ip: str):
    """Alerta cuando una PC se desconecta"""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"\033[91m[{ts}] OFFLINE: {pc_name} ({ip})\033[0m")

    if _PLYER_OK:
        try:
            plyer_notify.notify(
                title="⚠️  PC DESCONECTADA",
                message=f"{pc_name} ({ip}) se desconectó de la red",
                app_name="PC Monitor v2",
                timeout=8,
            )
        except Exception:
            pass


def notify_online(pc_name: str, ip: str, downtime_seconds: float = None):
    """Alerta cuando una PC vuelve online"""
    ts = datetime.now().strftime("%H:%M:%S")
    downtime_str = ""
    if downtime_seconds:
        downtime_str = f" (offline {_format_downtime(downtime_seconds)})"
    print(f"\033[92m[{ts}] ONLINE:  {pc_name} ({ip}){downtime_str}\033[0m")

    if _PLYER_OK:
        try:
            plyer_notify.notify(
                title="✅ PC RECONECTADA",
                message=f"{pc_name} ({ip}) volvió online{downtime_str}",
                app_name="PC Monitor v2",
                timeout=8,
            )
        except Exception:
            pass


def notify_error(message: str):
    """Notificación de error del sistema de monitoreo"""
    print(f"\033[93m[ERROR] {message}\033[0m")
