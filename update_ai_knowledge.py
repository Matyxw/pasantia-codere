"""
update_ai_knowledge.py — El Auto-Renovador de Contexto IA

Este script escanea el repositorio automáticamente para extraer el árbol de directorios
actualizado, versiones de dependencias (Python y Node) y los esquemas de la BD.
Lo inyecta todo en `docs/ai_context_dump.md` para que la IA (vos) pueda leerlo y
saber EXACTAMENTE cómo está el proyecto en tiempo real sin gastar tokens adivinando.

Uso por el Agente:
    python update_ai_knowledge.py
    (Y luego leer docs/ai_context_dump.md)
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent
OUTPUT = ROOT / "docs" / "ai_context_dump.md"


def get_tree() -> str:
    # Usar git ls-tree para ignorar archivos basura si está en un repo
    try:
        res = subprocess.run(["git", "ls-tree", "-r", "--name-only", "HEAD"], capture_output=True, text=True)
        if res.returncode == 0:
            files = [f for f in res.stdout.splitlines() if not f.startswith(".")]
            return "\n".join(files[:200]) + ("\n... (truncado)" if len(files) > 200 else "")
    except Exception:
        pass
    return "Error al generar árbol."


def get_dependencies() -> str:
    output = "### Python (pyproject.toml)\n```toml\n"
    pyproject = ROOT / "pyproject.toml"
    if pyproject.exists():
        with open(pyproject, encoding="utf-8") as f:
            for line in f:
                if line.startswith("dependencies") or "fastapi" in line or "react" in line:
                    pass # Leeremos un extracto simplificado
            output += pyproject.read_text(encoding="utf-8")[:500] + "\n```\n"

    output += "\n### Node (package.json)\n```json\n"
    pkg = ROOT / "dashboard" / "package.json"
    if pkg.exists():
        with open(pkg, encoding="utf-8") as f:
            data = json.load(f)
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            output += json.dumps(deps, indent=2) + "\n```\n"
    return output


def update_knowledge():
    ROOT.joinpath("docs").mkdir(exist_ok=True)
    content = f"""# AI Context Dump — PC Monitor v2.0
*Auto-generado el: {datetime.now().isoformat()}*

Este archivo es un snapshot automático del proyecto. Léelo para actualizar tu contexto.

## Estructura de Archivos
```text
{get_tree()}
```

## Dependencias Instaladas
{get_dependencies()}
"""
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ Contexto IA actualizado exitosamente en: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    update_knowledge()
