# Entorno de desarrollo

Objetivo: que los dos tengamos **exactamente** el mismo Python, las mismas librerías y las mismas reglas de commit. Si los entornos difieren, ninguna métrica es reproducible.

La regla general: **todo el código vive y se ejecuta dentro de Ubuntu (WSL2)**, nunca en Windows. Windows solo pone Docker Desktop y VS Code. Esta guía se probó de punta a punta el 11 de noviembre de 2026, con la prueba de humo de la plataforma. Si algo no sale igual, detente y avisa antes de improvisar: casi todos los errores de esa prueba vinieron de saltarse un detalle.

## 1. Antes de empezar

- Windows 10 u 11 con la virtualización activada en la BIOS.
- 16 GB de RAM o más. Airflow pide al menos 4 GB para Docker, y con 8 GB ya va justo.
- Unos 15 GB libres en disco: solo las imágenes ocupan alrededor de 6 GB.
- Una conexión estable. La primera construcción descarga varios cientos de MB. **No suspendas la computadora mientras construye**: si la red se corta a mitad de una descarga, pip aborta con un error de integridad.

## 2. Instalar (una vez)

**WSL2 con Ubuntu.** En PowerShell como administrador: `wsl --install -d Ubuntu-24.04`. Reinicia, abre Ubuntu, crea tu usuario y comprueba con `wsl -l -v` que la versión sea la 2.

**Docker Desktop.** En *Settings*: *Use the WSL 2 based engine* activado y, en *Resources → WSL integration*, tu Ubuntu activado. Comprueba desde Ubuntu:

```bash
docker run --rm hello-world
docker info | grep -i "total memory"   # idealmente 8 GB o más
```

**VS Code** en Windows, con la extensión **WSL**. El resto de extensiones las sugiere el propio repositorio (`.vscode/extensions.json`).

**Herramientas en Ubuntu:**

```bash
sudo apt update && sudo apt install -y git make curl
git config --global user.name "Nombre Apellido"
git config --global user.email "correo-de-github"
git config --global pull.rebase true          # historial lineal, sin merges de "sincronización"
```

**GitHub CLI.** No lo instales con `sudo apt install gh` a secas: la versión de los repositorios de Ubuntu es muy vieja y falla con los PR. Sigue la sección *Debian / Ubuntu (apt)* de las instrucciones oficiales de GitHub CLI. Después: `gh auth login` (GitHub.com → HTTPS → navegador) y `gh auth setup-git`.

**uv:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
uv python install 3.11
```

**Comprobación importante.** WSL agrega las rutas de Windows al PATH de Ubuntu, y puede pasar que `python` apunte al Python de Windows. Ejecuta `which -a python python3`: si alguna ruta empieza con `/mnt/c/`, hay que quitarla en `~/.bashrc`. No desactives por completo las rutas de Windows, porque el comando `code` depende de ellas.

## 3. Clonar y preparar el repositorio

```bash
mkdir -p ~/code && cd ~/code
gh repo clone juan975/glp-demand-prediction-lojagas
cd glp-demand-prediction-lojagas
uv sync --extra ingesta --extra procesamiento --extra ml --extra interfaz
uv run pre-commit install
uv run pytest                                 # debe salir todo en verde
code .
```

- Clona **dentro de Linux**, nunca en `/mnt/c/`: es lento para Docker y da problemas de permisos. Una sola copia del repositorio; el Word, EA y Canva van en otra carpeta de Windows, sin Git.
- **No uses `--all-extras`**: arrastra PyTorch con CUDA, que pesa varios GB y no sirve (el servidor no tiene GPU).
- Abre VS Code siempre con `code .` desde Ubuntu. Abajo a la izquierda debe decir "WSL: Ubuntu".

## 4. Datos y `.env`

Crea la carpeta de datos tú, antes de levantar nada. Si la crea Docker, queda a nombre de root y nadie puede escribir en ella:

```bash
mkdir -p ~/lojagas_datos/{pg_data,mlruns,reportes,lakehouse/{raw,curated,feature,predicciones}}
cp .env.example .env
chmod 600 .env
```

En el `.env`, para desarrollo:

| Variable | Valor | Por qué |
|---|---|---|
| `LOJAGAS_DATA_ROOT` | `/home/<tu_usuario>/lojagas_datos` | El ejemplo trae la ruta del servidor. |
| `AIRFLOW_UID` | el resultado de `id -u` (casi siempre 1000) | Con 50000, los archivos que escribe Airflow te quedan sin permisos. |
| `LOJAGAS_LAN_IP` | `127.0.0.1` | El ejemplo trae la IP del servidor. |
| `COMPOSE_FILE` | `docker-compose.yml:compose.dev.yml` | Publica MLflow y Airflow para abrirlos en el navegador. Solo en desarrollo. |
| `LOJAGAS_IMAGE_TAG` | `dev` | Es la etiqueta que construye `docker compose build`. |

Los secretos vienen vacíos a propósito: el compose no arranca hasta que existan.

```bash
# AIRFLOW_FERNET_KEY
uv run --with cryptography python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# AIRFLOW_JWT_SECRET y LOJAGAS_PII_SALT
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

La sal de PII se acuerda entre los dos: si vamos a intercambiar archivos de Curated o Feature, tiene que ser la misma. En producción no la generamos nosotros: la genera y custodia el administrador de Lojagas.

Reglas sin excepciones:

1. El `.env` nunca se pega en un chat (WhatsApp, correo o una IA) ni se copia a OneDrive, Drive o `/mnt/c/`. Para mostrarlo: `sed 's/=.*/=***/' .env`.
2. La sal de PII y la clave Fernet se respaldan en un gestor de contraseñas (KeePassXC o Bitwarden). Si se pierden, no se recuperan.
3. El dataset real tiene cédulas, RUC, nombres y coordenadas (LOPDP). Va solo en `LOJAGAS_DATA_ROOT`, nunca en una carpeta sincronizada ni en adjuntos, y el disco tiene que estar cifrado (BitLocker en Windows). Cuando el servidor de Lojagas esté listo, se trabaja contra él por *VS Code Remote-SSH* y la copia local se borra.

## 5. Levantar la plataforma y comprobarla

```bash
docker compose --profile jobs build ingesta procesamiento
docker compose config --quiet && echo "config OK"
docker compose up -d
docker compose ps
```

`docker compose up -d` no levanta los contenedores de trabajo: esos solo se construyen, y es Airflow quien los lanza. (`make build` es para el servidor: etiqueta las imágenes con el SHA del commit, y entonces hay que poner ese SHA en `LOJAGAS_IMAGE_TAG`.)

```bash
curl -s http://127.0.0.1:8080/api/v2/monitor/health; echo
curl -s http://127.0.0.1:5000/health; echo
docker compose exec airflow-scheduler airflow dags unpause prueba_humo
docker compose exec airflow-scheduler airflow dags trigger prueba_humo
```

En un minuto, el DAG `prueba_humo` tiene que terminar en *success* (Airflow en `http://localhost:8080`, con el usuario del `.env`; MLflow en `http://localhost:5000`). Para apagar sin perder nada: `docker compose stop`.

## 6. Configurar GitHub (lo hace el dueño del repo, una vez)

1. **Settings → Code security**: activar *Secret scanning* y *Push protection* (gratis en repos públicos).
2. **Settings → Collaborators**: invitar a la otra persona con rol *Write*.
3. **Settings → Branches → Add rule** para `main`: *Require a pull request* (1 aprobación), *Require status checks* (`calidad`) y *Do not allow bypassing*.
4. **Projects → New project → Board** con las columnas *Backlog → Esta semana → En curso → En revisión → Hecho*.
5. `python scripts/bootstrap_github.py --aplicar` crea las etiquetas y los issues iniciales.

Las reglas de trabajo (ramas, commits, revisión) están en [`CONTRIBUTING.md`](../CONTRIBUTING.md).
