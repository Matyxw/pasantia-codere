#!/usr/bin/env python3
"""
VERIFICADOR DE SISTEMA - Comprueba que todo está instalado correctamente
Ejecuta antes de empezar a usar el sistema
"""

import sys
import subprocess
import socket
import platform

class Verificador:
    def __init__(self):
        self.errores = []
        self.advertencias = []
        self.exito = []
    
    def verificar_python(self):
        """Verifica versión de Python"""
        version = sys.version_info
        if version.major >= 3 and version.minor >= 7:
            self.exito.append(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        else:
            self.errores.append(f"❌ Python {version.major}.{version.minor} - Se requiere 3.7+")
    
    def verificar_libreria(self, nombre_paquete, nombre_import=None):
        """Verifica si una librería está instalada"""
        if nombre_import is None:
            nombre_import = nombre_paquete
        
        try:
            __import__(nombre_import)
            self.exito.append(f"✅ {nombre_paquete}")
        except ImportError:
            self.errores.append(f"❌ {nombre_paquete} - No instalado")
    
    def verificar_librerias(self):
        """Verifica todas las librerías necesarias"""
        print("\n📦 Verificando librerías...")
        
        librerias = [
            ("flask", "flask"),
            ("psutil", "psutil"),
            ("requests", "requests"),
            ("openpyxl", "openpyxl"),
            ("pandas", "pandas"),
        ]
        
        for paquete, import_name in librerias:
            self.verificar_libreria(paquete, import_name)
    
    def verificar_red(self):
        """Verifica conectividad de red"""
        print("\n🌐 Verificando red...")
        
        try:
            ip_local = socket.gethostbyname(socket.gethostname())
            self.exito.append(f"✅ IP local: {ip_local}")
            
            # Intenta conectarse a Google DNS
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            self.exito.append("✅ Conectividad a Internet")
        except:
            self.advertencias.append("⚠️  Conexión a Internet - Puede no ser crítico")
    
    def verificar_puerto(self, puerto=5000):
        """Verifica si el puerto está disponible"""
        print(f"\n🔌 Verificando puerto {puerto}...")
        
        try:
            socket.socket().bind(("0.0.0.0", puerto))
            self.exito.append(f"✅ Puerto {puerto} disponible")
        except OSError:
            self.errores.append(f"❌ Puerto {puerto} ocupado")
    
    def verificar_archivos(self):
        """Verifica que existan los archivos principales"""
        print("\n📁 Verificando archivos...")
        
        import os
        archivos = [
            "agent_servidor.py",
            "cliente_central.py",
            "scanner_red.py",
            "instalar.py",
            "INICIO.py",
            "README.md"
        ]
        
        for archivo in archivos:
            if os.path.exists(archivo):
                self.exito.append(f"✅ {archivo}")
            else:
                self.advertencias.append(f"⚠️  {archivo} - No encontrado")
    
    def verificar_so(self):
        """Verifica el sistema operativo"""
        print("\n💻 Sistema Operativo...")
        
        so = platform.system()
        version = platform.release()
        self.exito.append(f"✅ {so} {version}")
    
    def instalar_librerias_faltantes(self):
        """Instala librerías que falten"""
        print("\n⚙️  Intentando instalar librerías faltantes...")
        
        librerias = ['flask', 'psutil', 'requests', 'openpyxl', 'pandas']
        
        for lib in librerias:
            try:
                __import__(lib.replace('-', '_'))
            except ImportError:
                print(f"   Instalando {lib}...")
                try:
                    subprocess.run(
                        [sys.executable, '-m', 'pip', 'install', lib, '-q'],
                        timeout=60
                    )
                    self.exito.append(f"✅ {lib} instalado")
                except:
                    self.errores.append(f"❌ Error instalando {lib}")
    
    def mostrar_resultados(self):
        """Muestra los resultados de todas las verificaciones"""
        print("\n" + "="*60)
        print("📊 RESULTADO DE VERIFICACIÓN")
        print("="*60)
        
        if self.exito:
            print("\n✅ VERIFICACIONES EXITOSAS:")
            for msg in self.exito:
                print(f"   {msg}")
        
        if self.advertencias:
            print("\n⚠️  ADVERTENCIAS:")
            for msg in self.advertencias:
                print(f"   {msg}")
        
        if self.errores:
            print("\n❌ ERRORES:")
            for msg in self.errores:
                print(f"   {msg}")
        
        print("\n" + "="*60)
        
        if not self.errores:
            print("✅ ¡TODO ESTÁ LISTO!")
            print("\nPuedes empezar ejecutando:")
            print("   python INICIO.py")
            print("   O: python cliente_central.py")
            return True
        else:
            print("❌ HAY PROBLEMAS QUE SOLUCIONAR")
            print("\nIntenta ejecutar: python instalar.py")
            return False
    
    def ejecutar_verificacion_completa(self):
        """Ejecuta todas las verificaciones"""
        print("\n" + "="*60)
        print("🔍 VERIFICACIÓN DEL SISTEMA")
        print("="*60)
        
        self.verificar_python()
        self.verificar_so()
        self.verificar_librerias()
        self.verificar_red()
        self.verificar_puerto()
        self.verificar_archivos()
        
        resultado = self.mostrar_resultados()
        return resultado

def main():
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║                   VERIFICADOR DE SISTEMA                              ║
║          Comprueba que todo está instalado correctamente              ║
╚════════════════════════════════════════════════════════════════════════╝
""")
    
    print("¿Qué deseas hacer?")
    print("1. Verificación completa")
    print("2. Instalar librerías faltantes")
    print("3. Solo mostrar información del sistema")
    print("4. Verificar puerto 5000")
    print("5. Salir")
    
    opcion = input("\nOpción (1-5): ").strip()
    
    verificador = Verificador()
    
    if opcion == "1":
        verificador.ejecutar_verificacion_completa()
    elif opcion == "2":
        verificador.instalar_librerias_faltantes()
        print("\n✅ Instalación completada")
    elif opcion == "3":
        verificador.verificar_python()
        verificador.verificar_so()
        print("\nPython:")
        for msg in verificador.exito:
            print(f"   {msg}")
    elif opcion == "4":
        verificador.verificar_puerto(5000)
        print(f"\n{verificador.exito[0] if verificador.exito else verificador.errores[0]}")
    elif opcion == "5":
        print("\n👋 Hasta luego")
    else:
        print("❌ Opción inválida")
    
    input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelado")
    except Exception as e:
        print(f"\n❌ Error: {e}")
