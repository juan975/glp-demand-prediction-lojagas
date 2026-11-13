# 0014 — Calendario de ejecución y horizonte de predicción

**Estado:** Propuesto. Bloqueado por la fecha límite de pedido de Lojagas.

## Contexto
El día en que corre el DAG mensual no es un detalle operativo: fija qué meses están cerrados al momento de predecir y, con eso, el horizonte del modelo. Con datos hasta M−1, predecir M es horizonte 1 y predecir M+1 es horizonte 2. El horizonte decide qué rezagos se pueden usar como features, cómo se arma el walk-forward y qué se reporta.

Hoy las piezas no coinciden:

- `dags/prediccion_mensual.py` corre el día 2 de cada mes a las 06:00.
- El Word (3.4.5.5) dice que el DAG corre el primer día de cada mes y predice el mes siguiente.
- La model card fija horizonte 1.

En una reunión, Lojagas indicó que necesita tiempo para preparar sus pedidos, pero todavía no se definió la fecha límite ni a qué mes corresponde cada pedido.

## Decisión provisional
Se mantiene la ejecución el día 2. Ese día el mes anterior ya está cerrado y la predicción llega con el mayor margen posible. Ejecutar a mediados de mes no da más tiempo de planificación para el mismo mes objetivo: da menos.

## Pregunta para Lojagas
¿Cuál es la fecha límite para solicitar el cupo de GLP y a qué mes corresponde ese pedido?

## Consecuencias
- La respuesta fija el día de ejecución y el horizonte. Ambos se registran aquí, en la model card y en la sección 3.4.5.5 del Word.
- Hay que decidirlo **antes del EDA**. Cambiar el `cron` es una línea; cambiar el horizonte después de entrenar obliga a repetir los experimentos A y B.
