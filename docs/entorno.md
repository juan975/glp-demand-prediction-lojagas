# Entorno de trabajo (cada integrante)

Objetivo: que los dos tengan **exactamente** el mismo Python, las mismas librerías y las mismas reglas de commit. Si los entornos difieren, ninguna de las métricas es reproducible.

## 1. Instalar (una vez)

| Herramienta | Para qué | Windows | macOS / Linux |
|---|---|---|---|
| **WSL2 + Ubuntu** | Airflow no corre nativo en Windows | `wsl --install` y luego trabajar **dentro** de Ubuntu | — |
| **Git** | Control de versiones | dentro de WSL: `sudo apt install git` | viene instalado o con `brew` |
| **uv** | Python 3.11 y dependencias fijadas | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | igual |
| **Docker Desktop** | Levantar Airflow, MLflow y PostgreSQL | activar *WSL integration* | instalador oficial |
| **GitHub CLI (`gh`)** | PRs e issues desde la terminal | `sudo apt install gh` | `brew install gh` |
| **VS Code** | Editor | extensiones: Python, Ruff, Jupyter, Docker, WSL, GitHub Pull Requests | igual, sin WSL |

En Windows, clonen el repo **dentro de WSL** (`~/code/...`), no en `C:\`. El disco de Windows visto desde WSL es lento y mezcla finales de línea.

## 2. Configurar el repo (una vez)

```bash
git config --global user.name "Nombre Apellido"
git config --global user.email "correo-de-github"
git config --global pull.rebase true          # historial lineal, sin merges de "sincronización"

gh auth login
gh repo clone juan975/glp-demand-prediction-lojagas
cd glp-demand-prediction-lojagas

uv python install 3.11
uv sync --all-extras                          # crea .venv con versiones fijadas en uv.lock
uv run pre-commit install                     # ruff, bloqueo de datos y secretos
uv run pytest                                 # debe salir todo en verde
cp .env.example .env                          # completar; .env nunca se sube
```

En VS Code: `Ctrl+Shift+P` → *Python: Select Interpreter* → `.venv`. Activen *Format on Save* con Ruff.

## 3. Datos reales en tu máquina

El dataset tiene cédulas, RUC, nombres y coordenadas (LOPDP).

- Guárdenlo **fuera del repo**, en `LOJAGAS_DATA_ROOT` (por ejemplo `~/lojagas_datos/`).
- **Nunca** en una carpeta sincronizada (OneDrive, Google Drive, iCloud) ni adjunto en WhatsApp o correo.
- Disco cifrado: BitLocker en Windows, FileVault en macOS.
- Cuando el servidor de Lojagas esté listo, se desarrolla contra él con *VS Code Remote-SSH* y la copia local se borra.

## 4. Ciclo diario

```bash
git switch main && git pull                   # empezar siempre desde main actualizado
git switch -c feat/12-cliente-odoo            # una rama por issue
# ... código + test ...
uv run pytest && git add -p && git commit     # commits pequeños, Conventional Commits
git push -u origin HEAD
gh pr create --fill                           # "Closes #12" en la descripción
```

## 5. Configurar GitHub (lo hace el dueño del repo, una vez)

1. **Settings → Code security → activar *Secret scanning* y *Push protection*** (gratis en repos públicos): GitHub bloquea el push si detecta una clave.
2. **Settings → Collaborators →** invitar a la otra persona con rol *Write*.
3. **Settings → Branches → Add rule** para `main`: *Require a pull request* (1 aprobación), *Require status checks* (`calidad`) y *Do not allow bypassing*.
   - En repos públicos las reglas de rama son gratis.
4. **Projects → New project → Board** con las columnas *Backlog → Esta semana → En curso → En revisión → Hecho*.
5. `python scripts/bootstrap_github.py --aplicar` crea las etiquetas y un issue por inconsistencia.
