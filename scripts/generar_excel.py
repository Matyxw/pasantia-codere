import logging
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] CLI - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("GenerarExcelCLI")

def download_excel(ip: str | None = None) -> str:
    """
    Se conecta al Servidor Central (FastAPI) para descargar el archivo Excel
    generado al vuelo con los últimos datos de la flota o de una PC específica.
    """
    base_url = "http://127.0.0.1:8000/api/export/excel"
    url = f"{base_url}?ip={ip}" if ip else base_url

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status != 200:
                logger.error("Error del servidor: Código HTTP %s", response.status)
                sys.exit(1)

            content = response.read()

            os.makedirs("Reportes", exist_ok=True)
            ip_str = ip.replace('.', '_') if ip else 'Global'
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"Reportes/Reporte_Codere_{ip_str}_{timestamp}.xlsx"

            with open(filename, "wb") as f:
                f.write(content)

            return filename

    except urllib.error.URLError as e:
        logger.error(
            "Fallo conectando al Servidor Central en %s: %s\n"
            "Asegúrate de que 'Codere_Monitor_Servidor' esté corriendo y que el firewall no bloquee el puerto 8000.",
            base_url, e
        )
        sys.exit(1)
    except Exception as e:
        logger.critical("Fallo catastrófico al descargar el Excel: %s", e, exc_info=True)
        sys.exit(1)


def main() -> None:
    print("=" * 60)
    print("   GENERADOR DE REPORTES EXCEL - CODERE PC MONITOR (CLI)")
    print("=" * 60)
    print("Este programa se conectará al Servidor Central y extraerá")
    print("la telemetría arquitectónica y de hardware a un Excel de élite.")
    print("-" * 60)

    ip_target = None
    if len(sys.argv) > 1:
        ip_target = sys.argv[1].strip()
    else:
        print("\nOpciones de Reporte:")
        print(" [1] Exportar TODA LA FLOTA")
        print(" [2] Exportar una única IP")
        ans = input("\n> Seleccione una opción (1 o 2): ").strip()

        if ans == "2":
            ip_target = input("> Ingrese la IP exacta del equipo: ").strip()
            if not ip_target:
                logger.error("No se ingresó ninguna IP válida. Abortando.")
                sys.exit(1)
        elif ans != "1" and ans != "":
            logger.error("Opción inválida. Seleccione 1 o 2.")
            sys.exit(1)

    if ip_target:
        logger.info("Solicitando reporte específico para la IP: %s", ip_target)
    else:
        logger.info("Solicitando reporte Global de toda la flota...")

    output_file = download_excel(ip_target)

    logger.info("¡EXCEL GENERADO CON ÉXITO!")
    logger.info("Archivo guardado en: %s", os.path.abspath(output_file))

    # Intentar abrir la carpeta en Windows de manera segura
    if os.name == 'nt':
        try:
            os.startfile(os.path.abspath("Reportes"))
        except OSError as e:
            logger.warning("No se pudo abrir automáticamente la carpeta en el Explorador de Windows: %s", e)

    if len(sys.argv) == 1:
        print("\nPresione ENTER para salir.")
        input()


if __name__ == "__main__":
    main()
