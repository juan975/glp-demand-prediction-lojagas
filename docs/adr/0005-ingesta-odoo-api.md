# 0005 — Ingesta de Odoo por API

**Estado:** Propuesto. Bloqueado por la versión de Odoo.

## Contexto
Odoo está en la nube y Lojagas pidió que la ingesta sea por API. El diccionario `ventas_ml_dataset.md` se construyó con SQL directo sobre PostgreSQL. Esa consulta une modelos estándar (`account.move.line`, `res.partner`, `product.product`, `sale.order`) con modelos propios (`despacho_granelero`, `consumption_spreadsheet`, `loj_turns`, `remission_guide`).

Odoo 19 depreca XML-RPC y JSON-RPC (`/xmlrpc`, `/xmlrpc/2`, `/jsonrpc`) en favor de la API JSON-2, que autentica con una API key en un header bearer. Se eliminan en Odoo Online 21.1 (invierno de 2027) y en self-hosted u Odoo.sh con Odoo 22.

## Opciones
| | A. JSON-2 modelo por modelo | B. Endpoint o vista del lado de Odoo | C. Exportación programada (CSV/SFTP) |
|---|---|---|---|
| Esfuerzo propio | Alto: replicar todos los joins | Bajo | Bajo |
| Dependencia de Lojagas | Solo una API key | Desarrollo en su Odoo | Configurar el job |
| Fidelidad al diccionario | Riesgo de diferencias | Total | Total |
| Vida útil | Larga | Larga | Media |

## Preguntas para Lojagas
1. ¿Qué versión de Odoo usan y en qué hosting (Online, Odoo.sh o un tercero)?
2. ¿Pueden exponer un endpoint o una vista con la consulta del dataset (opción B)?
3. ¿Qué límites de tasa y paginación tiene su instancia?

## Decisión
Pendiente. Recomendación: **B**, con **A** como respaldo. B conserva la semántica que ya validaron en el diccionario de datos.
