#!/usr/bin/env python3
"""
INSTALADOR Y CONFIGURADOR - Crea accesos directos y configura el sistema
Ejecuta esto una sola vez para configurar todo
"""

import os
import sys
import subprocess
from pathlib import Path

def instalar_dependencias():
    """Instala las librerías necesarias"""
    print("📦 Instalando dependencias...")
    librerías = ['flask', 'psutil', 'requests', 'openpyxl', 'pandas']
    
    for lib in librerías:
        print(f"   Instalando {lib}...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', lib, '-q'])
    
    print("✅ Dependencias instaladas")

def crear_acceso_directo_windows():
    """Crea accesos directos en el escritorio de Windows"""
    print("\n📌 Creando accesos directos...")
    
    escritorio = Path.home() / "Desktop"
    ruta_script = Path(__file__).parent
    
    # Acceso directo para el cliente central
    script_cliente = ruta_script / "cliente_central.py"
    acceso_cliente = escritorio / "Monitor Central.lnk"
    
    # Script VBS para ejecutar sin consola visible (opcional)
    vbs_content = f'''Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{acceso_cliente}"
Set oLink = oWS.CreateShortLink(sLinkFile)
oLink.TargetPath = "{sys.executable}"
oLink.Arguments = "{script_cliente}"
oLink.WorkingDirectory = "{ruta_script}"
oLink.Description = "Monitor de PCs en Red"
oLink.Save'''
    
    try:
        # Método simple usando pythonw (sin ventana de consola)
        command = f'powershell -Command "\'$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut(\\\"{acceso_cliente}\\\"); $Shortcut.TargetPath = \\\"{sys.executable}\\\"; $Shortcut.Arguments = \\\"{script_cliente}\\\"; $Shortcut.WorkingDirectory = \\\"{ruta_script}\\\"; $Shortcut.IconLocation = \\\"{sys.executable}\\\"; $Shortcut.Save()\'\"'
        
        subprocess.run(command, shell=True)
        print(f"✅ Acceso directo creado: {acceso_cliente}")
    except Exception as e:
        print(f"⚠️  No se pudo crear acceso directo automáticamente: {e}")
        print(f"   Crea uno manualmente apuntando a: {script_cliente}")

def crear_batch_launcher():
    """Crea un archivo .bat para ejecutar fácilmente"""
    print("\n🚀 Creando lanzadores...")
    
    ruta_script = Path(__file__).parent
    
    # Launcher para cliente central
    cliente_bat = ruta_script / "Abrir_Monitor.bat"
    with open(cliente_bat, 'w') as f:
        f.write(f"""@echo off
title Monitor de PCs en Red
cd /d "{ruta_script}"
python cliente_central.py
pause
""")
    
    # Launcher para servidor
    servidor_bat = ruta_script / "Iniciar_Servidor.bat"
    with open(servidor_bat, 'w') as f:
        f.write(f"""@echo off
title Servidor de Monitoreo (Dejar activo)
cd /d "{ruta_script}"
python agent_servidor.py
""")
    
    print(f"✅ Lanzador de Monitor creado: {cliente_bat}")
    print(f"✅ Lanzador de Servidor creado: {servidor_bat}")

def mostrar_instrucciones():
    """Muestra instrucciones de uso"""
    print("\n" + "="*60)
    print("📖 INSTRUCCIONES DE USO")
    print("="*60)
    print("""
PASO 1: En CADA computadora que quieras monitorear:
   ✓ Ejecuta: "Iniciar_Servidor.bat" 
   ✓ O: python agent_servidor.py
   ✓ Déjalo corriendo en segundo plano

PASO 2: En la PC que será el "núcleo" de control:
   ✓ Ejecuta: "Abrir_Monitor.bat"
   ✓ O: python cliente_central.py
   ✓ Usa el menú para registrar las otras PCs por IP

PASO 3: Desde el panel de control podrás:
   ✓ Ver datos en tiempo real de cada PC
   ✓ Ejecutar comandos remotos
   ✓ Exportar a Excel
   ✓ Guardar historial

NOTA: 
   - Asegúrate que todas las PCs estén en la misma red
   - Puedes encontrar las IPs con: ipconfig (comando)
   - O desde el Panel Central (opción 3)

EJEMPLO DE IP: 192.168.1.105
""")
    print("="*60)

def main():
    print("\n" + "="*60)
    print("⚙️  INSTALADOR DEL SISTEMA DE MONITOREO")
    print("="*60)
    
    print("\n¿Qué deseas hacer?")
    print("1. Instalación completa (recomendado primera vez)")
    print("2. Solo instalar dependencias")
    print("3. Solo crear lanzadores")
    print("4. Ver instrucciones")
    
    opcion = input("\nOpción (1-4): ").strip()
    
    if opcion == "1":
        instalar_dependencias()
        crear_batch_launcher()
        crear_acceso_directo_windows()
        mostrar_instrucciones()
    elif opcion == "2":
        instalar_dependencias()
    elif opcion == "3":
        crear_batch_launcher()
    elif opcion == "4":
        mostrar_instrucciones()
    else:
        print("❌ Opción inválida")
    
    print("\n✅ ¡Listo! Puedes cerrar esta ventana.")
    input("Presiona Enter para salir...")

if __name__ == "__main__":
    main()
