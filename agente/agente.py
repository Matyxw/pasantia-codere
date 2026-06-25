#!/usr/bin/env python3
"""
AGENTE v3.0 — Arquitectura Push + UDP Discovery
Corre en cada PC remota que se requiera monitorear.

Responsabilidades Clave:
1. Recolectar métricas profundas de hardware y software vía `psutil`.
2. Descubrir al servidor maestro vía broadcast UDP en entornos corporativos complejos.
3. Hacer envíos Push constantes (cada 5s) del estado actual y ejecutar comandos aprobados.

Este módulo aplica logging estructurado, tipado fuerte y manejo granular de errores para asegurar
que ninguna caída del módulo o problema de acceso WMI bloquee el ciclo de reporte.
"""

import json
import logging
import os
import platform
import socket
import subprocess
import sys
import time
from datetime import datetime
from typing import Any

import psutil
import requests

# Configuración de Logging de alto nivel
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("AgentePush")

# Fix para modo --noconsole de PyInstaller/Nuitka: Evita bloqueos en stdout
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

BOOT_TIME = datetime.fromtimestamp(psutil.boot_time())
AGENT_VERSION = "3.0.0-Push"

ALLOWED_COMMANDS = [
    'dir', 'tasklist', 'ipconfig', 'systeminfo',
    'whoami', 'hostname', 'netstat', 'ping', 'echo', 'type'
]


def _get_local_ip() -> str:
    """
    Obtiene la dirección IPv4 local que el Agente utiliza para salida a Internet.
    Se conecta a un DNS público de manera pasiva para determinar la interfaz de red correcta.
    
    Returns:
        str: Dirección IP local en formato string. En caso de no tener salida, devuelve la del hostname.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError as e:
        logger.warning("Fallo al obtener IP vía socket UDP externo. Detalle: %s", e)
        return socket.gethostbyname(socket.gethostname())
    except Exception as e:
        logger.error("Error inesperado en _get_local_ip: %s", e, exc_info=True)
        return "127.0.0.1"


def get_metrics() -> dict[str, Any]:
    """
    Recolecta y estructura métricas de sistema críticas (CPU, RAM, Discos, Red, Procesos, Batería).
    Captura excepciones específicas en fallos de ACLs (AccessDenied) o procesos zombis.

    Returns:
        dict: Dicionario jerárquico conteniendo toda la telemetría del equipo.
    """
    cpu_percent = psutil.cpu_percent(interval=0.5)

    try:
        cpu_per_core = psutil.cpu_percent(percpu=True, interval=0)
    except Exception as e:
        logger.warning("No se pudo obtener el porcentaje de CPU por núcleo: %s", e)
        cpu_per_core = []

    freq = psutil.cpu_freq()
    freq_mhz = round(freq.current, 1) if freq else None

    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    disks = {}
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks[part.device] = {
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total_gb": round(usage.total / (1024 ** 3), 2),
                "used_gb": round(usage.used / (1024 ** 3), 2),
                "free_gb": round(usage.free / (1024 ** 3), 2),
                "percent": usage.percent,
            }
        except PermissionError:
            logger.debug("Permiso denegado al leer la partición: %s", part.mountpoint)
        except Exception as e:
            logger.debug("Error leyendo disco %s: %s", part.device, e)

    try:
        net_io = psutil.net_io_counters()
        net_connections = len(psutil.net_connections())
        network = {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
            "connections": net_connections,
        }
    except psutil.AccessDenied:
        logger.debug("Permiso denegado para leer contadores de red avanzados.")
        network = {"connections": 0}
    except Exception as e:
        logger.error("Error al obtener red: %s", e)
        network = {"connections": 0}

    processes: list[dict[str, Any]] = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status']):
        try:
            mem_info = p.info.get('memory_info')
            processes.append({
                "pid": p.info['pid'],
                "name": p.info['name'],
                "cpu_percent": p.info.get('cpu_percent', 0.0),
                "memory_mb": round(mem_info.rss / (1024 ** 2), 1) if mem_info else 0,
                "status": p.info.get('status', ''),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
        except Exception as e:
            logger.debug("Excepción procesando PID: %s", e)

    processes.sort(key=lambda x: float(x.get('cpu_percent', 0.0)), reverse=True)

    temperatures = {}
    try:
        if hasattr(psutil, 'sensors_temperatures'):
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    temperatures[name] = [
                        {"label": e.label, "current": e.current, "high": e.high}
                        for e in entries
                    ]
    except Exception as e:
        logger.debug("No se soportan sensores de temperatura en este hardware: %s", e)

    users: list[dict[str, Any]] = []
    try:
        for u in psutil.users():
            users.append({
                "name": u.name,
                "terminal": u.terminal or "",
                "host": u.host or "",
                "started": u.started
            })
    except Exception as e:
        logger.debug("No se pudo obtener información de usuarios activos: %s", e)

    battery: dict[str, Any] | None = None
    try:
        if hasattr(psutil, 'sensors_battery'):
            bat = psutil.sensors_battery()
            if bat:
                battery = {
                    "percent": round(bat.percent, 1),
                    "secsleft": bat.secsleft,
                    "power_plugged": bat.power_plugged
                }
    except Exception as e:
        logger.debug("Error leyendo estado de batería: %s", e)

    uptime_secs = (datetime.now() - BOOT_TIME).total_seconds()

    return {
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": uptime_secs,
        "system": {
            "architecture": platform.architecture()[0],
            "processor": platform.processor()
        },
        "cpu": {
            "percent": cpu_percent,
            "per_core": cpu_per_core,
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "frequency_mhz": freq_mhz,
        },
        "memory": {
            "total_gb": round(mem.total / (1024 ** 3), 2),
            "used_gb": round(mem.used / (1024 ** 3), 2),
            "available_gb": round(mem.available / (1024 ** 3), 2),
            "percent": mem.percent,
        },
        "swap": {
            "total_gb": round(swap.total / (1024 ** 3), 2),
            "used_gb": round(swap.used / (1024 ** 3), 2),
            "percent": swap.percent,
        },
        "disk": disks,
        "network": network,
        "processes": {
            "total": len(psutil.pids()),
            "top_cpu": processes[:10],
        },
        "temperatures": temperatures,
        "users": users,
        "battery": battery,
    }


def discover_server() -> str:
    """
    Descubre de manera robusta la dirección IP del Servidor Central.
    Primero busca un override local ('agent_config.json') para entornos Enterprise donde
    los bridges LAN/WiFi no soportan Broadcast.
    Como fallback, envía mensajes UDP Broadcast.
    
    Returns:
        str: IP válida del Servidor Central.
    """
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    config_path = os.path.join(base_dir, "agent_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                cfg = json.load(f)
                if "server_ip" in cfg:
                    logger.info("Override empresarial detectado. Usando IP fijada en agent_config.json: %s", cfg["server_ip"])
                    return cfg["server_ip"]
        except json.JSONDecodeError as e:
            logger.error("agent_config.json corrupto. Ignorando override. Detalle: %s", e)
        except Exception as e:
            logger.error("Error al leer agent_config.json: %s", e)

    logger.info("Buscando servidor Codere en la red vía UDP Broadcast (puerto 8002)...")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.settimeout(2.0)

    while True:
        try:
            s.sendto(b"CODERE_DISCOVERY_REQUEST", ('<broadcast>', 8002))
            data, addr = s.recvfrom(1024)
            if b"CODERE_SERVER" in data:
                logger.info("¡Servidor encontrado en %s!", addr[0])
                s.close()
                return addr[0]
        except TimeoutError:
            logger.debug("Timeout de UDP Broadcast, reintentando...")
        except Exception as e:
            logger.error("Error intermitente en socket UDP: %s", e)
        time.sleep(2)


def execute_command(comando: str) -> dict[str, Any]:
    """
    Ejecuta un comando en la shell del equipo local, asegurando validación de la Whitelist.
    
    Args:
        comando (str): El comando de shell solicitado desde el dashboard.

    Returns:
        Dict: Metadatos de ejecución incluyendo return_code, stdout o error de permisos.
    """
    allowed = any(comando.lower().startswith(cmd) for cmd in ALLOWED_COMMANDS)
    if not allowed:
        logger.warning("Ejecución denegada por seguridad para comando: %s", comando)
        return {"error": "Comando no permitido", "command": comando}

    try:
        result = subprocess.run(
            comando, shell=True, capture_output=True, timeout=30,
            encoding="utf-8", errors="replace"
        )
        logger.info("Comando '%s' ejecutado exitosamente con código %d", comando, result.returncode)
        return {
            "command": comando,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timestamp": datetime.now().isoformat(),
        }
    except subprocess.TimeoutExpired:
        logger.error("El comando '%s' excedió el timeout de 30s.", comando)
        return {"error": "Timeout excedido (30s)", "command": comando}
    except Exception as e:
        logger.error("Error crítico ejecutando '%s': %s", comando, e, exc_info=True)
        return {"error": str(e), "command": comando}


def main() -> None:
    """
    Entrypoint principal. Despliega el ciclo infinito de recolección y Push de estado.
    Captura y mitiga interrupciones de red sin crashear el subproceso.
    """
    local_ip = _get_local_ip()
    hostname = socket.gethostname()
    os_info = f"{platform.system()} {platform.release()} ({platform.architecture()[0]})"

    logger.info("=" * 50)
    logger.info(" AGENTE PUSH CODERE v3.0 (God Mode / Apex Architecture)")
    logger.info(" Iniciando en: %s (%s)", hostname, local_ip)
    logger.info("=" * 50)

    server_ip = discover_server()
    server_url = f"http://{server_ip}:8000"

    # Bucle core de Push
    while True:
        try:
            payload = {
                "ip": local_ip,
                "name": hostname,
                "hostname": hostname,
                "os": os_info,
                "metrics": get_metrics()
            }
            resp = requests.post(f"{server_url}/api/agent/push", json=payload, timeout=5)

            if resp.status_code == 200:
                data = resp.json()
                cmds = data.get("pending_commands", [])
                for cmd in cmds:
                    cmd_id = cmd["id"]
                    comando_txt = cmd["command"]
                    logger.info("Comando remoto recibido (ID: %s): %s", cmd_id, comando_txt)

                    res = execute_command(comando_txt)

                    requests.post(f"{server_url}/api/agent/command_result", json={
                        "pc_ip": local_ip,
                        "command_id": cmd_id,
                        "result": res
                    }, timeout=5)

        except requests.exceptions.ConnectionError:
            logger.error("Conexión perdida con el Servidor Central (%s). Reintentando en 5s...", server_url)
        except requests.exceptions.Timeout:
            logger.warning("Timeout al enviar métricas. Posible saturación de red o servidor ocupado.")
        except Exception as e:
            logger.critical("Fallo catastrófico en el loop principal del Agente: %s", e, exc_info=True)

        time.sleep(5)


if __name__ == "__main__":
    main()
