"""
build_server.py — Empaqueta el servidor central como .exe standalone

Uso:
    python build/build_server.py

Salida:
    build/dist/PCMonitor-Servidor.exe
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SERVIDOR = ROOT / "servidor" / "main.py"
DIST = ROOT / "build" / "dist"


def build() -> None:
    DIST.mkdir(parents=True, exist_ok=True)

    print("=" * 55)
    print("  BUILD: PCMonitor-Servidor.exe")
    print("=" * 55)
    print(f"  Fuente : {SERVIDOR}")
    print(f"  Salida : {DIST}")
    print()

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name",
        "PCMonitor-Servidor",
        "--distpath",
        str(DIST),
        "--workpath",
        str(ROOT / "build" / "work"),
        "--specpath",
        str(ROOT / "build"),
        "--hidden-import",
        "fastapi",
        "--hidden-import",
        "uvicorn",
        "--hidden-import",
        "uvicorn.logging",
        "--hidden-import",
        "uvicorn.loops.auto",
        "--hidden-import",
        "uvicorn.protocols.http.auto",
        "--hidden-import",
        "uvicorn.protocols.websockets.auto",
        "--hidden-import",
        "uvicorn.lifespan.on",
        "--hidden-import",
        "apscheduler",
        "--hidden-import",
        "apscheduler.schedulers.background",
        "--hidden-import",
        "apscheduler.executors.pool",
        "--hidden-import",
        "sqlalchemy",
        "--hidden-import",
        "sqlalchemy.dialects.sqlite",
        "--hidden-import",
        "pydantic_settings",
        "--collect-data",
        "uvicorn",
        "--clean",
        "--noconfirm",
        str(SERVIDOR),
    ]

    result = subprocess.run(cmd, cwd=ROOT)

    if result.returncode == 0:
        exe = DIST / "PCMonitor-Servidor.exe"
        size_mb = exe.stat().st_size / (1024**2)
        print()
        print("  [OK] Build exitoso!")
        print(f"  [EXE] {exe}")
        print(f"  [SIZE] Tamaño: {size_mb:.1f} MB")
        print()
        print("  [WARN]  Recordá colocar el .env junto al .exe antes de ejecutar")
    else:
        print("  [FAIL] Build falló")
        sys.exit(1)


if __name__ == "__main__":
    build()
