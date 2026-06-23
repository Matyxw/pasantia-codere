"""
build_agent.py — Empaqueta el agente como .exe standalone con PyInstaller
El .exe resultante puede copiarse a cualquier PC sin instalar Python.

Uso:
    python build/build_agent.py

Salida:
    build/dist/PCMonitor-Agente.exe
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
AGENTE = ROOT / "agente" / "agente.py"
DIST = ROOT / "build" / "dist"


def build() -> None:
    DIST.mkdir(parents=True, exist_ok=True)

    print("=" * 55)
    print("  BUILD: PCMonitor-Agente.exe")
    print("=" * 55)
    print(f"  Fuente : {AGENTE}")
    print(f"  Salida : {DIST}")
    print()

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                          # Un solo .exe
        "--name", "PCMonitor-Agente",
        "--distpath", str(DIST),
        "--workpath", str(ROOT / "build" / "work"),
        "--specpath", str(ROOT / "build"),
        "--hidden-import", "psutil",
        "--hidden-import", "fastapi",
        "--hidden-import", "uvicorn",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.lifespan",
        "--hidden-import", "uvicorn.lifespan.on",
        "--clean",
        "--noconfirm",
        str(AGENTE),
    ]

    result = subprocess.run(cmd, cwd=ROOT)

    if result.returncode == 0:
        exe = DIST / "PCMonitor-Agente.exe"
        size_mb = exe.stat().st_size / (1024 ** 2)
        print()
        print(f"  ✅ Build exitoso!")
        print(f"  📦 {exe}")
        print(f"  📏 Tamaño: {size_mb:.1f} MB")
    else:
        print("  ❌ Build falló")
        sys.exit(1)


if __name__ == "__main__":
    build()
