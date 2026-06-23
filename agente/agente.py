#!/usr/bin/env python3
"""
AGENTE v3.0 — Arquitectura Push + UDP Discovery
Corre en cada PC que quieras monitorear.
"""

import json
import os
import platform
import socket
import subprocess
import sys
import time
from datetime import datetime

import psutil
import requests

# Fix for --noconsole mode
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
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return socket.gethostbyname(socket.gethostname())

def get_metrics():
    cpu_percent = psutil.cpu_percent(interval=0.5)
    try:
        cpu_per_core = psutil.cpu_percent(percpu=True, interval=0)
    except:
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
        except:
            pass

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
    except:
        network = {"connections": 0}

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
        except:
            pass
    processes.sort(key=lambda x: x['cpu_percent'], reverse=True)

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
    except:
        pass

    users = []
    try:
        for u in psutil.users():
            users.append({
                "name": u.name,
                "terminal": u.terminal or "",
                "host": u.host or "",
                "started": u.started
            })
    except:
        pass

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
    except:
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

def discover_server():
    # 1. Fallback de archivo de configuración (Enterprise Override)
    # Permite fijar la IP si el router bloquea el UDP Broadcast (LAN vs WiFi)
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
                    return cfg["server_ip"]
        except Exception:
            pass

    print("[UDP] Buscando servidor Codere en la red...")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.settimeout(2.0)

    while True:
        try:
            # Enviamos broadcast al puerto 8002
            s.sendto(b"CODERE_DISCOVERY_REQUEST", ('<broadcast>', 8002))
            data, addr = s.recvfrom(1024)
            if b"CODERE_SERVER" in data:
                print(f"[UDP] ¡Servidor encontrado en {addr[0]}!")
                s.close()
                return addr[0]
        except Exception:
            pass
        time.sleep(2)

def execute_command(comando: str):
    allowed = any(comando.lower().startswith(cmd) for cmd in ALLOWED_COMMANDS)
    if not allowed:
        return {"error": "Comando no permitido", "command": comando}

    try:
        result = subprocess.run(
            comando, shell=True, capture_output=True, timeout=30,
            encoding="utf-8", errors="replace"
        )
        return {
            "command": comando,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "command": comando}

def main():
    local_ip = _get_local_ip()
    hostname = socket.gethostname()
    os_info = f"{platform.system()} {platform.release()} ({platform.architecture()[0]})"

    print("=" * 50)
    print("  AGENTE PUSH CODERE v3.0")
    print("=" * 50)

    server_ip = discover_server()
    server_url = f"http://{server_ip}:8000"

    # Loop principal
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
                    res = execute_command(comando_txt)

                    # Enviar resultado de vuelta
                    requests.post(f"{server_url}/api/agent/command_result", json={
                        "pc_ip": local_ip,
                        "command_id": cmd_id,
                        "result": res
                    }, timeout=5)

        except Exception as e:
            print(f"[ERROR] No se pudo enviar metrics: {e}")

        time.sleep(5)

if __name__ == "__main__":
    main()
