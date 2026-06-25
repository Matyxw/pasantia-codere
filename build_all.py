import logging
import os
import shutil
import subprocess
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] BUILDER (PyInstaller) - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("PyInstallerBuilder")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
RELEASE_DIR = os.path.join(ROOT_DIR, "Release_v2")


def run_cmd(cmd: list[str]) -> None:
    """Ejecuta un comando con validación estricta de éxito. SIN shell=True."""
    logger.info("Ejecutando: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)


def build_dashboard() -> None:
    """Compila el frontend React antes de empaquetar."""
    dashboard_dir = os.path.join(ROOT_DIR, "dashboard")
    logger.info("[0/3] Compilando Dashboard React...")
    subprocess.run(
        ["npm", "run", "build"],
        cwd=dashboard_dir,
        check=True,
        shell=True,  # npm en Windows requiere shell
    )


def build() -> None:
    logger.info("=" * 60)
    logger.info(" INICIANDO EMPAQUETADO OFICIAL CON PYINSTALLER")
    logger.info("=" * 60)

    # Dashboard primero
    build_dashboard()

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
    dashboard_dist = os.path.join(ROOT_DIR, "dashboard", "dist")

    # 1. Servidor
    logger.info("\n[1/3] Compilando Servidor Central (con Dashboard incrustado)...")
    cmd_servidor = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--noconsole",
        "--log-level",
        "ERROR",
        "--name",
        "Codere_Monitor_Servidor",
        "--add-data",
        f"{dashboard_dist}{os.pathsep}dashboard_dist",
        os.path.join(ROOT_DIR, "servidor", "main.py"),
    ]
    if os.path.exists(icon_path):
        cmd_servidor.insert(6, f"--icon={icon_path}")
    run_cmd(cmd_servidor)
    shutil.copy(os.path.join(ROOT_DIR, "dist", "Codere_Monitor_Servidor.exe"), RELEASE_DIR)

    # 2. Agente
    logger.info("\n[2/3] Compilando Agente Invisible...")
    cmd_agente = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--noconsole",
        "--log-level",
        "ERROR",
        "--name",
        "Codere_Agente",
        os.path.join(ROOT_DIR, "agente", "agente.py"),
    ]
    if os.path.exists(icon_path):
        cmd_agente.insert(6, f"--icon={icon_path}")
    run_cmd(cmd_agente)
    shutil.copy(os.path.join(ROOT_DIR, "dist", "Codere_Agente.exe"), RELEASE_DIR)

    # 3. Exportador Excel (si existe el script)
    excel_script = os.path.join(ROOT_DIR, "servidor", "generar_excel_logic.py")
    if os.path.exists(excel_script):
        logger.info("\n[3/3] Compilando Exportador Excel...")
        cmd_excel = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onefile",
            "--log-level",
            "ERROR",
            "--name",
            "Codere_Exportar_Excel",
            excel_script,
        ]
        if os.path.exists(icon_path):
            cmd_excel.insert(6, f"--icon={icon_path}")
        run_cmd(cmd_excel)
        shutil.copy(os.path.join(ROOT_DIR, "dist", "Codere_Exportar_Excel.exe"), RELEASE_DIR)
    else:
        logger.warning("[3/3] Exportador Excel omitido (script no encontrado).")

    # Limpieza final
    logger.info("Limpiando directorios temporales de PyInstaller...")
    shutil.rmtree(os.path.join(ROOT_DIR, "build"), ignore_errors=True)

    logger.info("=" * 60)
    logger.info(" COMPILACIÓN COMPLETADA CON ÉXITO")
    logger.info(" Los archivos están listos en: %s", RELEASE_DIR)
    logger.info("=" * 60)


if __name__ == "__main__":
    build()
