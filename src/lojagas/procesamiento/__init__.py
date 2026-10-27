"""«Contenedor Procesamiento» — Módulo Tratamiento Datos (Despliegue_v3).

- curacion.py: Raw → Curated (contrato → seudonimización → agregación → contrato).
- ingenieria_caracteristicas.py: Curated → Feature.

Regla de oro: toda feature debe poder calcularse con información disponible
el día en que se ejecuta la predicción (ver `Fuente.disponible_desde_dias`).
"""
