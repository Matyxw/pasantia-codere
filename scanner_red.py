#!/usr/bin/env python3
"""
SCANNER DE RED - Encuentra todas las IPs activas en la red local
Útil para descubrir computadoras para monitorear
"""

import subprocess
import socket
import ipaddress
import platform
import sys
from pathlib import Path

def obtener_ip_local():
    """Obtiene la IP local de esta computadora"""
    try:
        # Conecta a un servidor externo (sin enviar datos) para obtener la IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def obtener_rango_red():
    """Obtiene el rango de red basado en la IP local"""
    ip_local = obtener_ip_local()
    partes = ip_local.split('.')
    # Asume red /24 (clase C típica)
    rango = f"{partes[0]}.{partes[1]}.{partes[2]}.0/24"
    return rango, ip_local

def ping_host(ip):
    """Verifica si un host responde al ping"""
    try:
        # Parámetro diferente según el SO
        param = "-n" if platform.system().lower() == "windows" else "-c"
        resultado = subprocess.run(
            ["ping", param, "1", str(ip)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2
        )
        return resultado.returncode == 0
    except:
        return False

def obtener_hostname(ip):
    """Intenta obtener el nombre de host de una IP"""
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        return hostname
    except:
        return "Desconocido"

def verificar_servidor_monitoreo(ip):
    """Verifica si hay un servidor de monitoreo corriendo en la IP"""
    try:
        import requests
        respuesta = requests.get(f"http://{ip}:5000/salud", timeout=1)
        return respuesta.status_code == 200
    except:
        return False

def escanear_red():
    """Escanea la red y encuentra hosts activos"""
    print("\n" + "="*60)
    print("🔍 SCANNER DE RED - BÚSQUEDA DE COMPUTADORAS")
    print("="*60)
    
    rango, ip_local = obtener_range_red()
    print(f"\n📍 Tu IP local: {ip_local}")
    print(f"🌐 Rango de red: {rango}")
    print(f"\n⏳ Escaneando red (esto puede tomar 1-2 minutos)...\n")
    
    hosts_activos = []
    
    try:
        # Crea un objeto de red
        red = ipaddress.ip_network(rango, strict=False)
        total_ips = len(list(red.hosts()))
        procesados = 0
        
        for ip in red.hosts():
            ip_str = str(ip)
            procesados += 1
            
            # Muestra progreso cada 10 IPs
            if procesados % 10 == 0:
                print(f"Progreso: {procesados}/{total_ips} IPs verificadas...", end='\r')
            
            if ping_host(ip_str):
                hostname = obtener_hostname(ip_str)
                servidor = "✅" if verificar_servidor_monitoreo(ip_str) else "❌"
                hosts_activos.append({
                    'ip': ip_str,
                    'hostname': hostname,
                    'servidor': servidor
                })
        
        print(f"\nProgreso: {total_ips}/{total_ips} IPs verificadas.\n")
        
    except Exception as e:
        print(f"❌ Error en escaneo: {e}")
        return
    
    # Muestra resultados
    if hosts_activos:
        print("="*60)
        print(f"✅ Se encontraron {len(hosts_activos)} computadoras activas:")
        print("="*60)
        print(f"{'IP':<18} {'HOSTNAME':<20} {'SERVIDOR':<10}")
        print("-"*60)
        
        for host in sorted(hosts_activos, key=lambda x: x['ip']):
            print(f"{host['ip']:<18} {host['hostname']:<20} {host['servidor']:<10}")
        
        print("="*60)
        print("\n✅ = Servidor de monitoreo activo")
        print("❌ = Sin servidor de monitoreo (debe iniciarse)")
        
        # Opción para guardar
        guardar = input("\n¿Guardar lista en archivo? (s/n): ").lower() == 's'
        if guardar:
            with open("hosts_encontrados.txt", "w") as f:
                f.write("COMPUTADORAS ENCONTRADAS EN LA RED\n")
                f.write("="*60 + "\n\n")
                for host in sorted(hosts_activos, key=lambda x: x['ip']):
                    f.write(f"IP: {host['ip']}\n")
                    f.write(f"Hostname: {host['hostname']}\n")
                    f.write(f"Servidor: {host['servidor']}\n\n")
            print("✅ Guardado en: hosts_encontrados.txt")
        
        # Copiar IPs al portapapeles
        copiar = input("\n¿Copiar IPs al portapapeles? (s/n): ").lower() == 's'
        if copiar:
            try:
                import pyperclip
                ips = '\n'.join([h['ip'] for h in hosts_activos])
                pyperclip.copy(ips)
                print("✅ IPs copiadas al portapapeles")
            except:
                print("⚠️  Instala pyperclip: pip install pyperclip")
    else:
        print("❌ No se encontraron computadoras activas en la red")
        print("   Verifica que haya otras computadoras conectadas")
        print("   Comprueba tu conexión de red")

def menu_rapido():
    """Menú para búsqueda rápida de un IP específico"""
    print("\n" + "="*60)
    print("🔍 VERIFICADOR DE IP")
    print("="*60)
    
    ip = input("\nIngresa una IP para verificar (ejemplo: 192.168.1.105): ").strip()
    
    print(f"\n⏳ Verificando {ip}...")
    
    if ping_host(ip):
        print(f"✅ El host {ip} está activo")
        hostname = obtener_hostname(ip)
        print(f"   Hostname: {hostname}")
        
        if verificar_servidor_monitoreo(ip):
            print(f"   ✅ Servidor de monitoreo ACTIVO")
        else:
            print(f"   ❌ Sin servidor de monitoreo")
    else:
        print(f"❌ El host {ip} no responde")

def main():
    print("\n" + "="*60)
    print("🖥️  HERRAMIENTA DE BÚSQUEDA DE COMPUTADORAS")
    print("="*60)
    print("\n¿Qué deseas hacer?")
    print("1. Escanear toda la red (LENTO - 1-2 min)")
    print("2. Verificar una IP específica (RÁPIDO)")
    print("3. Ver mi IP local")
    print("4. Salir")
    
    opcion = input("\nOpción (1-4): ").strip()
    
    if opcion == "1":
        escanear_red()
    elif opcion == "2":
        menu_rapido()
    elif opcion == "3":
        ip_local = obtener_ip_local()
        print(f"\n🖥️  Tu IP local: {ip_local}")
        print(f"    (Usa esta dirección en otras computadoras)")
    elif opcion == "4":
        print("\n👋 Hasta luego!")
    else:
        print("\n❌ Opción inválida")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelado por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
