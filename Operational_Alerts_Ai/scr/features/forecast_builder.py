import pandas as pd
import logging

logger = logging.getLogger(__name__)  

# ===================================================
# FORECAST DATASET BUILDER
# ===================================================

# ---------------------------------------------------
# Construir dataset para predicción de RT
# ---------------------------------------------------
def build_rt_forecast_dataset(
    forecast_earnings_df: pd.DataFrame,
    forecast_orders_df: pd.DataFrame,
    weather_forecast_df: pd.DataFrame
):
    """
    Combina forecasts de earnings, orders y clima
    en un solo dataset listo para el modelo.

    Args:
        forecast_df: forecast de earnings
        forecast_orders_df: forecast de órdenes
        weather_forecast_df: forecast de lluvia

    Returns:
        pd.DataFrame: dataset listo para predicción
    """

    # ---------------------------------------------------
    # 🆕 VALIDAR UNICIDAD POR ZONA
    # ---------------------------------------------------
    if forecast_earnings_df["ZONE"].duplicated().any():
        logger.warning("Duplicados en forecast_earnings_df")

    if forecast_orders_df["ZONE"].duplicated().any():
        logger.warning("Duplicados en forecast_orders_df")

    if weather_forecast_df["ZONE"].duplicated().any():
        logger.warning("Duplicados en weather_forecast_df")

    # ---------------------------------------------------
    # BASE: usar earnings como referencia (todas las zonas)
    # ---------------------------------------------------
    df_future = forecast_earnings_df.copy()

    # ---------------------------------------------------
    # Merge de todas las fuentes (LEFT JOIN para no perder zonas)
    # ---------------------------------------------------
    df_future = (
        df_future
        .merge(
            forecast_orders_df[["ZONE", "orders_3h"]],
            on="ZONE",
            how="left"  # 🆕 evita perder zonas
        )
        .merge(
            weather_forecast_df[["ZONE", "precipitation_3h"]],
            on="ZONE",
            how="left"  # 🆕 evita perder zonas
        )
    )


    # ---------------------------------------------------
    # MANEJO DE NULOS
    # ---------------------------------------------------
    df_future["orders_3h"] = df_future["orders_3h"].fillna(0)
    df_future["precipitation_3h"] = df_future["precipitation_3h"].fillna(0)

    # ---------------------------------------------------
    # 🆕 VALIDACIÓN DE INTEGRIDAD
    # ---------------------------------------------------
    if df_future["ZONE"].nunique() != forecast_earnings_df["ZONE"].nunique():
        logger.warning("Pérdida de zonas en merge")

    # ---------------------------------------------------
    # 🆕 RESOLVER DUPLICADOS (CLAVE)
    # ---------------------------------------------------
    if df_future["ZONE"].duplicated().any():
        logger.warning("Resolviendo duplicados por zona usando max earnings")

        # ordenar por earnings descendente
        df_future = df_future.sort_values("earnings_3h", ascending=False)

        # quedarse con el mejor por zona
        df_future = df_future.drop_duplicates(subset=["ZONE"], keep="first")

    # ---------------------------------------------------
    # Renombrar columnas para el modelo
    # ---------------------------------------------------
    df_future = df_future.rename(columns={
        "earnings_3h": "EARNINGS",
        "orders_3h": "ORDERS",
        "precipitation_3h": "PRECIPITATION_MM"
    })

    # ---------------------------------------------------
    # SELECCIÓN FINAL
    # ---------------------------------------------------
    df_future = df_future[[
        "ZONE",
        "datetime_local",  
        "target_3h",       
        "EARNINGS",
        "ORDERS",
        "PRECIPITATION_MM"
    ]]

    return df_future