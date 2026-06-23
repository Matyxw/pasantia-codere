import os
import sys
import urllib.error
import urllib.request
from datetime import datetime


def download_excel(ip: str | None = None) -> str:
    # URL de nuestro servidor central
    base_url = "http://127.0.0.1:8000/api/export/excel"
    url = f"{base_url}?ip={ip}" if ip else base_url

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status != 200:
                print(f"\n[X] Error del servidor: Código {response.status}")
                sys.exit(1)

            content = response.read()

            os.makedirs("Reportes", exist_ok=True)
            filename = f"Reportes/Reporte_IP_{ip.replace('.', '_') if ip else 'Global'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

            with open(filename, "wb") as f:
                f.write(content)

            return filename

    except urllib.error.URLError as e:
        print(f"\n[X] Error conectando al Servidor Central: {e}")
        print("Asegurate de que Codere_Monitor_Servidor esté en ejecución.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[X] Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("   GENERADOR DE REPORTES EXCEL - CODERE PC MONITOR (CLI)")
    print("=" * 60)
    print("Este programa se conectará al Servidor Central")
    print("y extraerá los datos a un archivo Excel.")
    print("-" * 60)

    ip_target = None
    if len(sys.argv) > 1:
        ip_target = sys.argv[1].strip()
    else:
        ans = input("\n> Ingrese la IP de la computadora (Deje en blanco para TODA la flota): ").strip()
        if ans:
            ip_target = ans

    if ip_target:
        print(f"\n[~] Solicitando reporte de {ip_target} al Servidor...")
    else:
        print("\n[~] Solicitando reporte de TODA LA FLOTA al Servidor...")

    output_file = download_excel(ip_target)

    print("\n[OK] ¡EXCEL GENERADO CON ÉXITO!")
    print(f"Archivo guardado en: {os.path.abspath(output_file)}")

    # Intentar abrir la carpeta en Windows
    try:
        if os.name == 'nt':
            os.startfile(os.path.abspath("Reportes"))
    except Exception:
        pass

    if len(sys.argv) == 1:
        print("\nPresione ENTER para salir.")
        input()
