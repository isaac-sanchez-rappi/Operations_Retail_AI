import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# ===================================================
# EARNINGS FORECAST MODEL
# ===================================================

# ---------------------------------------------------
# Forecast por zona
# ---------------------------------------------------
def forecast_earnings_per_zone(ts_zone: pd.DataFrame):
    """
    Aplica Holt-Winters para predecir earnings a 1h y 3h.

    Args:
        ts_zone (pd.DataFrame): serie temporal de una zona

    Returns:
        tuple: (forecast_1h, forecast_3h)
    """

    # ---------------------------------------------------
    # Preparar serie
    # ---------------------------------------------------
    ts_zone = ts_zone.sort_values("datetime")
    ts_zone = ts_zone.set_index("datetime")

    # asegurar frecuencia horaria
    ts_zone = ts_zone.asfreq("h")

    # ---------------------------------------------------
    # CONTROL DE OUTLIERS
    # ---------------------------------------------------
    p5 = y.quantile(0.05)
    p95 = y.quantile(0.95)

    # ---------------------------------------------------
    # IMPUTACIÓN DE VALORES FALTANTES
    # ---------------------------------------------------

    # interpolación lineal (rellena huecos intermedios)
    ts_zone["earnings"] = ts_zone["earnings"].interpolate(method="linear")

    # forward fill (por si quedan NaNs al final)
    ts_zone["earnings"] = ts_zone["earnings"].ffill()

    # backward fill (por si quedan NaNs al inicio)
    ts_zone["earnings"] = ts_zone["earnings"].bfill()

    y = ts_zone["earnings"]

    # ---------------------------------------------------
    # CALCULAR HORIZONTES FUTUROS
    # ---------------------------------------------------
    last_timestamp = y.index[-1]

    # horizontes futuros
    t_plus_1 = last_timestamp + pd.Timedelta(hours=1)
    t_plus_3 = last_timestamp + pd.Timedelta(hours=3)

    # extraer solo la hora (0–23)
    hour_1h = t_plus_1.hour
    hour_3h = t_plus_3.hour


    # ---------------------------------------------------
    # FALLBACK POR SI HAY POCA DATA)
    # ---------------------------------------------------
    if len(y) < 48:

        df_temp = y.to_frame(name="earnings")
        df_temp["hour"] = df_temp.index.hour

        def get_hour_avg(target_hour):
            same_hour_values = df_temp[df_temp["hour"] == target_hour]["earnings"]

            if len(same_hour_values) > 0:
                return float(same_hour_values.mean())
            else:
                return float(df_temp["earnings"].mean())

        f1 = get_hour_avg(hour_1h)
        f3 = get_hour_avg(hour_3h)
        
        f1 = max(0.0, f1)
        f3 = max(0.0, f3)

        f1 = min(max(f1, p5), p95)
        f3 = min(max(f3, p5), p95)

        return f1, f3

    # ---------------------------------------------------
    # Modelo Holt-Winters
    # ---------------------------------------------------
    try:
        model = ExponentialSmoothing(
            y,
            trend="add",
            seasonal="add",
            seasonal_periods=24
        )

        fit = model.fit(
            smoothing_level=0.3,
            smoothing_trend=0.1,
            smoothing_seasonal=0.1,
            optimized=False  # estabilidad
        )

        # ---------------------------------------------------
        # Forecast
        # ---------------------------------------------------
        forecast = fit.forecast(3)

        f1 = max(0.0, float(forecast.iloc[0]))
        f3 = max(0.0, float(forecast.iloc[2]))

        f1 = max(0.0, f1)
        f3 = max(0.0, f3)

        # clipping dinámico
        f1 = min(max(f1, p5), p95)
        f3 = min(max(f3, p5), p95)

        return f1, f3
    
    except Exception:
        # ---------------------------------------------------
        # FALLBACK SI MODELO FALLA
        # ---------------------------------------------------
        df_temp = y.to_frame(name="earnings")
        df_temp["hour"] = df_temp.index.hour

        def get_hour_avg(target_hour):
            same_hour_values = df_temp[df_temp["hour"] == target_hour]["earnings"]

            if len(same_hour_values) > 0:
                return float(same_hour_values.mean())
            else:
                return float(df_temp["earnings"].mean())

        f1 = get_hour_avg(hour_1h)
        f3 = get_hour_avg(hour_3h)

        f1 = max(0.0, f1)
        f3 = max(0.0, f3)

        f1 = min(max(f1, p5), p95)
        f3 = min(max(f3, p5), p95)

        return f1, f3


# ---------------------------------------------------
# Forecast para todas las zonas
# ---------------------------------------------------

def forecast_earnings_all_zones(ts: pd.DataFrame):
    """
    Genera forecast de earnings para todas las zonas.

    Args:
        ts (pd.DataFrame): time series completa

    Returns:
        pd.DataFrame: earnings_1h y earnings_3h por zona
    """

    results = []

    for zone, group in ts.groupby("ZONE"):

        # ---------------------------------------------------
        # ASEGURAR ORDEN TEMPORAL
        # ---------------------------------------------------
        group = group.sort_values("datetime")

        # ---------------------------------------------------
        # DEFINIR TIEMPO BASE
        # ---------------------------------------------------
        now = group["datetime"].max()

        target_1h = now + pd.Timedelta(hours=1)
        target_3h = now + pd.Timedelta(hours=3)

        try:
            f1, f3 = forecast_earnings_per_zone(group)

        except Exception:
            # fallback extremo (nunca romper pipeline)
            last_value = float(group["earnings"].iloc[-1])
            f1, f3 = last_value, last_value

        results.append({
            "ZONE": zone,
            "datetime_local": now,
            "target_1h": target_1h,
            "target_3h": target_3h,
            "earnings_1h": f1,
            "earnings_3h": f3
        })

    return pd.DataFrame(results)