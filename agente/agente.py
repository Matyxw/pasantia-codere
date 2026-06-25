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
import uuid
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import psutil
import requests

# Configuración de Logging de alto nivel
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] AGENTE - %(message)s",
    handlers=[logging.FileHandler("agent.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("AgentePush")

# Fix para modo --noconsole de PyInstaller/Nuitka: Evita bloqueos en stdout
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

BOOT_TIME = datetime.fromtimestamp(psutil.boot_time())
AGENT_VERSION = "3.1.0-SecurePush"

# Cargar variables desde .env si existe en el directorio del ejecutable
if getattr(sys, "frozen", False):
    _base_dir = os.path.dirname(sys.executable)
else:
    _base_dir = os.path.dirname(os.path.abspath(__file__))

_env_path = os.path.join(_base_dir, ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#"):
                _k, _, _v = _line.partition("=")
                os.environ[_k.strip()] = _v.strip().strip('"').strip("'")

# Obtener SECRET_KEY para autenticación
SECRET_KEY = os.environ.get("SECRET_KEY", "CAMBIAR_POR_CLAVE_ALEATORIA_DE_64_CARACTERES")  # noqa: S105
if SECRET_KEY == "CAMBIAR_POR_CLAVE_ALEATORIA_DE_64_CARACTERES":
    logger.warning(
        "SECRET_KEY no configurada. Usando valor por defecto INSEGURO.\n"
        "  Seteá la variable de entorno SECRET_KEY con la misma clave que el servidor."
    )

# Comandos explícitos y seguros, sin shell
ALLOWED_COMMANDS = {
    "ipconfig": ["ipconfig"],
    "systeminfo": ["systeminfo"],
    "whoami": ["whoami"],
    "hostname": ["hostname"],
    "netstat": ["netstat", "-an"],
    "tasklist": ["tasklist"],
    "ping_localhost": ["ping", "127.0.0.1"],
}


def _get_agent_id() -> str:
    """Obtiene o genera un UUID persistente para este agente."""
    id_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".agent_id")
    if os.path.exists(id_file):
        with open(id_file) as f:
            return f.read().strip()
    new_id = uuid.uuid4().hex
    try:
        with open(id_file, "w") as f:
            f.write(new_id)
    except Exception as e:
        logger.warning("No se pudo persistir el agent_id: %s", e)
    return new_id


AGENT_ID = _get_agent_id()


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
        logger.warning("No se pudo obtener el porcentaje de CPU por núcleo: %s", e, exc_info=True)
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
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round(usage.used / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "percent": usage.percent,
            }
        except PermissionError:
            logger.debug("Permiso denegado leyendo partición %s", part.device)
        except Exception as e:
            logger.debug(
                "Error accediendo a particiones de disco (%s): %s", part.device, e, exc_info=True
            )

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
        logger.error("Error al obtener estadísticas de red: %s", e, exc_info=True)
        network = {"connections": 0}

    processes: list[dict[str, Any]] = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info", "status"]):
        try:
            mem_info = p.info.get("memory_info")
            processes.append(
                {
                    "pid": p.info["pid"],
                    "name": p.info["name"],
                    "cpu_percent": p.info.get("cpu_percent", 0.0),
                    "memory_mb": round(mem_info.rss / (1024**2), 1) if mem_info else 0,
                    "status": p.info.get("status", ""),
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            logger.debug("Error esperado leyendo proceso: %s", e)
        except Exception as e:
            logger.debug("Excepción procesando PID: %s", e, exc_info=True)

    processes.sort(key=lambda x: float(x.get("cpu_percent", 0.0)), reverse=True)

    temperatures = {}
    try:
        sensors_fn = getattr(psutil, "sensors_temperatures", None)
        if sensors_fn:
            temps = sensors_fn()
            if temps:
                for name, entries in temps.items():
                    temperatures[name] = [
                        {"label": e.label, "current": e.current, "high": e.high} for e in entries
                    ]
    except Exception as e:
        logger.debug(
            "No se soportan sensores de temperatura en este hardware: %s", e, exc_info=True
        )

    users: list[dict[str, Any]] = []
    try:
        for u in psutil.users():
            users.append(
                {
                    "name": u.name,
                    "terminal": u.terminal or "",
                    "host": u.host or "",
                    "started": u.started,
                }
            )
    except psutil.AccessDenied as e:
        logger.debug("Permiso denegado listando usuarios: %s", e)
    except Exception as e:
        logger.debug("Fallo al listar usuarios activos: %s", e, exc_info=True)

    battery: dict[str, Any] | None = None
    try:
        bat_fn = getattr(psutil, "sensors_battery", None)
        if bat_fn:
            bat = bat_fn()
            if bat:
                battery = {
                    "percent": round(bat.percent, 1),
                    "secsleft": bat.secsleft,
                    "power_plugged": bat.power_plugged,
                }
    except Exception as e:
        logger.debug("Error leyendo estado de batería: %s", e, exc_info=True)

    uptime_secs = (datetime.now() - BOOT_TIME).total_seconds()

    return {
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": uptime_secs,
        "system": {"architecture": platform.architecture()[0], "processor": platform.processor()},
        "cpu": {
            "percent": cpu_percent,
            "per_core": cpu_per_core,
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "frequency_mhz": freq_mhz,
        },
        "memory": {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "percent": mem.percent,
        },
        "swap": {
            "total_gb": round(swap.total / (1024**3), 2),
            "used_gb": round(swap.used / (1024**3), 2),
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


def discover_server() -> tuple[str, int] | None:
    """
    Descubre el Servidor Central. Prioridad:
    1. SERVER_URL env var (ej: http://srv-monitor.dominio.local:8000)
    2. agent_config.json (server_host + server_port)
    3. SERVER_IP env var (solo IP, puerto default 8000)
    4. UDP Broadcast (5 intentos, 2s timeout c/u)
    5. Retorna None si nada funciona → el caller reintenta con backoff

    Returns:
        tuple[str, int] | None: (host, port) o None si no se encontró.
    """
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # ── Capa 1: SERVER_URL ──
    server_url = os.environ.get("SERVER_URL", "").strip()
    if server_url:
        try:
            parsed = urlparse(server_url)
            host = parsed.hostname or server_url
            port = parsed.port or 8000
            logger.info("[CONFIG] SERVER_URL: %s:%d", host, port)
            return host, port
        except Exception as e:
            logger.debug("SERVER_URL parse error: %s", e)

    # ── Capa 2: agent_config.json ──
    config_path = os.path.join(base_dir, "agent_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                cfg = json.load(f)
                host = cfg.get("server_host") or cfg.get("server_ip")
                port = cfg.get("server_port", 8000)
                if host:
                    logger.info("[CONFIG] agent_config.json: %s:%d", host, port)
                    return host, port
        except (json.JSONDecodeError, OSError) as e:
            logger.error("agent_config.json inválido: %s", e)

    # ── Capa 3: SERVER_IP ──
    server_ip = os.environ.get("SERVER_IP", "").strip()
    if server_ip:
        logger.info("[CONFIG] SERVER_IP: %s:8000", server_ip)
        return server_ip, 8000

    # ── Capa 4: UDP Broadcast ──
    logger.info("Broadcast UDP (puerto 8002)...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(2.0)
        for _attempt in range(5):
            try:
                s.sendto(b"CODERE_DISCOVERY_REQUEST", ("<broadcast>", 8002))
                data, addr = s.recvfrom(1024)
                if b"CODERE_SERVER" in data:
                    logger.info("Servidor encontrado en %s", addr[0])
                    s.close()
                    return addr[0], 8000
            except TimeoutError:
                pass
            except OSError:
                break
        s.close()
    except OSError as e:
        logger.debug("Broadcast no disponible: %s", e)

    return None


def try_connect(host: str, port: int) -> bool:
    """Verifica conectividad TCP + auth con el servidor."""
    try:
        resp = requests.get(
            f"http://{host}:{port}/api/stats",
            headers={"Authorization": f"Bearer {SECRET_KEY}"},
            timeout=5,
            proxies={"http": None, "https": None}
        )
        if resp.status_code == 200:
            return True
        if resp.status_code == 403:
            logger.error("SECRET_KEY rechazada por el servidor. Verificá que coincidan.")
        else:
            logger.warning("Servidor respondió HTTP %d", resp.status_code)
    except requests.exceptions.ConnectionError:
        logger.debug("Sin conexión a %s:%d", host, port)
    except requests.exceptions.Timeout:
        logger.debug("Timeout conectando a %s:%d", host, port)
    except Exception as e:
        logger.debug("Error verificando servidor: %s", e)
    return False


def execute_command(comando: str) -> dict[str, Any]:
    """
    Ejecuta un comando mapeado localmente, SIN shell=True, bloqueando inyecciones.
    """
    cmd_args = ALLOWED_COMMANDS.get(comando.strip().lower())
    if not cmd_args:
        logger.warning("Ejecución denegada por seguridad para comando: %s", comando)
        return {"error": "Comando no permitido o malformado", "command": comando}

    try:
        result = subprocess.run(  # noqa: S603
            cmd_args, capture_output=True, timeout=30, encoding="utf-8", errors="replace"
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
    Entrypoint anti-frágil. Nunca crashea.
    - Sin conectividad: reintenta descubrimiento con backoff.
    - Conexión caída: reconecta automáticamente.
    - HTTP 403: avisa de SECRET_KEY mismatch, sigue intentando.
    """
    local_ip = _get_local_ip()
    hostname = socket.gethostname()
    os_info = f"{platform.system()} {platform.release()} ({platform.architecture()[0]})"

    logger.info("=" * 50)
    logger.info(" AGENTE v%s | %s (%s)", AGENT_VERSION, hostname, local_ip)
    logger.info("=" * 50)

    server_host: str | None = None
    server_port: int = 8000
    server_url: str = ""
    backoff = 5  # segundos iniciales entre reintentos de descubrimiento

    while True:
        # ── Fase 1: Descubrir servidor ──
        if server_url and not try_connect(server_host, server_port):
            logger.warning("Servidor dejó de responder. Redescubriendo...")
            server_url = ""
            server_host = None
            backoff = 5

        if not server_url:
            result = discover_server()
            if result:
                server_host, server_port = result
                server_url = f"http://{server_host}:{server_port}"
                if try_connect(server_host, server_port):
                    logger.info("Conectado a %s", server_url)
                    backoff = 5
                else:
                    logger.warning(
                        "Servidor encontrado (%s) pero no responde. "
                        "¿Firewall? ¿Servidor caído? Reintentando en %ds...",
                        server_url,
                        backoff,
                    )
                    server_url = ""
                    server_host = None
            else:
                logger.warning(
                    "Sin servidor. Métodos probados: env, agent_config.json, UDP broadcast.\n"
                    "  Configurá: SERVER_URL=http://IP:8000 o creá agent_config.json\n"
                    "  Reintentando en %ds...",
                    backoff,
                )

            time.sleep(backoff)
            backoff = min(backoff * 2, 120)  # Backoff: 5→10→20→40→80→120s máx
            continue

        # ── Fase 2: Push loop ──
        headers = {"Authorization": f"Bearer {SECRET_KEY}"}
        try:
            payload = {
                "agent_id": AGENT_ID,
                "ip": local_ip,
                "name": hostname,
                "hostname": hostname,
                "os": os_info,
                "metrics": get_metrics(),
            }
            resp = requests.post(
                f"{server_url}/api/agent/push",
                json=payload,
                headers=headers,
                timeout=5,
                proxies={"http": None, "https": None}
            )

            if resp.status_code == 403:
                logger.error("SECRET_KEY rechazada. El servidor espera otra clave.")
                time.sleep(30)
                continue

            if resp.status_code == 200:
                data = resp.json()
                cmds = data.get("pending_commands", [])
                for cmd in cmds:
                    cmd_id = cmd["id"]
                    comando_txt = cmd["command"]
                    logger.info("Ejecutando comando: %s", comando_txt)
                    res = execute_command(comando_txt)
                    requests.post(
                        f"{server_url}/api/agent/command_result",
                        json={"agent_id": AGENT_ID, "command_id": cmd_id, "result": res},
                        headers=headers,
                        timeout=5,
                        proxies={"http": None, "https": None}
                    )
            else:
                logger.warning("HTTP %d del servidor", resp.status_code)

        except requests.exceptions.ConnectionError:
            logger.warning("Conexión perdida con %s", server_url)
            server_url = ""
            server_host = None
            backoff = 5
            continue
        except requests.exceptions.Timeout:
            logger.debug("Timeout push")
        except Exception as e:
            logger.error("Error en push: %s", e)

        time.sleep(5)


if __name__ == "__main__":
    main()
