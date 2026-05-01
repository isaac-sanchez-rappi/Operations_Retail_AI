import pandas as pd
import statsmodels.formula.api as smf
import logging

logger = logging.getLogger(__name__)

# ===================================================
# RT MODEL (OLS)
# ===================================================

# ---------------------------------------------------
# Entrenar modelo de RT
# ---------------------------------------------------
def train_rt_model(df: pd.DataFrame):
    """
    Entrena modelo OLS para predecir CONNECTED_RT.

    Args:
        df (pd.DataFrame): datos históricos

    Returns:
        model: modelo entrenado
    """


    # ---------------------------------------------------
    # VALIDAR COLUMNAS
    # ---------------------------------------------------
    required_cols = ["CONNECTED_RT", "EARNINGS", "ORDERS", "PRECIPITATION_MM"]

    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Faltan columnas en training: {missing_cols}")
        raise ValueError(f"Faltan columnas en training: {missing_cols}")
    
    # ---------------------------------------------------
    # LIMPIEZA
    # ---------------------------------------------------
    df_model = df[required_cols].dropna()

    if df_model.empty:
        logger.error("Dataset vacío después de limpieza")
        raise ValueError("Dataset vacío después de limpieza")
    
    # ---------------------------------------------------
    # ENTRENAMIENTO
    # ---------------------------------------------------
    model = smf.ols(
        "CONNECTED_RT ~ EARNINGS + ORDERS + PRECIPITATION_MM",
        data=df_model
    ).fit()
    
    # ---------------------------------------------------
    # LOGGING DE MÉTRICAS
    # ---------------------------------------------------
    logger.info(f"RT Model trained | R2: {round(model.rsquared, 3)}")

    return model


# ---------------------------------------------------
# Predecir RT
# ---------------------------------------------------
def predict_rt(model, df_future: pd.DataFrame):
    """
    Predice CONNECTED_RT usando el modelo OLS y devuelve dataset completo enriquecido.

    Args:
        model: modelo entrenado
        df_future (pd.DataFrame): datos futuros

    Returns:
        pd.DataFrame: dataset completo con todas las predicciones
    """

    # ---------------------------------------------------
    # VALIDAR COLUMNAS
    # ---------------------------------------------------
    required_cols = ["EARNINGS", "ORDERS", "PRECIPITATION_MM"]

    missing_cols = [col for col in required_cols if col not in df_future.columns]
    if missing_cols:
        logger.error(f"Faltan columnas en predicción: {missing_cols}")
        raise ValueError(f"Faltan columnas en predicción: {missing_cols}")
    
    # ---------------------------------------------------
    # LIMPIEZA
    # ---------------------------------------------------
    df_future_clean = df_future.copy()

    for col in ["EARNINGS", "ORDERS", "PRECIPITATION_MM"]:
        mean_val = df_future_clean[col].mean()

        # si toda la columna es NaN → fallback a 0
        if pd.isna(mean_val):
            mean_val = 0

        df_future_clean[col] = df_future_clean[col].fillna(mean_val)

    # ---------------------------------------------------
    # PREDICCIÓN
    # ---------------------------------------------------
    prediction_time = pd.Timestamp.now()
    preds = model.predict(df_future_clean)

    # ---------------------------------------------------
    # CONTROL DE OUTLIERS
    # ---------------------------------------------------
    p5 = preds.quantile(0.05)
    p95 = preds.quantile(0.95)

    preds = preds.clip(lower=p5, upper=p95)

    # ---------------------------------------------------
    # LIMPIEZA FINAL
    # ---------------------------------------------------
    preds = preds.round().clip(lower=0).astype(int)

    # ---------------------------------------------------
    # OUTPUT COMPLETO
    # ---------------------------------------------------
    df_result = df_future.copy()

    df_result["CONNECTED_RT_pred"] = preds
    df_result["PREDICTION_DATETIME"] = prediction_time

    return df_result