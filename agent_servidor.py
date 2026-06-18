#!/usr/bin/env python3
"""
AGENTE SERVIDOR - Corre en cada PC y expone datos del sistema
Se debe instalar en cada computadora que quieras monitorear
"""

from flask import Flask, jsonify, request
import psutil
import socket
import platform
import subprocess
import json

app = Flask(__name__)

def obtener_datos_sistema():
    """Recolecta todos los datos del sistema"""
    try:
        datos = {
            "hostname": socket.gethostname(),
            "ip": socket.gethostbyname(socket.gethostname()),
            "sistema_operativo": platform.system(),
            "version_so": platform.release(),
            "arquitectura": platform.architecture()[0],
            "procesador": platform.processor(),
            "cpu": {
                "porcentaje": psutil.cpu_percent(interval=1),
                "nucleos_fisicos": psutil.cpu_count(logical=False),
                "nucleos_logicos": psutil.cpu_count(logical=True),
            },
            "memoria": {
                "total_gb": psutil.virtual_memory().total / (1024**3),
                "usada_gb": psutil.virtual_memory().used / (1024**3),
                "disponible_gb": psutil.virtual_memory().available / (1024**3),
                "porcentaje": psutil.virtual_memory().percent,
            },
            "disco": {},
            "procesos": {
                "total": len(psutil.pids()),
                "procesos_activos": [
                    {
                        "pid": p.pid,
                        "nombre": p.name(),
                        "cpu_percent": p.cpu_percent(),
                        "memoria_mb": p.memory_info().rss / (1024**2)
                    }
                    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info'])[:10]
                ]
            },
            "red": {
                "conexiones_activas": len(psutil.net_connections())
            }
        }
        
        # Información de discos
        for disco in psutil.disk_partitions():
            try:
                uso = psutil.disk_usage(disco.mountpoint)
                datos["disco"][disco.device] = {
                    "total_gb": uso.total / (1024**3),
                    "usado_gb": uso.used / (1024**3),
                    "libre_gb": uso.free / (1024**3),
                    "porcentaje": uso.percent
                }
            except:
                pass
        
        return datos
    except Exception as e:
        return {"error": str(e)}

@app.route('/datos', methods=['GET'])
def datos_sistema():
    """Endpoint para obtener datos del sistema"""
    return jsonify(obtener_datos_sistema())

@app.route('/ejecutar', methods=['POST'])
def ejecutar_comando():
    """Endpoint para ejecutar comandos (con seguridad básica)"""
    try:
        datos = request.json
        comando = datos.get('comando', '')
        
        # Lista blanca de comandos permitidos
        comandos_permitidos = ['dir', 'tasklist', 'ipconfig', 'systeminfo', 'taskkill', 'shutdown']
        
        if not any(cmd in comando.lower() for cmd in comandos_permitidos):
            return jsonify({"error": "Comando no permitido"}), 403
        
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True)
        return jsonify({
            "exit_code": resultado.returncode,
            "salida": resultado.stdout,
            "error": resultado.stderr
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/salud', methods=['GET'])
def salud():
    """Endpoint para verificar que el servidor está activo"""
    return jsonify({"estado": "activo", "hostname": socket.gethostname()})

if __name__ == '__main__':
    print("🚀 Servidor de Agente iniciado")
    print(f"📍 Escuchando en http://{socket.gethostbyname(socket.gethostname())}:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
