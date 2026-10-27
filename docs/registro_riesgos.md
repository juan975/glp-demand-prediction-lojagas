# Registro de riesgos (ISO/IEC 23894:2023)

Los riesgos R1 a R5 vienen de la sección 3.4.5. R6 a R9 aparecieron al pasar al diseño de despliegue y al código. **La columna "Evidencia" es lo que vuelve operativa la norma**: un riesgo sin control verificable es solo una cita.

| ID | Riesgo | Prob. | Impacto | Tratamiento | Evidencia en el repo |
|---|---|---|---|---|---|
| R1 | Datos insuficientes o de baja calidad | Alta | Alto | Contratos de datos; documentar limitaciones | `procesamiento/contratos.py`; model card §6 |
| R2 | Sesgo por segmento o zona subrepresentada | Media | Medio | Error estratificado por segmento | _pendiente: `ml/evaluacion.py` por segmento_ |
| R3 | Degradación (data o concept drift) | Media | Alto | Reentrenamiento semestral; umbral de alerta | `dags/reentrenamiento.py`; ADR-0008 pendiente |
| R4 | Uso fuera del rango válido | Media | Medio | Rango de uso en la model card | model card §1 |
| R5 | Exposición de PII | Media | Alto | Seudonimización antes de Curated; nada de datos en git | `procesamiento/anonimizacion.py`; `.gitignore`; pre-commit; CI |
| R6 | Fuga temporal en la validación | Alta si no se controla | Alto | Particiones por mes con aserción | `ml/walk_forward.py`; `tests/unit/test_walk_forward.py` |
| R7 | Escape del contenedor vía la API de Docker | Baja | Alto | Proxy del socket con endpoints mínimos | ADR-0002 |
| R8 | Pérdida de reproducibilidad por `VACUUM` | Media | Alto | Retención de 3650 días | `comun/lakehouse.py`; ADR-0006 |
| R9 | Retiro de JSON-RPC/XML-RPC en Odoo | Alta (2027-2028) | Alto | Elegir JSON-2 o un endpoint propio | ADR-0005 |
