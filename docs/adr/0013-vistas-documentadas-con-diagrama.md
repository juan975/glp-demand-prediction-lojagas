# 0013 — Vistas de arquitectura que se documentan con diagrama

**Estado:** Aceptado (nov 2026)

## Contexto

El documento del TIC describe la arquitectura con el modelo 4+1 de Kruchten, bajo ISO/IEC/IEEE 42010. El repositorio había reservado carpetas para casos de uso y para las vistas de procesos y de desarrollo, todas vacías. El director del TIC indicó que no hace falta modelar con diagramas todas las vistas, porque el artefacto es un sistema de datos y aprendizaje automático y no un producto de software de propósito general.

## Decisión

Se documentan con diagrama tres modelos: el mapa de capacidades, la vista lógica (diseño arquitectónico) y la vista de despliegue. Las vistas de procesos, de desarrollo y de escenarios se describen solo en texto en el documento del TIC. Se eliminan sus carpetas y se renumeran las restantes.

Las carpetas de modelo de datos, protección de datos, seguridad y pruebas se conservan después de las tres vistas, como documentación de soporte. No son vistas del 4+1.

## Consecuencias

- La 42010 no prescribe una notación gráfica para los modelos, pero el documento del TIC debe declarar explícitamente qué vistas son textuales y por qué. Sin esa declaración, el 4+1 parecería incompleto.
- El flujo de procesos se puede verificar directamente en `dags/`, y la correspondencia entre componentes, contenedores y código, en `docs/arquitectura/trazabilidad.md`.
- Si más adelante el director o el tribunal piden alguna de las vistas omitidas, se agrega como diagrama nuevo sin cambiar esta estructura.
