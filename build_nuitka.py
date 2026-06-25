import logging
import os
import shutil
import subprocess
import sys

# Configuración de Logging para el orquestador de builds
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] BUILDER - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("NuitkaBuilder")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
RELEASE_DIR = os.path.join(ROOT_DIR, "Release_Nuitka")


def run_cmd(cmd: str) -> None:
    """
    Ejecuta un comando de sistema operativo con comprobación estricta de éxito.
    
    Args:
        cmd (str): Comando raw a inyectar en el shell.
        
    Raises:
        subprocess.CalledProcessError: Si el código de salida es distinto de 0.
    """
    logger.info("Ejecutando subproceso: %s", cmd)
    subprocess.run(cmd, shell=True, check=True)


def build_with_nuitka() -> None:
    """
    Orquesta la compilación extrema AOT (Ahead-Of-Time) mediante Nuitka.
    Traduce el código Python a C puro y lo compila con MinGW/GCC para evitar
    descompilación y evadir falsos positivos heurísticos de antivirus corporativos.
    """
    logger.info("=" * 60)
    logger.info(" [ INICIANDO COMPILACION EXTREMA CON NUITKA ] ")
    logger.info(" Filosofía Core: Sacrificar tiempo por la mejor calidad.")
    logger.info("=" * 60)

    # 1. Instalar dependencias del compilador
    logger.info("[0/4] Verificando dependencias core (Nuitka, Zstandard)...")
    try:
        run_cmd(f'"{sys.executable}" -m pip install nuitka zstandard')
    except subprocess.CalledProcessError as e:
        logger.critical("Fallo al instalar Nuitka o Zstandard. Abortando build. Detalle: %s", e)
        sys.exit(1)

    # Limpieza de builds previos
    if os.path.exists(RELEASE_DIR):
        try:
            shutil.rmtree(RELEASE_DIR)
            logger.info("Directorio de release previo purgado exitosamente.")
        except PermissionError:
            logger.critical(
                "Permiso denegado al limpiar %s. Asegurate de que los ejecutables "
                "no estén corriendo o bloqueados por el Antivirus.", RELEASE_DIR
            )
            sys.exit(1)
        except Exception as e:
            logger.error("Error inesperado al limpiar release: %s", e, exc_info=True)
            sys.exit(1)

    os.makedirs(RELEASE_DIR, exist_ok=True)
    icon_path = os.path.join(ROOT_DIR, "codere_icon.ico")

    # Banderas maestras de Nuitka
    base_flags: list[str] = [
        f'"{sys.executable}" -m nuitka',
        "--standalone",                 # Empaqueta dependencias C y Python juntas
        "--onefile",                    # Compresión en un único .exe usando zstandard
        "--windows-disable-console",    # Modo silencioso (Windowed mode GUI)
        f'--windows-icon-from-ico="{icon_path}"',
        "--assume-yes-for-downloads"    # Auto-descarga de gcc/ccache si no existe
    ]

    # 1. Compilar Servidor
    logger.info("[1/4] Compilando Servidor Central (Esto tomará un tiempo considerable)...")
    flags_servidor = base_flags.copy()
    flags_servidor.extend([
        "--enable-plugin=pywebview",
        f'--include-data-dir="{os.path.join(ROOT_DIR, "dashboard", "dist")}=dashboard_dist"',
        "--include-module=plyer.platforms.win.notification",
        "--output-dir=build_nuitka_temp",
        "--output-filename=Codere_Monitor_Servidor.exe"
    ])
    cmd_servidor = " ".join(flags_servidor) + f' "{os.path.join(ROOT_DIR, "servidor", "main.py")}"'

    try:
        run_cmd(cmd_servidor)
        shutil.copy(os.path.join(ROOT_DIR, "build_nuitka_temp", "Codere_Monitor_Servidor.exe"), RELEASE_DIR)
    except subprocess.CalledProcessError:
        logger.error("Fallo la compilación del Servidor Central.")
        sys.exit(1)

    # 2. Compilar Agente
    logger.info("[2/4] Compilando Agente Invisible...")
    flags_agente = base_flags.copy()
    flags_agente.extend([
        "--output-dir=build_nuitka_temp",
        "--output-filename=Codere_Agente.exe"
    ])
    cmd_agente = " ".join(flags_agente) + f' "{os.path.join(ROOT_DIR, "agente", "agente.py")}"'

    try:
        run_cmd(cmd_agente)
        shutil.copy(os.path.join(ROOT_DIR, "build_nuitka_temp", "Codere_Agente.exe"), RELEASE_DIR)
    except subprocess.CalledProcessError:
        logger.error("Fallo la compilación del Agente.")
        sys.exit(1)

    # 3. Compilar Exportador Excel
    logger.info("[3/4] Compilando Exportador Excel...")
    flags_excel = base_flags.copy()
    flags_excel.extend([
        "--output-dir=build_nuitka_temp",
        "--output-filename=Codere_Exportar_Excel.exe"
    ])
    cmd_excel = " ".join(flags_excel) + f' "{os.path.join(ROOT_DIR, "scripts", "generar_excel.py")}"'

    try:
        run_cmd(cmd_excel)
        shutil.copy(os.path.join(ROOT_DIR, "build_nuitka_temp", "Codere_Exportar_Excel.exe"), RELEASE_DIR)
    except subprocess.CalledProcessError:
        logger.error("Fallo la compilación del Exportador Excel.")
        sys.exit(1)

    # Limpieza
    logger.info("[4/4] Limpiando artefactos intermedios y código C...")
    try:
        shutil.rmtree(os.path.join(ROOT_DIR, "build_nuitka_temp"), ignore_errors=True)
    except Exception as e:
        logger.warning("No se pudieron limpiar todos los temporales: %s", e)

    logger.info("=" * 60)
    logger.info(" COMPILACIÓN DE ÉLITE CON NUITKA COMPLETADA CON ÉXITO")
    logger.info(" Tus nuevos ejecutables hiper-optimizados están en: %s", RELEASE_DIR)
    logger.info("=" * 60)


if __name__ == "__main__":
    build_with_nuitka()
