import os
import pandas as pd

# ===================================================
# DATA LOADER
# ===================================================

def load_raw_data():
    """
    Carga datos desde data/raw automáticamente
    """

    # ruta base del proyecto
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    file_path = os.path.join(
        base_path,
        "data",
        "raw",
        "rappi_delivery_case_data.xlsx"
    )

    df = pd.read_excel(file_path, sheet_name="RAW_DATA")
    zone_info = pd.read_excel(file_path, sheet_name="ZONE_INFO")

    # Combina fecha + hora → timestamp real
    df["datetime"] = (
        pd.to_datetime(df["DATE"]) +
        pd.to_timedelta(df["HOUR"], unit="h")
    )

    df = df.sort_values(["ZONE", "datetime"])

    # Use solo los últimos 3 meses
    max_date = df["datetime"].max()
    cutoff_date = max_date - pd.Timedelta(days=90)
    df = df[df["datetime"] >= cutoff_date]

    print(f"Data cargada: {len(df)} filas")
    print(f"Rango fechas: {df['datetime'].min()} → {df['datetime'].max()}")

    return df, zone_info
