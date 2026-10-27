"""Crea etiquetas e issues en GitHub a partir de docs/inconsistencias.md.

Uso (una sola vez, desde la raíz del repo, con `gh auth login` hecho):
    python scripts/bootstrap_github.py            # muestra lo que haría
    python scripts/bootstrap_github.py --aplicar  # lo hace
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ETIQUETAS = {
    "tesis": "5319e7",
    "p0-bloqueante": "b60205",
    "p1-mayor": "d93f0b",
    "p2-menor": "fbca04",
    **{
        f"crisp:{f}": "0e8a16"
        for f in ["negocio", "datos", "preparacion", "modelado", "evaluacion", "despliegue"]
    },
    **{
        f"vista:{v}": "1d76db" for v in ["logica", "procesos", "desarrollo", "fisica", "escenarios"]
    },
}
PRIORIDAD = {"P0": "p0-bloqueante", "P1": "p1-mayor", "P2": "p2-menor"}


def issues(md: str):
    prioridad = None
    for linea in md.splitlines():
        if m := re.match(r"## (P\d)", linea):
            prioridad = PRIORIDAD[m.group(1)]
        if m := re.match(r"\| (I-\d+) \| (.+?) \| (.+?) \|(?: (.+?) \|)?$", linea):
            iid, donde, problema, correccion = m.groups()
            cuerpo = f"**Ubicación:** {donde}\n\n**Problema:** {problema}"
            if correccion:
                cuerpo += f"\n\n**Corrección propuesta:** {correccion}"
            titulo = f"[{iid}] {donde}: {problema[:70]}"
            yield titulo, cuerpo, ["tesis", prioridad]


def main() -> None:
    aplicar = "--aplicar" in sys.argv
    md = Path("docs/inconsistencias.md").read_text(encoding="utf-8")

    def run(cmd: list[str]) -> None:
        print(" ".join(cmd[:6]), "...")
        if aplicar:
            subprocess.run(cmd, check=False)

    for nombre, color in ETIQUETAS.items():
        run(["gh", "label", "create", nombre, "--color", color, "--force"])
    for titulo, cuerpo, etiquetas in issues(md):
        run(
            [
                "gh",
                "issue",
                "create",
                "--title",
                titulo,
                "--body",
                cuerpo,
                "--label",
                ",".join(etiquetas),
            ]
        )


if __name__ == "__main__":
    main()
