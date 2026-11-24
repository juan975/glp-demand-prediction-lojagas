"""INAMHI: estaciones meteorológicas (nivel 3 del documento de fuentes v4).

No es una fuente del pipeline mensual y no entra al modelo. Sirve para validar ERA5-Land
(¿tiene sesgo frente a las estaciones de Loja y Zamora Chinchipe?) y, si hiciera falta, para
calcular una corrección que se aplicaría en Procesamiento.

La entrega de INAMHI en datosabiertos.gob.ec está cerrada a diciembre de 2019, así que la
validación es un análisis de una sola vez: notebooks/07_dv_validacion_era5_inamhi.ipynb, con
las estaciones de referencias/inamhi_estaciones.csv e inamhi_valores.csv (armadas con
scripts/inamhi_estaciones.py). Por eso no hay una clase `Fuente` aquí.
"""
