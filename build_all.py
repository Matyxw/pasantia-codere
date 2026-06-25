import logging
import os
import shutil
import subprocess
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] BUILDER (PyInstaller) - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("PyInstallerBuilder")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
RELEASE_DIR = os.path.join(ROOT_DIR, "Release_v2")

def run_cmd(cmd: str) -> None:
    """Ejecuta un comando con validación estricta de éxito."""
    logger.info("Ejecutando: %s", cmd)
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.critical("Error fatal al compilar: %s", e)
        sys.exit(1)

def build() -> None:
    logger.info("=" * 60)
    logger.info(" INICIANDO EMPAQUETADO OFICIAL CON PYINSTALLER")
    logger.info("=" * 60)

    # Limpiar builds antiguos
    if os.path.exists(RELEASE_DIR):
        try:
            shutil.rmtree(RELEASE_DIR)
        except PermissionError:
            logger.critical("Permiso denegado para limpiar %s. ¿Archivos en uso?", RELEASE_DIR)
            sys.exit(1)
        except Exception as e:
            logger.error("Error imprevisto al borrar %s: %s", RELEASE_DIR, e, exc_info=True)
            sys.exit(1)

    os.makedirs(RELEASE_DIR, exist_ok=True)
    icon_path = os.path.join(ROOT_DIR, "codere_icon.ico")

    # 1. Servidor
    logger.info("\n[1/3] Compilando Servidor Central (con Dashboard incrustado)...")
    cmd_servidor = (
        f'"{sys.executable}" -m PyInstaller --noconfirm --clean --onefile --noconsole '
        f'--name "Codere_Monitor_Servidor" --icon="{icon_path}" '
        f'--hidden-import webview --hidden-import plyer.platforms.win.notification '
        f'--exclude-module PyQt5 --exclude-module tkinter '
        f'--add-data "{ROOT_DIR}/dashboard/dist;dashboard_dist" '
        f'"{ROOT_DIR}/servidor/main.py"'
    )
    run_cmd(cmd_servidor)
    shutil.copy(os.path.join(ROOT_DIR, "dist", "Codere_Monitor_Servidor.exe"), RELEASE_DIR)

    # 2. Agente
    logger.info("\n[2/3] Compilando Agente Invisible...")
    cmd_agente = (
        f'"{sys.executable}" -m PyInstaller --noconfirm --clean --onefile '
        f'--name "Codere_Agente" --noconsole --icon="{icon_path}" '
        f'--exclude-module PyQt5 --exclude-module tkinter '
        f'"{ROOT_DIR}/agente/agente.py"'
    )
    run_cmd(cmd_agente)
    shutil.copy(os.path.join(ROOT_DIR, "dist", "Codere_Agente.exe"), RELEASE_DIR)

    # 3. Exportador Excel
    logger.info("\n[3/3] Compilando Exportador Excel...")
    cmd_excel = (
        f'"{sys.executable}" -m PyInstaller --noconfirm --clean --onefile '
        f'--name "Codere_Exportar_Excel" --icon="{icon_path}" '
        f'--exclude-module PyQt5 --exclude-module tkinter '
        f'"{ROOT_DIR}/scripts/generar_excel.py"'
    )
    run_cmd(cmd_excel)
    shutil.copy(os.path.join(ROOT_DIR, "dist", "Codere_Exportar_Excel.exe"), RELEASE_DIR)

    # Limpieza final
    logger.info("Limpiando directorios temporales de PyInstaller...")
    shutil.rmtree(os.path.join(ROOT_DIR, "build"), ignore_errors=True)

    logger.info("=" * 60)
    logger.info(" COMPILACIÓN COMPLETADA CON ÉXITO")
    logger.info(" Los archivos están listos en: %s", RELEASE_DIR)
    logger.info("=" * 60)

if __name__ == "__main__":
    build()
