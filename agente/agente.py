#!/usr/bin/env python3
"""
AGENTE v2.0 — FastAPI
Corre en cada PC que quieras monitorear.
Puerto: 8001
"""

import sys
import os

# Fix for --noconsole mode (sys.stdout is None)
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psutil
import socket
import platform
import subprocess
from datetime import datetime
import uvicorn

app = FastAPI(title="PC Monitor Agent", version="2.0.0", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BOOT_TIME = datetime.fromtimestamp(psutil.boot_time())

ALLOWED_COMMANDS = [
    'dir', 'tasklist', 'ipconfig', 'systeminfo',
    'whoami', 'hostname', 'netstat', 'ping', 'echo', 'type'
]


def _get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return socket.gethostbyname(socket.gethostname())


@app.get("/health")
async def health():
    """Health check — usado por el heartbeat del servidor central"""
    return {
        "status": "online",
        "hostname": socket.gethostname(),
        "timestamp": datetime.now().isoformat(),
        "agent_version": "2.0.0",
    }


@app.get("/info")
async def info():
    """Información estática del sistema (SO, procesador, arquitectura)"""
    uptime_secs = (datetime.now() - BOOT_TIME).total_seconds()
    return {
        "hostname": socket.gethostname(),
        "ip": _get_local_ip(),
        "os": platform.system(),
        "os_version": platform.release(),
        "os_edition": platform.version(),
        "architecture": platform.architecture()[0],
        "processor": platform.processor(),
        "machine": platform.machine(),
        "boot_time": BOOT_TIME.isoformat(),
        "uptime_seconds": uptime_secs,
        "python_version": platform.python_version(),
        "agent_version": "2.0.0",
    }


@app.get("/metrics")
async def metrics():
    """
    Métricas en tiempo real:
    CPU, RAM, Swap, Discos, Red, Procesos, Temperatura (si disponible)
    """
    # CPU
    cpu_percent = psutil.cpu_percent(interval=0.5)
    try:
        cpu_per_core = psutil.cpu_percent(percpu=True, interval=0)
    except Exception:
        cpu_per_core = []

    freq = psutil.cpu_freq()
    freq_mhz = round(freq.current, 1) if freq else None

    # Memoria
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    # Discos
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
        except Exception:
            pass

    # Red
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
    except Exception:
        network = {"connections": 0}

    # Procesos top CPU
    processes = []
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
        except Exception:
            pass

    processes.sort(key=lambda x: x['cpu_percent'], reverse=True)

    # Temperatura (solo disponible en algunos sistemas)
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
    except Exception:
        pass

    # Usuarios logueados
    users = []
    try:
        for u in psutil.users():
            users.append({
                "name": u.name,
                "terminal": u.terminal or "",
                "host": u.host or "",
                "started": u.started
            })
    except Exception:
        pass

    # Bateria
    battery = None
    try:
        if hasattr(psutil, 'sensors_battery'):
            bat = psutil.sensors_battery()
            if bat:
                battery = {
                    "percent": round(bat.percent, 1),
                    "secsleft": bat.secsleft,
                    "power_plugged": bat.power_plugged
                }
    except Exception:
        pass

    uptime_secs = (datetime.now() - BOOT_TIME).total_seconds()

    return {
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": uptime_secs,
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


@app.post("/execute")
async def execute(body: dict):
    """
    Ejecuta comandos remotos con lista blanca de seguridad.
    Body: {"command": "ipconfig"}
    """
    comando = body.get("command", "").strip()

    if not comando:
        return {"error": "Comando vacío"}

    allowed = any(comando.lower().startswith(cmd) for cmd in ALLOWED_COMMANDS)
    if not allowed:
        return {
            "error": "Comando no permitido",
            "allowed_commands": ALLOWED_COMMANDS,
        }

    try:
        result = subprocess.run(
            comando,
            shell=True,
            capture_output=True,
            timeout=30,
            encoding="utf-8",
            errors="replace",
        )
        return {
            "command": comando,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timestamp": datetime.now().isoformat(),
        }
    except subprocess.TimeoutExpired:
        return {"error": "Timeout: el comando tardó más de 30 segundos"}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    local_ip = _get_local_ip()
    print("=" * 50)
    print("  AGENTE PC MONITOR v2.0")
    print("=" * 50)
    print(f"  Hostname : {socket.gethostname()}")
    print(f"  IP Local : {local_ip}")
    print(f"  URL      : http://{local_ip}:8001")
    print(f"  Docs     : http://{local_ip}:8001/docs")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8001, log_config=None)
