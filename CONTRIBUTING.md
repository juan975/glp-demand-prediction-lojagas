# Cómo trabajamos

Somos dos. Cada línea que llega a `main` la revisó la otra persona. Esto no es burocracia: es la evidencia de "reproducción cruzada por al menos dos miembros" que promete la sección 3.6.1 de la tesis.

## Ramas y PRs

- `main` está protegida: sin push directo, con CI en verde y una aprobación.
- Ramas cortas desde `main`, de uno a tres días como máximo:
  - `feat/descripcion` para código nuevo
  - `fix/descripcion` para errores
  - `docs/descripcion` para ADRs, model card y trazabilidad
  - `tesis/descripcion` para correcciones que nacen de una inconsistencia del Word
  - `refactor/descripcion` y `test/descripcion` cuando corresponda
- Cada PR cierra un issue (`Closes #12` en la descripción). Sin issue no hay PR. El número va en el PR, no en el nombre de la rama.
- Si un PR depende de otro que todavía no se mergea, se abre en borrador con ese otro como base. Al mergear el primero con squash, el segundo se rebasa con `git rebase --onto main <rama-base> <rama>`.
- Se integra con *squash merge*: un commit por PR en `main`.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/es/v1.0.0/) en español:

```
feat(ingesta): extraer facturas por rango de fechas
fix(features): rezagos desalineados al faltar un mes
docs(adr): 0002 proxy del socket de Docker
test(walk-forward): caso de un solo segmento
```

## Reparto

Por contenedor del diagrama de despliegue. El detalle y las reglas para mantenerlo dinámico están en [`docs/plan_inicial.md`](docs/plan_inicial.md); los dueños por carpeta, en `.github/CODEOWNERS`.

## Reglas que no se negocian

1. **Ningún dato real en git.** Ni CSV, ni Parquet, ni notebooks con salidas. El pre-commit lo bloquea y CI lo vuelve a revisar.
2. **Ningún secreto en git.** Todo va en `.env`, que no se versiona.
3. **Tests con datos sintéticos.** Si un bug solo aparece con datos reales, se reproduce con un fixture sintético.
4. **Si cambia el diagrama, cambia el código, y viceversa.** El PR actualiza `docs/arquitectura/trazabilidad.md`.
5. **Decisión no trivial = ADR.** Va en `docs/adr/` antes o junto con el código que la implementa.
6. **Toda inconsistencia con el Word es un issue** con la etiqueta `tesis`. Es el backlog oficial (`docs/inconsistencias.md` explica la convención).
7. **Nunca se imprimen registros de clientes**, ni para depurar. Lo que imprime un contenedor de trabajo queda en los logs de Airflow y la última línea en su base de datos: PII fuera del Lakehouse.
8. **Los hooks no se saltan.** Nada de `--no-verify`. Si un hook modifica un archivo, se vuelve a hacer `git add` y se repite el commit.
9. **Dependencias con `uv add`** en el extra que corresponda, con `pyproject.toml` y `uv.lock` en el mismo commit. Nada de `pip install` dentro del entorno.
10. **Si cambia `docker-compose.yml`, un Dockerfile o las redes**, el DAG `prueba_humo` tiene que terminar en `success` antes de pedir revisión.

## Etiquetas de issues

- Fase CRISP-DM: `crisp:negocio`, `crisp:datos`, `crisp:preparacion`, `crisp:modelado`, `crisp:evaluacion`, `crisp:despliegue`
- Vista 4+1: `vista:logica`, `vista:procesos`, `vista:desarrollo`, `vista:fisica`, `vista:escenarios`
- `tesis`: corrección del documento Word
- Prioridad: `p0-bloqueante`, `p1-mayor`, `p2-menor`

## Entregas

Cada entrega de Prácticum se marca con un tag (`p41-entrega-final`, `p42-avance-1`…). Así el capítulo de resultados puede citar el commit exacto con el que se obtuvo cada número.
