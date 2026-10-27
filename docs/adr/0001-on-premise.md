# 0001 — Despliegue on-premise

**Estado:** Aceptado (oct 2026)

## Contexto
El dataset transaccional contiene PII: cédulas, RUC, nombres, coordenadas y números de cheque. La LOPDP (arts. 55-59) y la Res. SPDP-SPD-2026-0004-R regulan la transferencia internacional de datos personales. La carga es batch y de baja frecuencia (mensual y semestral), y el stack es open source y de un solo nodo.

## Decisión
Todo el procesamiento ocurre en un servidor on-premise que provee Lojagas: 256 GB de RAM, 64 núcleos y sin GPU.

## Alternativas descartadas
- **Nube pública:** implica transferencia internacional de PII y un costo recurrente injustificado para una carga mensual.

## Consecuencias
- La conformidad legal del hosting de Odoo (que está en la nube) es un asunto previo y queda fuera del alcance del TIC. La responsabilidad del TIC empieza en el punto de extracción.
- Sin GPU, la LSTM se entrena en CPU. Con aproximadamente 46 puntos por serie no es una limitación real.
- Lojagas opera el servidor: copias de respaldo de `${LOJAGAS_DATA_ROOT}`, parches del sistema operativo y acceso SSH.
