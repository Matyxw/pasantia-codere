import os
import shutil
import subprocess
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
RELEASE_DIR = os.path.join(ROOT_DIR, "Release_Nuitka")

def run_cmd(cmd):
    print(f"\n[+] Ejecutando: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def build_with_nuitka():
    print("=" * 60)
    print(" [ INICIANDO COMPILACION EXTREMA CON NUITKA ] ")
    print(" Filosofia Core: Sacrificar tiempo por la mejor calidad.")
    print("=" * 60)

    # 1. Instalar Nuitka si no está instalado
    print("\n[0/4] Verificando Nuitka...")
    run_cmd(f"{sys.executable} -m pip install nuitka zstandard")

    if os.path.exists(RELEASE_DIR):
        try:
            shutil.rmtree(RELEASE_DIR)
        except Exception as e:
            print(f"Advertencia: No se pudo limpiar {RELEASE_DIR}: {e}")
            print("Cerrá cualquier ejecutable previo que esté corriendo.")
            return

    os.makedirs(RELEASE_DIR, exist_ok=True)
    icon_path = os.path.join(ROOT_DIR, "codere_icon.ico")
    
    # Notas sobre flags de Nuitka:
    # --standalone: Empaqueta todo para que funcione sin Python instalado en la PC destino.
    # --onefile: Genera un único .exe. (Requiere zstandard, que instalamos arriba)
    # --windows-disable-console: Equivalente a --noconsole de PyInstaller.
    # --enable-plugin=pywebview: Nuitka tiene soporte nativo para pywebview.
    # --include-data-dir: Para meter el build de React dentro del ejecutable.
    # --assume-yes-for-downloads: Permite que Nuitka descargue el compilador de C (MinGW) automáticamente si no lo tenés.

    base_flags = [
        f'"{sys.executable}" -m nuitka',
        "--standalone",
        "--onefile",
        "--windows-disable-console",
        f'--windows-icon-from-ico="{icon_path}"',
        "--assume-yes-for-downloads"
    ]

    # 1. Compilar Servidor
    print("\n[1/4] Compilando Servidor Central (Esto va a tardar MUCHO tiempo)...")
    flags_servidor = base_flags.copy()
    flags_servidor.extend([
        "--enable-plugin=pywebview",
        f'--include-data-dir="{os.path.join(ROOT_DIR, "dashboard", "dist")}=dashboard_dist"',
        "--output-dir=build_nuitka_temp",
        "--output-filename=Codere_Monitor_Servidor.exe"
    ])
    cmd_servidor = " ".join(flags_servidor) + f' "{os.path.join(ROOT_DIR, "servidor", "main.py")}"'
    run_cmd(cmd_servidor)
    shutil.copy(os.path.join(ROOT_DIR, "build_nuitka_temp", "Codere_Monitor_Servidor.exe"), RELEASE_DIR)

    # 2. Compilar Agente
    print("\n[2/4] Compilando Agente Invisible...")
    flags_agente = base_flags.copy()
    flags_agente.extend([
        "--output-dir=build_nuitka_temp",
        "--output-filename=Codere_Agente.exe"
    ])
    cmd_agente = " ".join(flags_agente) + f' "{os.path.join(ROOT_DIR, "agente", "agente.py")}"'
    run_cmd(cmd_agente)
    shutil.copy(os.path.join(ROOT_DIR, "build_nuitka_temp", "Codere_Agente.exe"), RELEASE_DIR)

    # 3. Compilar Exportador Excel
    print("\n[3/4] Compilando Exportador Excel...")
    flags_excel = base_flags.copy()
    flags_excel.extend([
        "--output-dir=build_nuitka_temp",
        "--output-filename=Codere_Exportar_Excel.exe"
    ])
    cmd_excel = " ".join(flags_excel) + f' "{os.path.join(ROOT_DIR, "scripts", "generar_excel.py")}"'
    run_cmd(cmd_excel)
    shutil.copy(os.path.join(ROOT_DIR, "build_nuitka_temp", "Codere_Exportar_Excel.exe"), RELEASE_DIR)

    # Limpieza
    print("\n[4/4] Limpiando archivos temporales de C...")
    shutil.rmtree(os.path.join(ROOT_DIR, "build_nuitka_temp"), ignore_errors=True)

    print("\n" + "=" * 60)
    print(" COMPILACIÓN DE ÉLITE CON NUITKA COMPLETADA CON ÉXITO")
    print(f" Tus nuevos ejecutables hiper-optimizados están en: {RELEASE_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    build_with_nuitka()
