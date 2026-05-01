import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# ===================================================
# ORDERS FORECAST MODEL
# ===================================================

# ---------------------------------------------------
# Forecast por zona
# ---------------------------------------------------
def forecast_orders_per_zone(ts_zone: pd.DataFrame):
    """
    Aplica Holt-Winters para predecir órdenes a 1h y 3h.

    Args:
        ts_zone (pd.DataFrame): serie temporal de una zona

    Returns:
        tuple: (orders_1h, orders_3h)
    """

    # ---------------------------------------------------
    # Preparar serie
    # ---------------------------------------------------
    ts_zone = ts_zone.sort_values("datetime")
    ts_zone = ts_zone.set_index("datetime")

    # asegurar frecuencia horaria
    ts_zone = ts_zone.asfreq("h")

    # ---------------------------------------------------
    # IMPUTACIÓN DE VALORES FALTANTES
    # ---------------------------------------------------
    ts_zone["orders"] = ts_zone["orders"].interpolate(method="linear")
    ts_zone["orders"] = ts_zone["orders"].ffill()
    ts_zone["orders"] = ts_zone["orders"].bfill()

    y = ts_zone["orders"]

    # ---------------------------------------------------
    # CONTROL DE OUTLIERS BASE
    # ---------------------------------------------------
    p5 = y.quantile(0.05)
    p95 = y.quantile(0.95)

    # ---------------------------------------------------
    # CALCULAR HORIZONTES FUTUROS
    # ---------------------------------------------------
    last_timestamp = y.index[-1]

    t_plus_1 = last_timestamp + pd.Timedelta(hours=1)
    t_plus_3 = last_timestamp + pd.Timedelta(hours=3)

    hour_1h = t_plus_1.hour
    hour_3h = t_plus_3.hour

    # ---------------------------------------------------
    # FALLBACK POR SI HAY POCA DATA 
    # ---------------------------------------------------
    if len(y) < 48:

        df_temp = y.to_frame(name="orders")
        df_temp["hour"] = df_temp.index.hour

        def get_hour_avg(target_hour):
            same_hour_values = df_temp[df_temp["hour"] == target_hour]["orders"]

            if len(same_hour_values) > 0:
                return float(same_hour_values.mean())
            else:
                return float(df_temp["orders"].mean())

        f1 = get_hour_avg(hour_1h)
        f3 = get_hour_avg(hour_3h)

        f1 = max(0.0, f1)
        f3 = max(0.0, f3)

        # clipping
        f1 = min(max(f1, p5), p95)
        f3 = min(max(f3, p5), p95)

        return int(round(f1)), int(round(f3))

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
            optimized=False
        )

        # ---------------------------------------------------
        # Forecast
        # ---------------------------------------------------
        forecast = fit.forecast(3)

        f1 = float(forecast.iloc[0])
        f3 = float(forecast.iloc[2])

        # ---------------------------------------------------
        # CONTROL FINAL DE VALORES
        # ---------------------------------------------------
        f1 = max(0.0, f1)
        f3 = max(0.0, f3)

        f1 = min(max(f1, p5), p95)
        f3 = min(max(f3, p5), p95)

        return int(round(f1)), int(round(f3))

    except Exception:
        # ---------------------------------------------------
        # FALLBACK SI MODELO FALLA
        # ---------------------------------------------------
        df_temp = y.to_frame(name="orders")
        df_temp["hour"] = df_temp.index.hour

        def get_hour_avg(target_hour):
            same_hour_values = df_temp[df_temp["hour"] == target_hour]["orders"]

            if len(same_hour_values) > 0:
                return float(same_hour_values.mean())
            else:
                return float(df_temp["orders"].mean())

        f1 = get_hour_avg(hour_1h)
        f3 = get_hour_avg(hour_3h)

        f1 = max(0.0, f1)
        f3 = max(0.0, f3)

        f1 = min(max(f1, p5), p95)
        f3 = min(max(f3, p5), p95)

        return int(round(f1)), int(round(f3))


# ---------------------------------------------------
# Forecast para todas las zonas
# ---------------------------------------------------
def forecast_orders_all_zones(ts_orders: pd.DataFrame):
    """
    Genera forecast de órdenes para todas las zonas.

    Args:
        ts_orders (pd.DataFrame): time series completa

    Returns:
        pd.DataFrame: orders_1h y orders_3h por zona
    """

    
    results = []

    for zone, group in ts_orders.groupby("ZONE"):

        # ---------------------------------------------------
        # ASEGURAR ORDEN TEMPORAL  🆕
        # ---------------------------------------------------
        group = group.sort_values("datetime")

        # ---------------------------------------------------
        # DEFINIR TIEMPO BASE
        # ---------------------------------------------------
        now = group["datetime"].max()

        target_1h = now + pd.Timedelta(hours=1)
        target_3h = now + pd.Timedelta(hours=3)

        try:
            f1, f3 = forecast_orders_per_zone(group)

        except Exception:
            last_value = float(group["orders"].iloc[-1])
            f1, f3 = int(last_value), int(last_value)

        results.append({
            "ZONE": zone,
            "datetime_local": now,
            "target_1h": target_1h,
            "target_3h": target_3h,
            "orders_1h": f1,
            "orders_3h": f3
        })

    return pd.DataFrame(results)