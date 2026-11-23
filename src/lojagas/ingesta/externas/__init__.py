"""Fuentes externas. Una clase por fuente; todas cumplen el protocolo `Fuente`.

Prioridad según Fuentes_Datos_Externos_Lojagas v4 (niveles de integración al modelo):
    Nivel 1 (features del modelo): ERA5-Land → calendario de eventos → Petroecuador precios
        (los stockouts también son nivel 1, pero vienen de Lojagas, no de una fuente externa)
    Nivel 2 (features derivadas): SIPA-MAG, INIAP, mapas de precipitación INAMHI
    Nivel 3 (validación cruzada, no entra al modelo): estaciones INAMHI → corrige sesgo de ERA5-Land
    Nivel 4: INEC, vías (MTOP, ECU911), CNEL
"""
