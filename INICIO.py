#!/usr/bin/env python3
"""
GUÍA RÁPIDA - Empieza aquí
Solo 3 pasos para tener el sistema funcionando
"""

import os
import sys

def mostrar_bienvenida():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║            🖥️  SISTEMA DE MONITOREO DE PCs EN RED v1.0                  ║
║                                                                            ║
║   Monitorea múltiples computadoras conectadas en red desde un único panel  ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝

✨ CARACTERÍSTICAS:
   • Monitoreo en tiempo real (CPU, RAM, Disco)
   • Ejecución de comandos remotos
   • Almacenamiento en Excel
   • Interfaz fácil de usar

📁 ARCHIVOS DEL PROYECTO:

   agent_servidor.py      → Se instala en cada PC a monitorear
   cliente_central.py     → Panel de control (ejecutar aquí)
   scanner_red.py         → Buscar computadoras en la red
   instalar.py           → Instalador y configurador
   README.md             → Documentación completa

═══════════════════════════════════════════════════════════════════════════
""")

def mostrar_pasos():
    print("""
🚀 INSTALACIÓN EN 3 PASOS:

PASO 1️⃣  INSTALAR Y CONFIGURAR
   • Abre una terminal en esta carpeta
   • Ejecuta: python instalar.py
   • Sigue las instrucciones
   • Se instalarán automáticamente las librerías necesarias

PASO 2️⃣  ACTIVAR SERVIDORES EN CADA PC
   En cada computadora que quieras monitorear:
   
   Opción A (Recomendado):
   • Ejecuta el archivo: Iniciar_Servidor.bat
   • Deja la ventana abierta (puedes minimizarla)
   
   Opción B (Manual):
   • Abre terminal
   • Ejecuta: python agent_servidor.py
   • Verás: 🚀 Servidor iniciado en http://IP:5000

PASO 3️⃣  ABRIR PANEL CENTRAL
   En la PC que será tu "núcleo de control":
   
   Opción A (Recomendado):
   • Ejecuta el archivo: Abrir_Monitor.bat
   • O haz doble clic en el acceso del escritorio
   
   Opción B (Manual):
   • Abre terminal
   • Ejecuta: python cliente_central.py
   • Selecciona opción 1 para registrar IPs

═══════════════════════════════════════════════════════════════════════════
""")

def mostrar_opciones():
    while True:
        print("""
¿QUÉ QUIERES HACER?

1. 📦 Instalar todo (primera vez - RECOMENDADO)
2. 🔍 Buscar computadoras en la red
3. 🎯 Abrir el Panel Central
4. 🖥️  Iniciar un Servidor
5. 📖 Ver documentación completa
6. ℹ️  Ver instrucciones detalladas
7. ❌ Salir

═══════════════════════════════════════════════════════════════════════════
""")
        opcion = input("Selecciona una opción (1-7): ").strip()
        
        if opcion == "1":
            print("\n✨ Abriendo instalador...\n")
            os.system(f"{sys.executable} instalar.py")
        elif opcion == "2":
            print("\n🔍 Abriendo scanner de red...\n")
            os.system(f"{sys.executable} scanner_red.py")
        elif opcion == "3":
            print("\n🎯 Abriendo Panel Central...\n")
            os.system(f"{sys.executable} cliente_central.py")
        elif opcion == "4":
            print("\n🖥️  Abriendo Servidor...\n")
            os.system(f"{sys.executable} agent_servidor.py")
        elif opcion == "5":
            print("\n📖 Abriendo README...\n")
            try:
                import webbrowser
                webbrowser.open("file://" + os.path.abspath("README.md"))
            except:
                os.system("notepad README.md" if sys.platform == "win32" else "cat README.md")
        elif opcion == "6":
            mostrar_pasos()
        elif opcion == "7":
            print("\n👋 ¡Hasta luego!\n")
            break
        else:
            print("\n❌ Opción inválida, intenta nuevamente.\n")

def main():
    os.system("clear" if os.name == "posix" else "cls")
    mostrar_bienvenida()
    mostrar_pasos()
    print("\n✅ Ya estás listo para empezar.\n")
    mostrar_opciones()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelado")
    except Exception as e:
        print(f"\n❌ Error: {e}")
