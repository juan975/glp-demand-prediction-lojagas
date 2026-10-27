"""«Contenedor ML» (Despliegue_v3).

- pipeline_entrenamiento.py → MLflow Tracking (HTTP 5000)
- evaluacion.py             → selección del candidato y SHAP; Model Registry
- predictor.py              → carga desde Model Registry; escribe en zona Predicciones
- generar_reportes.py       → lee Predicciones; escribe Excel/PDF en reportes/ (SMB)
"""
