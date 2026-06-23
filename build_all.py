import os
import subprocess
import shutil

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
RELEASE_DIR = os.path.join(ROOT_DIR, "Release_v2")

def run_cmd(cmd):
    print(f"Ejecutando: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def build():
    print("=" * 50)
    print(" INICIANDO EMPAQUETADO CON PYINSTALLER")
    print("=" * 50)

    if os.path.exists(RELEASE_DIR):
        shutil.rmtree(RELEASE_DIR)
    os.makedirs(RELEASE_DIR, exist_ok=True)

    # 1. Servidor
    print("\n[1/3] Compilando Servidor Central (con Dashboard incrustado)...")
    cmd_servidor = f'python -m PyInstaller --noconfirm --clean --onefile --noconsole --name "PC_Monitor_Servidor" --icon="{ROOT_DIR}/codere_icon.ico" --hidden-import webview --exclude-module PyQt5 --exclude-module tkinter --add-data "{ROOT_DIR}/dashboard/dist;dashboard_dist" {ROOT_DIR}/servidor/main.py'
    run_cmd(cmd_servidor)
    shutil.copy(os.path.join(ROOT_DIR, "dist", "PC_Monitor_Servidor.exe"), RELEASE_DIR)

    # 2. Agente
    print("\n[2/3] Compilando Agente Invisible...")
    cmd_agente = f'python -m PyInstaller --noconfirm --clean --onefile --name "Agente_PC" --noconsole --icon="{ROOT_DIR}/codere_icon.ico" --exclude-module PyQt5 --exclude-module tkinter {ROOT_DIR}/agente/agente.py'
    run_cmd(cmd_agente)
    shutil.copy(os.path.join(ROOT_DIR, "dist", "Agente_PC.exe"), RELEASE_DIR)

    # 3. Exportador Excel
    print("\n[3/3] Compilando Exportador Excel...")
    cmd_excel = f'python -m PyInstaller --noconfirm --clean --onefile --name "Exportar_Excel" --icon="{ROOT_DIR}/codere_icon.ico" --exclude-module PyQt5 --exclude-module tkinter {ROOT_DIR}/scripts/generar_excel.py'
    run_cmd(cmd_excel)
    shutil.copy(os.path.join(ROOT_DIR, "dist", "Exportar_Excel.exe"), RELEASE_DIR)

    print("\n" + "=" * 50)
    print(" COMPILACION COMPLETADA CON EXITO")
    print(f" Los archivos estan listos en: {RELEASE_DIR}")
    print("=" * 50)

if __name__ == "__main__":
    build()
