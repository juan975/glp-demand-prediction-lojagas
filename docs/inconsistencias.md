# Backlog de inconsistencias

El backlog vive en los **issues de GitHub con la etiqueta `tesis`**. Este archivo ya no es una lista: solo explica cómo se usa.

- Cada inconsistencia entre el Word, los diagramas y el código es un issue. El título empieza con su identificador (`I-04`, `I-45`…), para que las referencias del Word, los ADR y este repositorio sigan siendo válidas.
- La prioridad va en las etiquetas `p0-bloqueante`, `p1-mayor` y `p2-menor`.
- Al cerrar un issue se anota el commit o la versión del Word que lo corrige.

Para verlas: `gh issue list --label tesis --state open`.

La versión anterior de esta lista (I-01 a I-32, sobre el `CuartoAvance.docx`) queda en el historial de git.
