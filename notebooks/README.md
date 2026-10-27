# notebooks/

Solo EDA y exploración. Convención: `NN_iniciales_tema.ipynb` (ej. `01_jc_eda_ventas.ipynb`).

- Se suben **sin salidas** (nbstripout lo hace en el pre-commit): una tabla impresa puede contener PII.
- Si algo de un notebook se va a reutilizar, se mueve a `src/lojagas/` con su test.
- Leen del lakehouse local con `lojagas.lakehouse.delta_io.leer(...)`, nunca de un CSV suelto.
