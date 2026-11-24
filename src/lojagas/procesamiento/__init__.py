"""«Contenedor Procesamiento» — Módulo Tratamiento Datos (diagrama de despliegue).

- curacion.py: Raw → Curated (contrato → seudonimización → agregación → contrato).
- ingenieria_caracteristicas.py: Curated → Feature.
- dias_venta.py: pesos de los días de la semana y días de venta de cada mes.
- clima.py: ERA5-Land por provincia (Curated) y sus variables con rezago (Feature).

Regla de oro: toda feature debe poder calcularse con información disponible
el día en que se ejecuta la predicción (ver `Fuente.disponible_desde_dias` y
`temporales.rezago_minimo_externo`).
"""
