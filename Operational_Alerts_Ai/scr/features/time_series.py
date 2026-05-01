import pandas as pd

# ===================================================
# TIME SERIES FEATURES
# ===================================================

# ---------------------------------------------------
# Construir serie temporal por zona
# ---------------------------------------------------
def build_earnings_timeseries(df: pd.DataFrame):
    """
    Construye serie temporal de earnings por zona y hora.

    Args:
        df (pd.DataFrame): datos crudos

    Returns:
        pd.DataFrame: time series (ZONE, datetime, earnings)
    """

    # ---------------------------------------------------
    # Crear columna datetime
    # ---------------------------------------------------
    df["datetime"] = pd.to_datetime(df["DATE"]) + pd.to_timedelta(df["HOUR"], unit="h")

    # ---------------------------------------------------
    # Ordenar datos
    # ---------------------------------------------------
    df = df.sort_values(["ZONE", "datetime"])

    # ---------------------------------------------------
    # Agregar earnings por zona y hora
    # ---------------------------------------------------
    ts = df.groupby(["ZONE", "datetime"]).agg(
        earnings=("EARNINGS", "sum")
    ).reset_index()

    return ts


# ===================================================
# TIME SERIES FEATURES
# ===================================================

# ---------------------------------------------------
# Construir serie temporal de órdenes
# ---------------------------------------------------
def build_orders_timeseries(df: pd.DataFrame):
    """
    Construye serie temporal de órdenes por zona.

    Args:
        df (pd.DataFrame): datos crudos

    Returns:
        pd.DataFrame: time series (ZONE, datetime, orders)
    """

    # ---------------------------------------------------
    # Crear datetime
    # ---------------------------------------------------
    df["datetime"] = pd.to_datetime(df["DATE"]) + pd.to_timedelta(df["HOUR"], unit="h")

    # ---------------------------------------------------
    # Ordenar datos
    # ---------------------------------------------------
    df = df.sort_values(["ZONE", "datetime"])

    # ---------------------------------------------------
    # Agregar órdenes por zona y hora
    # ---------------------------------------------------
    ts_orders = df.groupby(["ZONE", "datetime"]).agg(
        orders=("ORDERS", "sum")
    ).reset_index()

    return ts_orders
