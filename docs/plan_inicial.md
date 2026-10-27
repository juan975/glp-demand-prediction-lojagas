# Reparto y plan de arranque

## Principio: cortar por contenedor, acordar en los contratos

El reparto sigue las fronteras de Despliegue_v3. Cada contenedor se comunica con el siguiente **solo a través de una tabla del Lakehouse**. Si los dos acuerdan primero el esquema de esas tablas, cada quien avanza sin esperar al otro.

```
   Juan (plataforma + datos)                       Dara (modelado + salida)
┌──────────┐   Raw   ┌───────────────┐  Feature  ┌──────────────────────────┐
│ Ingesta  │ ──────► │ Procesamiento │ ────────► │ ML: entrenar → evaluar → │
└──────────┘         └───────────────┘     ▲     │ predecir → reportes      │
  + docker-compose, DAGs, servidor          │     └──────────────────────────┘
                                   CONTRATO compartido:
                       feature.demanda_mensual (columnas, tipos, granularidad)
```

| | Juan | Dara |
|---|---|---|
| Código | `ingesta/`, `procesamiento/`, `comun/`, `dags/`, `docker/` | `ml/`, `notebooks/` (EDA) |
| Word | Vistas Lógica, Procesos, Desarrollo y Despliegue; ADRs; Protección de datos | CRISP-DM (datos, modelado, evaluación); model card; métricas; Demostración |
| Revisa los PR de | Dara | Juan |

**Asígnense según sus fortalezas.** Si Dara tiene más base en ML, este es el reparto natural; si no, inviértanlo. Lo que no conviene es que cada uno haga "un poco de todo" sin dueño claro.

## Reglas para que el reparto sea dinámico y no se convierta en dos proyectos separados

1. **El contrato se acuerda primero y en pareja.** El esquema de `feature.demanda_mensual` se define en una sesión de una hora y queda en `procesamiento/contratos.py`. Mientras Juan construye el pipeline real, Dara entrena con `tests/conftest.py::serie_mensual`, que tiene la misma forma.
2. **PR pequeños** (menos de unas 300 líneas) y **revisión en menos de 24 h**. Un PR que espera tres días bloquea a los dos.
3. **Programación en pareja** solo en lo crítico: anonimización, walk-forward, regla de segmentos y el primer `docker compose up`. Son las piezas donde un error invalida la tesis.
4. **Rotación a mitad de proyecto** (después de la semana 4): cada uno toma un issue en el área del otro. Así los dos pueden defender cualquier parte ante el tribunal.
5. **Quien programa, documenta.** El PR que implementa un módulo actualiza su sección del Word y `trazabilidad.md`. El documento nunca queda atrasado respecto del código.
6. **Sincronización**: 15 minutos dos veces por semana (qué cerré, qué abro, qué me bloquea). Todo lo demás va en los issues, no en WhatsApp: los issues son evidencia del proceso para la tesis.

## Semana 1: base común (juntos)

| Tarea | Quién | Hecho cuando |
|---|---|---|
| Repo privado, colaboradora invitada, reglas de rama, `bootstrap_github.py --aplicar` | Juan | Issues creados, CI en verde |
| Entorno instalado según `docs/entorno.md` (ambos) | Ambos | `uv run pytest` en verde en las dos máquinas |
| `docker compose up` local: Airflow y MLflow responden | Juan | Captura de ambas UIs |
| Sesión del contrato `feature.demanda_mensual` | Ambos | Esquema en `contratos.py` |
| Reunión con Lojagas: versión de Odoo y regla de segmentos | Ambos | ADR-0005 decidido; `mapa_segmentos.csv` completo |

## Semanas 2–3: en paralelo

| Juan | Dara |
|---|---|
| Cliente Odoo → `raw/ventas_lineas` | EDA de la serie mensual por segmento (notebook 01) |
| `curacion` con datos reales; registrar las violaciones del contrato | Walk-forward de baselines + Ridge, registrado en MLflow (local) |
| `ingenieria_caracteristicas` produciendo la tabla del contrato | `evaluacion.py`: tabla comparativa + `supera_baseline` |
| Word: I-01, I-02, I-05, I-07, I-30 | Word: I-13, I-15, I-16, I-17 |

**Regla:** no se toca XGBoost, LightGBM ni LSTM hasta tener el número del estacional ingenuo. Ese número es la vara contra la que se mide todo lo demás.
