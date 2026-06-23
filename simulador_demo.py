import os
import sqlite3
import sys
import time
from datetime import datetime

# Colores de consola
CYAN = '\033[96m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

DB_PATH = os.path.join(os.path.dirname(__file__), "servidor", "monitor.db")

def clear_screen() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header() -> None:
    clear_screen()
    print(f"{CYAN}" + "="*60 + f"{RESET}")
    print(f"{CYAN}  [ GOD MODE ] SIMULADOR DE CRISIS PARA DEMOSTRACIONES{RESET}")
    print(f"{CYAN}" + "="*60 + f"{RESET}\n")

def check_db() -> None:
    if not os.path.exists(DB_PATH):
        print(f"{RED}ERROR: No se encontró la base de datos monitor.db en el servidor.{RESET}")
        sys.exit(1)

def get_online_pcs() -> list:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, ip FROM pcs WHERE status = 'online'")
    pcs = cursor.fetchall()
    conn.close()
    return pcs

def force_offline(pc_id: str, pc_name: str, pc_ip: str) -> None:
    print(f"\n{YELLOW}[*] Desconectando brutalmente la PC {pc_name} ({pc_ip})...{RESET}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Actualizar estado a offline
    now = datetime.now().isoformat()
    cursor.execute("UPDATE pcs SET status = 'offline', last_offline = ? WHERE id = ?", (now, pc_id))

    # Inyectar evento de caída
    cursor.execute(
        "INSERT INTO events (pc_id, pc_name, pc_ip, type, timestamp) VALUES (?, ?, ?, ?, ?)",
        (pc_id, pc_name, pc_ip, 'offline', now)
    )

    conn.commit()
    conn.close()
    print(f"{GREEN}[+] Operación exitosa. Mirá el Dashboard ahora mismo. El sistema debería haber disparado la alerta.{RESET}")
    time.sleep(3)

def interactive_mode() -> None:
    check_db()
    while True:
        print_header()
        print("¿Qué crisis querés simular en vivo para la audiencia?\n")
        print("1. 💥 Simular Caída de Red (Apagar PC Online)")
        print("2. 📈 (Próximamente) Simular Ataque de Ransomware (CPU/Disco al 100%)")
        print("0. Salir\n")

        choice = input("Tu elección: ")

        if choice == '0':
            break
        elif choice == '1':
            pcs = get_online_pcs()
            if not pcs:
                print(f"\n{RED}No hay PCs Online actualmente en la base de datos para simular una caída.{RESET}")
                time.sleep(2)
                continue

            print("\nPCs disponibles para desconectar:")
            for i, pc in enumerate(pcs):
                print(f"  [{i+1}] {pc[1]} ({pc[2]})")

            try:
                sel = int(input("\nSeleccioná el número de la PC que querés tumbar: ")) - 1
                if 0 <= sel < len(pcs):
                    force_offline(pcs[sel][0], pcs[sel][1], pcs[sel][2])
                else:
                    print("Selección inválida.")
            except ValueError:
                print("Entrada inválida.")
        else:
            print("Opción no válida.")

if __name__ == "__main__":
    interactive_mode()
