# 0014 — Calendario de ejecución y horizonte de predicción

**Estado:** Propuesto. Bloqueado por la fecha límite de pedido de Lojagas.

## Contexto
El día en que corre el DAG mensual no es un detalle operativo: fija qué meses están cerrados al momento de predecir y, con eso, el horizonte del modelo. Con datos hasta M−1, predecir M es horizonte 1 y predecir M+1 es horizonte 2. El horizonte decide qué rezagos se pueden usar como features, cómo se arma el walk-forward y qué se reporta.

Hoy las piezas no coinciden:

- `dags/prediccion_mensual.py` corre el día 2 de cada mes a las 06:00.
- El Word (3.4.5.5) dice que el DAG corre el primer día de cada mes y predice el mes siguiente.
- La model card fijaba horizonte 1 (hasta la decisión provisional de abajo).

En una reunión, Lojagas indicó que necesita tiempo para preparar sus pedidos, pero todavía no se definió la fecha límite ni a qué mes corresponde cada pedido.

## Decisión provisional
Se mantiene la ejecución el día 2. Ese día el mes anterior ya está cerrado y la predicción llega con el mayor margen posible. Ejecutar a mediados de mes no da más tiempo de planificación para el mismo mes objetivo: da menos.

Se trabaja con **horizonte 2**: el día 2 del mes M, con datos hasta M−1, se predice M+1 (el 2 de noviembre se predice diciembre). El código lo lee de `Config.horizonte_meses`, y de ese valor dependen los rezagos, las medias móviles, el baseline ingenuo y la separación del walk-forward; un test falla si una feature usa un mes no cerrado. Si Lojagas confirma horizonte 1, se cambia ese valor y se repiten los experimentos.

El EDA apoya el día 2: por el orden de `factura_id`, como máximo el 0,02 % de los kg de un mes se registra después del día 2 del mes siguiente. Es una aproximación: no detecta borradores publicados tarde (falta `create_date`).

## Pregunta para Lojagas
¿Cuál es la fecha límite para solicitar el cupo de GLP y a qué mes corresponde ese pedido?

## Consecuencias
- La respuesta fija el día de ejecución y el horizonte. Ambos se registran aquí, en la model card y en la sección 3.4.5.5 del Word.
- Hay que decidirlo **antes del EDA**. Cambiar el `cron` es una línea; cambiar el horizonte después de entrenar obliga a repetir los experimentos A y B.
