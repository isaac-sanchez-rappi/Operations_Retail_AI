import pandas as pd
import numpy as np 

# ===================================================
# WEATHER THRESHOLDS (LLUVIA → RIESGO)
# ===================================================

# ---------------------------------------------------
# 1. Preparar variables de riesgo
# ---------------------------------------------------
def build_risk_features(df: pd.DataFrame):
    """
    Calcula ratio e indicador de saturación.
    """

    df = df.copy()

    # ---------------------------------------------------
    # Crear datetime y ordenar
    # ---------------------------------------------------
    df["datetime"] = pd.to_datetime(df["DATE"]) + pd.to_timedelta(df["HOUR"], unit="h")
    df = df.sort_values(["ZONE", "datetime"])

    # ---------------------------------------------------
    # evitar división por cero
    # ---------------------------------------------------
    df["CONNECTED_RT"] = df["CONNECTED_RT"].replace(0, np.nan)

    df["RATIO"] = df["ORDERS"] / df["CONNECTED_RT"]

    # imputar ratios inválidos
    df["RATIO"] = df["RATIO"].fillna(0)

    # ---------------------------------------------------
    # Evento crítico
    # ---------------------------------------------------
    df["IS_SATURATED"] = (df["RATIO"] > 1.8).astype(int)

    return df


# ---------------------------------------------------
# 2. Crear bins de lluvia
# ---------------------------------------------------
def create_rain_bins(df: pd.DataFrame):
    """
    Genera niveles de lluvia usando cuantiles (qcut).

    Args:
        df (pd.DataFrame): dataset con precipitación

    Returns:
        pd.DataFrame: con columna rain_bin
    """

    df = df.copy()

    # baseline sin lluvia
    df["rain_bin"] = "no_rain"

    # máscara de lluvia
    mask = df["PRECIPITATION_MM"] > 0

    # aplicar qcut solo donde hay lluvia
    try:
        df.loc[mask, "rain_bin"] = pd.qcut(
            df.loc[mask, "PRECIPITATION_MM"],
            q=4,
            duplicates="drop"
        ).astype(str)

    except Exception:
        # fallback si qcut falla
        df.loc[mask, "rain_bin"] = "rain_generic"

    return df


# ---------------------------------------------------
# 3. Construir curva lluvia → riesgo
# ---------------------------------------------------
def build_rain_risk_curve(df: pd.DataFrame):
    """
    Calcula probabilidad de saturación por nivel de lluvia.

    Args:
        df (pd.DataFrame): dataset con rain_bin

    Returns:
        pd.DataFrame: curva de riesgo por zona
    """

    curve = df.groupby(["ZONE", "rain_bin"]).agg(
        prob_saturation=("IS_SATURATED", "mean"),
        count=("IS_SATURATED", "count")
    ).reset_index()

    # ---------------------------------------------------
    # FILTRO DE SOPORTE MÍNIMO
    # ---------------------------------------------------
    curve = curve[curve["count"] >= 1]

    # ---------------------------------------------------
    # Ordenar bins correctamente
    # ---------------------------------------------------
    def get_bin_start(x):
        if x == "no_rain":
            return 0
        if x == "rain_generic":
            return 0.1
        try:
            return float(x.split(",")[0].replace("(", "").replace("[", ""))
        except:
            return 0

    curve["order"] = curve["rain_bin"].apply(get_bin_start)

    curve = curve.sort_values(["ZONE", "order"])

    return curve


# ---------------------------------------------------
# 4. Calcular threshold por zona
# ---------------------------------------------------
def compute_rain_thresholds(curve: pd.DataFrame, threshold_prob: float = 0.20):
    """
    Determina el nivel de lluvia donde comienza el riesgo alto.

    Args:
        curve (pd.DataFrame): curva lluvia → riesgo
        threshold_prob (float): probabilidad mínima de saturación

    Returns:
        pd.DataFrame: thresholds por zona
    """

    thresholds = []

    for zone in curve["ZONE"].unique():

        temp = curve[curve["ZONE"] == zone]

        # ---------------------------------------------------
        # Encontrar primer punto donde supera el umbral
        # ---------------------------------------------------
        temp_thr = temp[temp["prob_saturation"] >= threshold_prob]

        if len(temp_thr) > 0:
            first = temp_thr.iloc[0]

            thresholds.append({
                "ZONE": zone,
                "threshold_bin": first["rain_bin"],
                "threshold_mm": first["order"], 
                "prob_saturation": first["prob_saturation"]
            })

        else:
            # fallback inteligente
            thresholds.append({
                "ZONE": zone,
                "threshold_bin": "no_risk_detected",
                "threshold_mm": 0.7,  # valor conservador
                "prob_saturation": 0.3
            })

    return pd.DataFrame(thresholds)