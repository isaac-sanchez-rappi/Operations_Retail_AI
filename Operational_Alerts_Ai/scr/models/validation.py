import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# ===================================================
# FORECAST VALIDATION (WALK-FORWARD)
# ===================================================

# ---------------------------------------------------
# 1. Calcular error MAE a 1h y 3h
# ---------------------------------------------------
def walk_forward_mae(series: pd.Series, train_frac: float = 0.75, n_eval: int = 50):
    """
    Evalúa desempeño del modelo usando walk-forward validation.

    Args:
        series (pd.Series): serie temporal (ordenada y con frecuencia horaria)
        train_frac (float): proporción usada para entrenamiento inicial
        n_eval (int): número máximo de evaluaciones

    Returns:
        tuple: (mae_1h, mae_3h)
    """

    # ---------------------------------------------------
    # Tamaño de la serie
    # ---------------------------------------------------
    n = len(series)

    # punto de corte de entrenamiento
    train_end = int(n * train_frac)

    # listas de errores
    e1, e3 = [], []

    # ---------------------------------------------------
    # Walk-forward validation
    # ---------------------------------------------------
    for i in range(train_end, min(n - 3, train_end + n_eval)):

        try:
            # entrenar solo con datos pasados
            model = ExponentialSmoothing(
                series.iloc[:i],
                trend='add',
                seasonal='add',
                seasonal_periods=24
            ).fit(
                smoothing_level=0.3,
                smoothing_trend=0.1,
                smoothing_seasonal=0.1,
                optimized=False
            )

            # forecast a 3 pasos
            forecast = model.forecast(3)

            # error t+1
            e1.append(abs(forecast.iloc[0] - series.iloc[i]))

            # error t+3
            e3.append(abs(forecast.iloc[2] - series.iloc[i + 2]))

        except:
            # ignorar errores puntuales
            pass

    return np.mean(e1), np.mean(e3)


# ---------------------------------------------------
# 2. Evaluar modelo por zona
# ---------------------------------------------------
def evaluate_forecast_by_zone(df: pd.DataFrame):
    """
    Calcula MAE a 1h y 3h para cada zona.

    Args:
        df (pd.DataFrame): datos con datetime y ZONE

    Returns:
        pd.DataFrame: métricas por zona
    """

    results = []

    for zone in df["ZONE"].unique():

        # ---------------------------------------------------
        # Construir serie temporal
        # ---------------------------------------------------
        series = (
            df[df["ZONE"] == zone]
            .groupby("datetime")["ORDERS"]
            .sum()
            .asfreq("h", fill_value=0)
        )

        # ---------------------------------------------------
        # Calcular errores
        # ---------------------------------------------------
        mae_1h, mae_3h = walk_forward_mae(series)

        results.append({
            "ZONE": zone,
            "MAE_1h": mae_1h,
            "MAE_3h": mae_3h
        })

    df_results = pd.DataFrame(results)

    # ---------------------------------------------------
    # Degradación del forecast
    # ---------------------------------------------------
    df_results["degradacion_pct"] = (
        (df_results["MAE_3h"] - df_results["MAE_1h"]) /
        df_results["MAE_1h"] * 100
    ).round(1)

    return df_results.sort_values("degradacion_pct", ascending=False)