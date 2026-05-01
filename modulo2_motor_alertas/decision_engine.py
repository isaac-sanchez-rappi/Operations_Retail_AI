import pandas as pd
import numpy as np
import logging

# ===================================================
# DECISION ENGINE (EARNINGS OPTIMIZATION)
# ===================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger("decision_engine")

# ===================================================
# CONSTANTES DE NEGOCIO
# ===================================================
RATIO_TARGET = 1.2
RATIO_HIGH   = 1.8
RATIO_CRIT   = 2.5
RATIO_LOW    = 0.5

MIN_ORDERS = 4
REACTION_TIME_MIN = 30


# ===================================================
# CLASIFICACIÓN DE SEVERIDAD
# ===================================================
def classify_severity(ratio: float):

    if ratio >= RATIO_CRIT:
        return "CRÍTICO"
    elif ratio >= RATIO_HIGH:
        return "ALTO"
    elif ratio >= 1.4:
        return "MEDIO"
    elif ratio < RATIO_LOW:
        return "SOBREOFERTA"
    else:
        return "BAJO"


# ===================================================
# FUNCIÓN PRINCIPAL
# ===================================================
def decision_engine(
    df_predictions: pd.DataFrame,
    thresholds_df: pd.DataFrame,
    model,
    df_historical: pd.DataFrame
) -> pd.DataFrame:

    # ---------------------------------------------------
    # MERGE THRESHOLDS
    # ---------------------------------------------------
    df = df_predictions.merge(
        thresholds_df[["ZONE", "threshold_mm"]],
        on="ZONE",
        how="left"
    )

    df["threshold_mm"] = df["threshold_mm"].fillna(0.7)

    # ---------------------------------------------------
    # HISTÓRICO POR ZONA
    # ---------------------------------------------------
    hist_stats = df_historical.groupby("ZONE")["EARNINGS"].agg(
        min_earn="min",
        max_earn="max"
    ).reset_index()

    df = df.merge(hist_stats, on="ZONE", how="left")

    results = []

    # coeficientes modelo
    b0 = model.params["Intercept"]
    b1 = model.params["EARNINGS"]
    b2 = model.params["ORDERS"]
    b3 = model.params["PRECIPITATION_MM"]

    # ===================================================
    # ITERAR ZONAS
    # ===================================================
    for _, row in df.iterrows():

        zone = row["ZONE"]
        orders = float(row["ORDERS"])
        precip = float(row["PRECIPITATION_MM"])
        earnings = float(row["EARNINGS"])
        rt_pred = float(row["CONNECTED_RT_pred"])
        threshold = float(row["threshold_mm"])
        forecast_hour = row.get("target_3h", None)

        min_earn = row["min_earn"]
        max_earn = row["max_earn"]

        # ---------------------------------------------------
        # GUARD — BAJA DEMANDA
        # ---------------------------------------------------
        if orders < MIN_ORDERS:
            results.append(_skip(zone, "Baja demanda", earnings=earnings, orders=orders, rt_pred=rt_pred, precip=precip, forecast_hour=forecast_hour))
            continue

        # ---------------------------------------------------
        # RATIO
        # ---------------------------------------------------
        ratio = round(orders / max(rt_pred, 1), 2)
        severity = classify_severity(ratio)

        high_ratio = ratio >= RATIO_HIGH
        low_ratio  = ratio < RATIO_LOW
        rain_risk  = precip >= threshold

        # ---------------------------------------------------
        # DECISIÓN
        # ---------------------------------------------------
        if low_ratio:
            action = "BAJAR_EARNINGS"
            should_act = True

        elif high_ratio or rain_risk:
            action = "SUBIR_EARNINGS"
            should_act = True

        else:
            action = "NO_ACTION"
            should_act = False

        # ---------------------------------------------------
        # CALCULAR EARNINGS ÓPTIMO
        # ---------------------------------------------------
        rt_needed = orders / RATIO_TARGET

        earn_opt = (rt_needed - b0 - b2 * orders - b3 * precip) / b1
        earn_opt = max(0, earn_opt)

        # ---------------------------------------------------
        # CONTROL POR HISTÓRICO
        # ---------------------------------------------------
        if pd.notna(min_earn) and earn_opt < min_earn:
            logger.info(f"[{zone}] earn_opt < min histórico → NO_ACTION")
            earn_opt = earnings
            should_act = False
            action = "NO_ACTION"

        if pd.notna(max_earn):
            cap = max_earn * 1.10  # 🆕 +10%
            if earn_opt > cap:
                logger.info(f"[{zone}] cap aplicado ({cap})")
                earn_opt = cap

        delta = round(earn_opt - earnings, 1)

        # ---------------------------------------------------
        # EVITAR RUIDO
        # ---------------------------------------------------
        if abs(delta) < 2:
            should_act = False
            action = "NO_ACTION"

        # ---------------------------------------------------
        # LOG
        # ---------------------------------------------------
        logger.info(
            f"[{zone}] ratio={ratio} | rain={precip} | action={action}"
        )

        # ---------------------------------------------------
        # OUTPUT
        # ---------------------------------------------------
        results.append({
            "ZONE": zone,
            "forecast_hour": forecast_hour,
            "orders_forecast": orders,
            "rt_predicted": rt_pred,
            "ratio": ratio,
            "severity": severity,
            "precipitation": precip,
            "rain_threshold": threshold,
            "rain_risk": rain_risk,
            "earn_current": earnings,
            "earn_needed": round(earn_opt, 1),
            "delta_earnings": delta,
            "action": action,
            "should_act": should_act,
            "action_window_min": REACTION_TIME_MIN,
            "skip_reason": ""
        })

    return pd.DataFrame(results)


# ===================================================
# HELPER
# ===================================================
def _skip(zone, reason, earnings=None, orders=None, rt_pred=None, precip=None, forecast_hour=None):

    return {
        "ZONE": zone,
        "forecast_hour": forecast_hour,
        "orders_forecast": orders,
        "rt_predicted": rt_pred,
        "ratio": None,
        "severity": "N/A",
        "precipitation": precip,
        "rain_threshold": None,
        "rain_risk": None,
        "earn_current": earnings,
        "earn_needed": None,
        "delta_earnings": None,
        "action": "No accionar",
        "should_act": False,
        "action_window_min": None,
        "skip_reason": reason
    }