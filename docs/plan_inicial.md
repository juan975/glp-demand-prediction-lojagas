# Reparto y plan de arranque

## Principio: cortar por contenedor, acordar en los contratos

El reparto sigue las fronteras de Despliegue_v4. Cada contenedor se comunica con el siguiente **solo a través de una tabla del Lakehouse**. Si los dos acuerdan primero el esquema de esas tablas, cada quien avanza sin esperar al otro.

```
   Dara (datos de entrada)          Juan (plataforma)         Dara + Juan (modelado)
┌──────────┐   Raw   ┌───────────────┐  Feature  ┌──────────────────────────┐
│ Ingesta  │ ──────► │ Procesamiento │ ────────► │ EDA → entrenar → evaluar │
└──────────┘         └───────────────┘     ▲     │ → predecir → reportes    │
                                           │     └──────────────────────────┘
          + docker-compose, DAGs, servidor │
                                   CONTRATO compartido:
                       feature.demanda_mensual (columnas, tipos, granularidad)
```

| | Juan | Dara |
|---|---|---|
| Código | `comun/`, `procesamiento/`, `dags/`, `docker/` | `ingesta/`, `ml/`, `notebooks/` |
| Word | Vistas Lógica, Procesos, Desarrollo y Despliegue; ADRs; Protección de datos | CRISP-DM (datos, modelado, evaluación); model card; métricas; Demostración |
| Revisa los PR de | Dara | Juan |

La **interfaz de consulta** (`src/lojagas/interfaz/`, `docker/interfaz/`) todavía no tiene dueño. Es trabajo de las últimas semanas y conviene asignarla cuando se sepa quién va más holgado.

## Reglas para que el reparto sea dinámico y no se convierta en dos proyectos separados

1. **El contrato se acuerda primero y en pareja.** El esquema de `feature.demanda_mensual` se define en una sesión de una hora y queda en `procesamiento/contratos.py`. Mientras Juan construye el pipeline real, Dara entrena con `tests/conftest.py::serie_mensual`, que tiene la misma forma.
2. **PR pequeños** (menos de unas 300 líneas) y **revisión en menos de 24 h**. Un PR que espera tres días bloquea a los dos.
3. **Programación en pareja** solo en lo crítico: anonimización, walk-forward, regla de segmentos y el primer `docker compose up`. Son las piezas donde un error invalida la tesis.
4. **El EDA se hace entre los dos.** No es una tarea que se reparta: de ahí salen las decisiones sobre segmentos, horizonte y tratamiento de los ceros, y las dos personas tienen que poder defenderlas.
5. **Quien programa, documenta.** El PR que implementa un módulo actualiza su sección del Word y `trazabilidad.md`. El documento nunca queda atrasado respecto del código.
6. **Sincronización**: 15 minutos dos veces por semana (qué cerré, qué abro, qué me bloquea). Todo lo demás va en los issues, no en WhatsApp: los issues son evidencia del proceso para la tesis.

## Semana 1: base común (juntos)

| Tarea | Quién | Hecho cuando |
|---|---|---|
| Colaboradora invitada, reglas de rama, `bootstrap_github.py --aplicar` | Juan | Issues creados, CI en verde |
| Entorno instalado según `docs/entorno.md` | Ambos | `uv run pytest` en verde en las dos máquinas |
| `docker compose up` local: Airflow y MLflow responden | Juan | Captura de ambas UIs |
| Sesión del contrato `feature.demanda_mensual` | Ambos | Esquema en `contratos.py` |
| Reunión con Lojagas: versión de Odoo y regla de segmentos | Ambos | ADR-0005 decidido; `mapa_segmentos.csv` completo |

## Semanas 2–3: en paralelo

| Dara | Juan |
|---|---|
| Cliente Odoo → `raw/ventas_lineas` | `curacion` con datos reales; registrar las violaciones del contrato |
| Fuentes externas de nivel 1 → `raw/` | `ingenieria_caracteristicas` produciendo la tabla del contrato |
| Word: I-13, I-15, I-16, I-17 | Word: I-01, I-02, I-05, I-07, I-30 |

Al cerrar la semana 3, **el EDA de la serie mensual por segmento se hace en pareja** sobre la tabla ya producida por el pipeline. De ahí sale el cuaderno 01 y las decisiones que condicionan el modelado.

## Semanas 4 en adelante: modelado

El entrenamiento se reparte sobre el mismo protocolo de walk-forward, con **dos configuraciones que comparten particiones, algoritmos y presupuesto de búsqueda**:

- **Configuración A**: solo variables derivadas del histórico de ventas.
- **Configuración B**: A más las fuentes contextuales externas.

La comparación entre ambas es la que responde a la pregunta de investigación, así que ninguna de las dos puede quedar peor instrumentada que la otra. Conviene que cada persona tome una configuración y que la otra revise sus resultados antes de darlos por buenos.

**Regla:** no se toca XGBoost, LightGBM ni LSTM hasta tener el número del estacional ingenuo. Ese número es la vara contra la que se mide todo lo demás.
