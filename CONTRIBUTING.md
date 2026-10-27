# Cómo trabajamos

Somos dos. Cada línea que llega a `main` la revisó la otra persona. Esto no es burocracia: es la evidencia de "reproducción cruzada por al menos dos miembros" que promete la sección 3.6.1 de la tesis.

## Ramas y PRs

- `main` está protegida: sin push directo, con CI en verde y una aprobación.
- Ramas cortas desde `main`, de uno a tres días como máximo:
  - `feat/<issue>-descripcion` para código nuevo
  - `fix/<issue>-descripcion` para errores
  - `docs/<issue>-descripcion` para ADRs, model card y trazabilidad
  - `tesis/<issue>-descripcion` para correcciones que nacen de una inconsistencia del Word
- Cada PR cierra un issue (`Closes #12`). Sin issue no hay PR.
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

Por contenedor de Despliegue_v3. El detalle y las reglas para mantenerlo dinámico están en [`docs/plan_inicial.md`](docs/plan_inicial.md); los dueños por carpeta, en `.github/CODEOWNERS`.

## Reglas que no se negocian

1. **Ningún dato real en git.** Ni CSV, ni Parquet, ni notebooks con salidas. El pre-commit lo bloquea y CI lo vuelve a revisar.
2. **Ningún secreto en git.** Todo va en `.env`, que no se versiona.
3. **Tests con datos sintéticos.** Si un bug solo aparece con datos reales, se reproduce con un fixture sintético.
4. **Si cambia el diagrama, cambia el código, y viceversa.** El PR actualiza `docs/arquitectura/trazabilidad.md`.
5. **Decisión no trivial = ADR.** Va en `docs/adr/` antes o junto con el código que la implementa.
6. **Toda inconsistencia con el Word se registra** en `docs/inconsistencias.md` o como issue con la etiqueta `tesis`.

## Etiquetas de issues

- Fase CRISP-DM: `crisp:negocio`, `crisp:datos`, `crisp:preparacion`, `crisp:modelado`, `crisp:evaluacion`, `crisp:despliegue`
- Vista 4+1: `vista:logica`, `vista:procesos`, `vista:desarrollo`, `vista:fisica`, `vista:escenarios`
- `tesis`: corrección del documento Word
- Prioridad: `p0-bloqueante`, `p1-mayor`, `p2-menor`

## Entregas

Cada entrega de Prácticum se marca con un tag (`p41-entrega-final`, `p42-avance-1`…). Así el capítulo de resultados puede citar el commit exacto con el que se obtuvo cada número.
