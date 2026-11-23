"""Utilidades de la exploración del experimento A (solo histórico de ventas).

Las usan los notebooks 02 a 06; no es código de producción. Reutiliza las funciones del
paquete (rezagos, calendario, particiones, catálogo y métricas) para que los resultados sean
comparables con la corrida oficial. Lo que agrega es la propuesta para `ml/`: métricas por
segmento, escala relativa, un modelo por segmento y ajuste anidado. Si se adopta, se mueve a
`src/lojagas/` con sus tests (regla de notebooks/README.md).
"""

from __future__ import annotations

import os
import urllib.request
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet, Lasso, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from lojagas.comun import lakehouse
from lojagas.comun.trazabilidad import etiquetas_corrida
from lojagas.ml import metricas
from lojagas.ml.modelos.catalogo import BASELINES, CATALOGO, crear
from lojagas.ml.walk_forward import particiones
from lojagas.procesamiento.temporales import calendario, rezagos

HORIZONTE = 2  # ADR-0014 (provisional): con datos hasta M−1 se predice M+1
LAGS = (2, 3, 12)  # elegidos en el notebook 03 (autocorrelación por segmento)
MIN_ENTRENAMIENTO = 12
SEMILLA = 42

TABLA_VENTAS = "ventas_mensual"
TABLA_CLIENTES = "clientes_activos_mensual"
TABLA_DIAS = "actividad_dia_semana"
DIAS_MES_MEDIO = 30.4375
TABLA_PREDICCIONES = "exp_a_walk_forward"
TABLA_AJUSTE = "exp_a_ajuste_anidado"
EXPERIMENTO_MLFLOW = "exploracion_a"

CLAVES = ["modelo", "modo", "escala"]
REFERENCIA = ("estacional_ingenuo", "referencia", "toneladas")
LINEALES = ("lasso", "ridge", "elastic_net")
MODELOS = tuple(n for n in CATALOGO if n not in BASELINES)


# --- Datos -------------------------------------------------------------------------------


def raiz_lakehouse() -> Path:
    """Lakehouse de exploración, fuera del repo: tablas agregadas, sin PII.

    Cuando exista el Curated real (ingesta + curación), basta apuntar
    `LOJAGAS_LAKEHOUSE_EXP` a ese lakehouse: los notebooks 03 a 06 no cambian.
    """
    if "LOJAGAS_LAKEHOUSE_EXP" in os.environ:
        return Path(os.environ["LOJAGAS_LAKEHOUSE_EXP"]).expanduser()
    entrada = Path(os.environ["LOJAGAS_DATOS_ENTRADA"]).expanduser()
    return entrada.parent / "trabajo" / "lakehouse"


def cargar_serie() -> pd.DataFrame:
    """Serie mensual por segmento (toneladas) y, si existe, clientes activos."""
    raiz = raiz_lakehouse()
    claves = ["mes", "segmento"]
    serie = lakehouse.leer(raiz, "curated", TABLA_VENTAS)[[*claves, "toneladas"]]
    if lakehouse.ruta_tabla(raiz, "curated", TABLA_CLIENTES).exists():
        clientes = lakehouse.leer(raiz, "curated", TABLA_CLIENTES)[[*claves, "clientes_activos"]]
        serie = serie.merge(clientes, on=claves, how="left", validate="one_to_one")
    serie["mes"] = pd.to_datetime(serie["mes"]).astype("datetime64[ns]")
    serie["dias_equiv"] = dias_equivalentes(serie, cargar_pesos_dias())
    return serie.sort_values(["segmento", "mes"]).reset_index(drop=True)


def cargar_pesos_dias() -> pd.DataFrame | None:
    """Actividad relativa de cada día de la semana por segmento (media 1), si existe la tabla."""
    raiz = raiz_lakehouse()
    if not lakehouse.ruta_tabla(raiz, "curated", TABLA_DIAS).exists():
        return None
    return lakehouse.leer(raiz, "curated", TABLA_DIAS)[["segmento", "dia_semana", "peso"]]


def dias_equivalentes(serie: pd.DataFrame, pesos: pd.DataFrame | None) -> pd.Series:
    """Días de venta de cada mes: sus días, ponderados por la actividad del día de la semana.

    Es calendario puro: se conoce de antemano para cualquier mes. Sin tabla de pesos, todos
    los días valen 1 y el resultado es el número de días del mes.
    """
    por_segmento = {}
    if pesos is not None:
        tabla = pesos.pivot_table(index="segmento", columns="dia_semana", values="peso")
        por_segmento = {s: fila.reindex(range(7)).to_numpy() for s, fila in tabla.iterrows()}
    uniforme = np.ones(7)
    conteos = {
        mes: np.bincount(pd.date_range(mes, mes + pd.offsets.MonthEnd(0)).day_of_week, minlength=7)
        for mes in pd.to_datetime(serie["mes"]).unique()
    }
    return pd.Series(
        [
            float(conteos[mes] @ por_segmento.get(segmento, uniforme))
            for mes, segmento in zip(pd.to_datetime(serie["mes"]), serie["segmento"], strict=True)
        ],
        index=serie.index,
    )


def construir(
    serie: pd.DataFrame, horizonte: int = HORIZONTE, lags: tuple[int, ...] = LAGS
) -> pd.DataFrame:
    """Variables de la configuración A. La fila del mes t usa solo meses ≤ t − horizonte."""
    df = calendario(rezagos(serie, horizonte=horizonte, lags=lags, ventanas=(3, 12)))
    mes = df["mes"].dt.month
    # Segundo armónico: un solo seno/coseno no representa dos picos al año
    df["mes_sin2"] = np.sin(4 * np.pi * mes / 12)
    df["mes_cos2"] = np.cos(4 * np.pi * mes / 12)
    df["t"] = (df["mes"].dt.year - df["mes"].dt.year.min()) * 12 + mes - 1
    # Escala relativa: todo se divide por el nivel del último año cerrado, así los
    # segmentos quedan comparables y el target es estable aunque haya tendencia.
    df["nivel"] = df["media_12"]
    for col in [*(f"lag_{k}" for k in lags), "media_3"]:
        df[f"{col}_rel"] = df[col] / df["nivel"]
    df["y_rel"] = df["toneladas"] / df["nivel"]
    if "dias_equiv" not in df.columns:
        df["dias_equiv"] = df["mes"].dt.days_in_month.astype(float)
    # Días de venta del mes: calendario, conocido de antemano (no es un rezago)
    df["dias_rel"] = df["dias_equiv"] / DIAS_MES_MEDIO
    df["ratio_dias_12"] = df["dias_equiv"] / df.groupby("segmento")["dias_equiv"].shift(12)
    df["estacional_dias"] = df["lag_12"] * df["ratio_dias_12"]
    if "clientes_activos" in df.columns:
        clientes = df.groupby("segmento")["clientes_activos"]
        df["clientes_lag"] = clientes.shift(horizonte)
        nivel_clientes = clientes.transform(lambda s: s.shift(horizonte).rolling(12).mean())
        df["clientes_rel"] = df["clientes_lag"] / nivel_clientes
    return df


def variables(escala: str, lags: tuple[int, ...] = LAGS, con_clientes: bool = False) -> list[str]:
    """Variables de entrada según la escala del target."""
    estacion = ["mes_sin", "mes_cos", "mes_sin2", "mes_cos2"]
    if escala == "toneladas":
        cols = [f"lag_{k}" for k in lags] + ["media_3", "media_12", "t", "dias_equiv"] + estacion
        return cols + (["clientes_lag"] if con_clientes else [])
    if escala == "relativa":
        cols = [f"lag_{k}_rel" for k in lags] + ["media_3_rel", "dias_rel"] + estacion
        return cols + (["clientes_rel"] if con_clientes else [])
    raise ValueError(f"Escala inválida: {escala}")


def _todas_las_variables(df: pd.DataFrame, lags: tuple[int, ...]) -> list[str]:
    candidatas = {*variables("toneladas", lags, True), *variables("relativa", lags, True)}
    return sorted(candidatas & set(df.columns))


def tabla_modelado(
    serie: pd.DataFrame, horizonte: int = HORIZONTE, lags: tuple[int, ...] = LAGS
) -> pd.DataFrame:
    """Filas con todas las variables disponibles: las mismas para todos los modelos."""
    df = construir(serie, horizonte, lags)
    necesarias = ["toneladas", "y_rel", "nivel", "estacional_dias", *_todas_las_variables(df, lags)]
    return df.dropna(subset=necesarias).sort_values(["mes", "segmento"]).reset_index(drop=True)


def verificar_sin_fuga(
    serie: pd.DataFrame, horizonte: int = HORIZONTE, lags: tuple[int, ...] = LAGS
) -> int:
    """Falla si una variable del mes t cambia al alterar los meses posteriores a t − horizonte.

    Devuelve el número de meses comprobados.
    """
    base = construir(serie, horizonte, lags).set_index(["segmento", "mes"]).sort_index()
    cols = ["nivel", *_todas_las_variables(base, lags)]
    medidas = [c for c in ("toneladas", "clientes_activos") if c in serie.columns]
    meses = np.sort(serie["mes"].unique())
    for mes in meses:
        alterada = serie.astype(dict.fromkeys(medidas, float))
        no_cerrados = alterada["mes"] > pd.Timestamp(mes) - pd.DateOffset(months=horizonte)
        alterada.loc[no_cerrados, medidas] = alterada.loc[no_cerrados, medidas] * 7.0 + 1.0
        nueva = construir(alterada, horizonte, lags).set_index(["segmento", "mes"]).sort_index()
        antes = base.xs(mes, level="mes")[cols].to_numpy(dtype=float)
        despues = nueva.xs(mes, level="mes")[cols].to_numpy(dtype=float)
        if not np.allclose(antes, despues, equal_nan=True):
            raise AssertionError(f"Fuga temporal en las variables de {pd.Timestamp(mes):%Y-%m}")
    return len(meses)


# --- Modelos -----------------------------------------------------------------------------


class Columna(RegressorMixin, BaseEstimator):
    """Referencia sin aprendizaje: predice el valor de una columna (p. ej., la media de 12)."""

    def __init__(self, columna: str = "media_12"):
        self.columna = columna

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return X[self.columna].to_numpy(dtype=float)


def _lineal(regresor) -> TransformedTargetRegressor:
    """Estandariza variables y target: la penalización significa lo mismo en toneladas y en
    escala relativa. Con el target sin estandarizar, el alpha del catálogo no penaliza nada
    en toneladas y anula todos los coeficientes en escala relativa."""
    return TransformedTargetRegressor(
        regressor=make_pipeline(StandardScaler(), regresor), transformer=StandardScaler()
    )


def crear_modelo(nombre: str, horizonte: int = HORIZONTE):
    """Modelo del catálogo con sus parámetros; a los lineales se les estandariza el target."""
    modelo = crear(nombre, horizonte)
    if "n_jobs" in modelo.get_params():
        # Con tan pocas filas, un hilo es lo más rápido. LightGBM usa por defecto todos los
        # núcleos físicos y, con varios procesos a la vez, se estorban entre sí.
        modelo.set_params(n_jobs=1)
    if nombre in LINEALES:
        return TransformedTargetRegressor(regressor=modelo, transformer=StandardScaler())
    return modelo


def _xgboost(t):
    from xgboost import XGBRegressor

    return XGBRegressor(
        n_estimators=t.suggest_int("n_estimators", 50, 300, step=50),
        max_depth=t.suggest_int("max_depth", 2, 4),
        learning_rate=t.suggest_float("learning_rate", 0.01, 0.2, log=True),
        subsample=t.suggest_float("subsample", 0.6, 1.0),
        min_child_weight=t.suggest_int("min_child_weight", 1, 5),
        reg_lambda=t.suggest_float("reg_lambda", 0.1, 10.0, log=True),
        random_state=SEMILLA,
        n_jobs=1,
    )


def _lightgbm(t):
    from lightgbm import LGBMRegressor

    return LGBMRegressor(
        n_estimators=t.suggest_int("n_estimators", 50, 300, step=50),
        num_leaves=t.suggest_int("num_leaves", 2, 8),
        learning_rate=t.suggest_float("learning_rate", 0.01, 0.2, log=True),
        min_child_samples=t.suggest_int("min_child_samples", 2, 8),
        reg_lambda=t.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
        random_state=SEMILLA,
        n_jobs=1,
        verbose=-1,
    )


# Espacios de búsqueda: cada entrada recibe un `trial` de Optuna y devuelve un modelo nuevo
ESPACIOS: dict[str, Callable] = {
    "ridge": lambda t: _lineal(Ridge(alpha=t.suggest_float("alpha", 1e-2, 1e3, log=True))),
    "lasso": lambda t: _lineal(
        Lasso(
            alpha=t.suggest_float("alpha", 1e-3, 1.0, log=True),
            max_iter=10_000,
            random_state=SEMILLA,
        )
    ),
    "elastic_net": lambda t: _lineal(
        ElasticNet(
            alpha=t.suggest_float("alpha", 1e-3, 1.0, log=True),
            l1_ratio=t.suggest_float("l1_ratio", 0.1, 0.9),
            max_iter=10_000,
            random_state=SEMILLA,
        )
    ),
    "random_forest": lambda t: RandomForestRegressor(
        n_estimators=300,
        max_depth=t.suggest_int("max_depth", 2, 6),
        min_samples_leaf=t.suggest_int("min_samples_leaf", 1, 5),
        max_features=t.suggest_float("max_features", 0.3, 1.0),
        random_state=SEMILLA,
    ),
    "xgboost": _xgboost,
    "lightgbm": _lightgbm,
}

# Los valores del catálogo son el primer intento de cada estudio: el ajuste nunca parte peor
PREDETERMINADOS: dict[str, dict] = {
    "ridge": {"alpha": 1.0},
    "lasso": {"alpha": 0.1},
    "elastic_net": {"alpha": 0.1, "l1_ratio": 0.5},
    "random_forest": {"max_depth": 4, "min_samples_leaf": 3, "max_features": 1.0},
    "xgboost": {
        "n_estimators": 300,
        "max_depth": 3,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "min_child_weight": 1,
        "reg_lambda": 1.0,
    },
    "lightgbm": {
        "n_estimators": 300,
        "num_leaves": 8,
        "learning_rate": 0.05,
        "min_child_samples": 5,
        "reg_lambda": 1e-3,
    },
}


_ENTEROS = {
    "n_estimators",
    "max_depth",
    "min_child_weight",
    "num_leaves",
    "min_child_samples",
    "min_samples_leaf",
}


def modelo_con(nombre: str, parametros: dict):
    """Modelo del espacio de búsqueda con hiperparámetros dados (los elegidos en un estudio)."""
    import optuna

    limpios = {k: int(v) if k in _ENTEROS else float(v) for k, v in parametros.items()}
    return ESPACIOS[nombre](optuna.trial.FixedTrial(limpios))


# --- Evaluación --------------------------------------------------------------------------


def matrices(datos: pd.DataFrame, features: list[str], modo: str, escala: str):
    """X, target y factor para volver a toneladas."""
    if modo not in ("conjunto", "por_segmento"):
        raise ValueError(f"Modo inválido: {modo}")
    X = datos[features].astype(float)
    if modo == "conjunto":
        X = X.join(pd.get_dummies(datos["segmento"], prefix="seg", dtype=float))
    if escala == "relativa":
        return X, datos["y_rel"], datos["nivel"]
    return X, datos["toneladas"], pd.Series(1.0, index=datos.index)


def grupos(segmentos: np.ndarray, idx: np.ndarray, modo: str) -> list[tuple[str, np.ndarray]]:
    """Subconjuntos de filas que comparten modelo: todas, o las de cada segmento."""
    if modo == "conjunto":
        return [("todos", idx)]
    return [(s, idx[segmentos[idx] == s]) for s in sorted(set(segmentos[idx]))]


def _filas(datos, fold, tr, te, pred) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "fold": fold,
            "mes": datos["mes"].to_numpy()[te],
            "segmento": datos["segmento"].to_numpy()[te],
            "n_entrenamiento": datos["mes"].iloc[tr].nunique(),
            "y": datos["toneladas"].to_numpy()[te],
            "pred": pred,
        }
    )


def _etiquetar(pred: pd.DataFrame, nombre: str, modo: str, escala: str) -> pd.DataFrame:
    pred.insert(0, "escala", escala)
    pred.insert(0, "modo", modo)
    pred.insert(0, "modelo", nombre)
    return pred


def evaluar(
    nombre: str,
    datos: pd.DataFrame,
    *,
    modo: str = "conjunto",
    escala: str = "toneladas",
    features: list[str] | None = None,
    fabrica: Callable | None = None,
    horizonte: int = HORIZONTE,
    min_entrenamiento: int = MIN_ENTRENAMIENTO,
) -> pd.DataFrame:
    """Walk-forward con horizonte. Una fila por mes de prueba y segmento, en toneladas.

    `datos` es la salida de `tabla_modelado`. `fabrica` devuelve un modelo nuevo; por
    defecto, el del catálogo.
    """
    features = features or variables(escala)
    X, objetivo, factor = matrices(datos, features, modo, escala)
    fabrica = fabrica or (lambda: crear_modelo(nombre, horizonte))
    segmentos = datos["segmento"].to_numpy()
    partes = []
    folds = particiones(datos["mes"], min_entrenamiento, horizonte=horizonte)
    for fold, (tr, te) in enumerate(folds):
        pred = pd.Series(np.nan, index=te)
        for grupo, g_te in grupos(segmentos, te, modo):
            g_tr = tr if grupo == "todos" else tr[segmentos[tr] == grupo]
            modelo = fabrica()
            modelo.fit(X.iloc[g_tr], objetivo.iloc[g_tr])
            pred[g_te] = modelo.predict(X.iloc[g_te])
        partes.append(_filas(datos, fold, tr, te, pred.to_numpy() * factor.to_numpy()[te]))
    return _etiquetar(pd.concat(partes, ignore_index=True), nombre, modo, escala)


def evaluar_referencias(datos: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """Referencias sin aprendizaje: ingenuo (t−h), estacional ingenuo (t−12), media de los
    últimos 12 meses cerrados y estacional ingenuo ajustado por los días de venta del mes."""
    horizonte = kwargs.get("horizonte", HORIZONTE)
    cols = sorted({f"lag_{horizonte}", "lag_12", "media_12", "estacional_dias"})
    partes = [
        evaluar("ingenuo", datos, features=cols, **kwargs),
        evaluar("estacional_ingenuo", datos, features=cols, **kwargs),
        *(
            evaluar(c, datos, features=cols, fabrica=lambda c=c: Columna(c), **kwargs)
            for c in ("media_12", "estacional_dias")
        ),
    ]
    return pd.concat(partes, ignore_index=True).assign(modo="referencia")


def _wape_interno(fabrica, X, objetivo, factor, datos, idx, horizonte, pliegues) -> float:
    """WAPE (promedio de los segmentos, en toneladas) de un walk-forward dentro de `idx`."""
    meses = datos["mes"].iloc[idx]
    minimo = meses.nunique() - pliegues - (horizonte - 1)
    if minimo < 4:
        raise ValueError(f"Muy pocos meses para {pliegues} pliegues internos")
    segmentos = datos["segmento"].to_numpy()
    partes = []
    for tr, te in particiones(meses, minimo, horizonte=horizonte):
        tr, te = idx[tr], idx[te]
        modelo = fabrica()
        modelo.fit(X.iloc[tr], objetivo.iloc[tr])
        a_toneladas = factor.to_numpy()[te]
        partes.append(
            pd.DataFrame(
                {
                    "segmento": segmentos[te],
                    "y": objetivo.to_numpy()[te] * a_toneladas,
                    "pred": modelo.predict(X.iloc[te]) * a_toneladas,
                }
            )
        )
    tabla = pd.concat(partes, ignore_index=True)
    return float(np.mean([metricas.wape(g["y"], g["pred"]) for _, g in tabla.groupby("segmento")]))


def _estudio(nombre, X, objetivo, factor, datos, g_tr, g_te, horizonte, pliegues, n_trials):
    """Un estudio de Optuna para un grupo de una partición: predicción e hiperparámetros."""
    import warnings

    import optuna
    from sklearn.exceptions import ConvergenceWarning

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    warnings.filterwarnings("ignore", category=ConvergenceWarning)
    espacio = ESPACIOS[nombre]

    def error_interno(trial):
        return _wape_interno(
            lambda: espacio(trial), X, objetivo, factor, datos, g_tr, horizonte, pliegues
        )

    estudio = optuna.create_study(
        direction="minimize", sampler=optuna.samplers.TPESampler(seed=SEMILLA)
    )
    estudio.enqueue_trial(PREDETERMINADOS[nombre])
    estudio.optimize(error_interno, n_trials=n_trials)
    modelo = espacio(optuna.trial.FixedTrial(estudio.best_params))
    modelo.fit(X.iloc[g_tr], objetivo.iloc[g_tr])
    return modelo.predict(X.iloc[g_te]), {**estudio.best_params, "wape_interno": estudio.best_value}


def ajustar_anidado(
    nombre: str,
    datos: pd.DataFrame,
    *,
    modo: str,
    escala: str,
    n_trials: int = 20,
    pliegues: int = 4,
    features: list[str] | None = None,
    horizonte: int = HORIZONTE,
    min_entrenamiento: int = MIN_ENTRENAMIENTO,
    n_jobs: int = -1,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Como `evaluar`, pero en cada partición los hiperparámetros se eligen con Optuna usando
    solo sus meses de entrenamiento (walk-forward interno con el mismo horizonte).

    Cada partición es independiente, así que los estudios se reparten entre procesos.
    Devuelve las predicciones y los hiperparámetros elegidos en cada partición.
    """
    from joblib import Parallel, delayed

    features = features or variables(escala)
    X, objetivo, factor = matrices(datos, features, modo, escala)
    segmentos = datos["segmento"].to_numpy()
    folds = list(particiones(datos["mes"], min_entrenamiento, horizonte=horizonte))
    tareas = [
        (fold, grupo, tr if grupo == "todos" else tr[segmentos[tr] == grupo], g_te)
        for fold, (tr, te) in enumerate(folds)
        for grupo, g_te in grupos(segmentos, te, modo)
    ]
    # Los procesos de joblib tienen que poder importar este módulo
    aqui = str(Path(__file__).parent)
    os.environ["PYTHONPATH"] = os.pathsep.join(filter(None, [aqui, os.environ.get("PYTHONPATH")]))
    resultados = Parallel(n_jobs=n_jobs)(
        delayed(_estudio)(
            nombre, X, objetivo, factor, datos, g_tr, g_te, horizonte, pliegues, n_trials
        )
        for _, _, g_tr, g_te in tareas
    )
    pred = pd.Series(np.nan, index=datos.index)
    elegidos = []
    for (fold, grupo, _, g_te), (estimado, parametros) in zip(tareas, resultados, strict=True):
        pred[g_te] = estimado
        elegidos.append({"fold": fold, "grupo": grupo, **parametros})
    partes = [
        _filas(datos, fold, tr, te, pred.to_numpy()[te] * factor.to_numpy()[te])
        for fold, (tr, te) in enumerate(folds)
    ]
    salida = _etiquetar(pd.concat(partes, ignore_index=True), f"{nombre}+ajuste", modo, escala)
    return salida, pd.DataFrame(elegidos)


# --- Métricas ----------------------------------------------------------------------------


def _fila_metricas(y, p) -> dict:
    y, p = np.asarray(y, float), np.asarray(p, float)
    sesgo = float((p.sum() - y.sum()) / y.sum() * 100)
    return {**metricas.calcular(y, p), "sesgo_pct": sesgo, "n": len(y)}


def resumir(pred: pd.DataFrame) -> pd.DataFrame:
    """Métricas por configuración y segmento, más TOTAL (la suma de los segmentos por mes)."""
    filas = []
    for clave, g in pred.groupby(CLAVES, sort=False):
        config = dict(zip(CLAVES, clave, strict=True))
        for segmento, gs in g.groupby("segmento"):
            filas.append({**config, "segmento": segmento, **_fila_metricas(gs["y"], gs["pred"])})
        total = g.groupby("mes")[["y", "pred"]].sum()
        filas.append({**config, "segmento": "TOTAL", **_fila_metricas(total["y"], total["pred"])})
    return pd.DataFrame(filas)


def comparar(pred: pd.DataFrame, referencia: tuple[str, str, str] = REFERENCIA) -> pd.DataFrame:
    """WAPE por segmento, macro (promedio de los segmentos) y TOTAL de cada configuración,
    con su mejora sobre la referencia en % (positiva = menos error)."""
    wape = resumir(pred).pivot_table(index=CLAVES, columns="segmento", values="wape", sort=False)
    segmentos = [c for c in wape.columns if c != "TOTAL"]
    wape["macro"] = wape[segmentos].mean(axis=1)
    wape = wape[[*segmentos, "macro", "TOTAL"]]
    mejora = metricas.mejora_relativa(wape, wape.loc[referencia])
    tabla = wape.join(mejora.add_prefix("mejora_"))
    tabla["segmentos_que_mejoran"] = (mejora[segmentos] > 0).sum(axis=1)
    return tabla.sort_values("macro")


def prueba_pareada(
    pred: pd.DataFrame, config: tuple[str, str, str], referencia: tuple[str, str, str] = REFERENCIA
) -> pd.DataFrame:
    """Wilcoxon pareado del error absoluto mensual, configuración frente a referencia.

    Una fila por segmento y otra para el TOTAL. Con una veintena de meses la prueba tiene
    poco poder: un p alto no demuestra que los dos modelos sean iguales.
    """
    from scipy.stats import wilcoxon

    def errores(clave):
        g = pred[(pred[CLAVES] == pd.Series(dict(zip(CLAVES, clave, strict=True)))).all(axis=1)]
        total = g.groupby("mes")[["y", "pred"]].sum().assign(segmento="TOTAL").reset_index()
        g = pd.concat([g[["mes", "segmento", "y", "pred"]], total], ignore_index=True)
        return (g["pred"] - g["y"]).abs().groupby([g["segmento"], g["mes"]]).sum()

    dif = (errores(referencia) - errores(config)).rename("ventaja")  # > 0: gana el modelo
    filas = []
    for segmento, d in dif.groupby(level="segmento"):
        p = wilcoxon(d).pvalue if (d != 0).any() else float("nan")
        filas.append(
            {
                "segmento": segmento,
                "meses": len(d),
                "meses_en_que_gana": int((d > 0).sum()),
                "ventaja_media_t": d.mean(),
                "p_wilcoxon": p,
            }
        )
    return pd.DataFrame(filas).set_index("segmento")


# --- Registro ----------------------------------------------------------------------------


def mlflow_disponible() -> str | None:
    """URI de MLflow si responde; si no, None y los notebooks siguen sin registrar."""
    uri = os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
    if not uri.startswith("http"):
        return uri
    try:
        urllib.request.urlopen(f"{uri}/health", timeout=3)
    except OSError:
        return None
    return uri


def _nombre_metrica(columna: str) -> str:
    if columna.startswith("mejora_"):
        return "mejora." + columna.removeprefix("mejora_")
    return columna if columna == "segmentos_que_mejoran" else f"wape.{columna}"


def registrar_mlflow(comparacion: pd.DataFrame, nombre: str, parametros: dict) -> str | None:
    """Registra una corrida por configuración (WAPE y mejoras) dentro de una corrida madre."""
    uri = mlflow_disponible()
    if uri is None:
        print("MLflow no responde: no se registró. Los resultados quedan en el lakehouse.")
        return None
    import mlflow

    mlflow.set_tracking_uri(uri)
    mlflow.set_experiment(EXPERIMENTO_MLFLOW)
    with mlflow.start_run(run_name=nombre) as madre:
        mlflow.set_tags(etiquetas_corrida())
        mlflow.log_params(parametros)
        for (modelo, modo, escala), fila in comparacion.iterrows():
            with mlflow.start_run(run_name=f"{modelo} | {modo} | {escala}", nested=True):
                mlflow.log_params({"modelo": modelo, "modo": modo, "escala": escala})
                mlflow.log_metrics(
                    {_nombre_metrica(k): float(v) for k, v in fila.items() if pd.notna(v)}
                )
    print(f"Registrado en MLflow ({EXPERIMENTO_MLFLOW}): {len(comparacion)} configuraciones")
    return madre.info.run_id


# --- Gráficos ----------------------------------------------------------------------------

TINTA, TINTA_SECUNDARIA, TENUE = "#0b0b0b", "#52514e", "#898781"
SUPERFICIE, REJILLA, EJE = "#fcfcfb", "#e1e0d9", "#c3c2b7"
# Tres primeros colores de la paleta categórica, en orden fijo (distinguibles con daltonismo)
AZUL, NARANJA, AGUA = "#2a78d6", "#eb6834", "#1baf7a"
_COLOR_SEGMENTO = {"domestico": AZUL, "industrial": NARANJA, "agroindustrial": AGUA}
_RESERVA = ["#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]


def estilo_graficos() -> None:
    """Estilo común: superficie clara fija, rejilla tenue, líneas de 2 px y texto en tinta."""
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "figure.facecolor": SUPERFICIE,
            "axes.facecolor": SUPERFICIE,
            "savefig.facecolor": SUPERFICIE,
            "figure.dpi": 110,
            "font.size": 9,
            "axes.edgecolor": EJE,
            "axes.linewidth": 1,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "axes.axisbelow": True,
            "grid.color": REJILLA,
            "grid.linewidth": 1,
            "grid.linestyle": "-",
            "axes.titlesize": 10,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.titlecolor": TINTA,
            "axes.labelcolor": TINTA_SECUNDARIA,
            "text.color": TINTA,
            "xtick.color": EJE,
            "ytick.color": EJE,
            "xtick.labelcolor": TINTA_SECUNDARIA,
            "ytick.labelcolor": TINTA_SECUNDARIA,
            "lines.linewidth": 2,
            "lines.solid_capstyle": "round",
            "lines.solid_joinstyle": "round",
            "legend.frameon": False,
        }
    )


def color_segmento(segmento: str, segmentos: list[str] | None = None) -> str:
    """El color sigue al segmento, no a su posición: es el mismo en todos los notebooks."""
    if segmento in _COLOR_SEGMENTO:
        return _COLOR_SEGMENTO[segmento]
    otros = sorted(s for s in (segmentos or [segmento]) if s not in _COLOR_SEGMENTO)
    return _RESERVA[otros.index(segmento) % len(_RESERVA)]
