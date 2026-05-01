import logging
import requests
import pandas as pd
from zoneinfo import ZoneInfo

# ===================================================
# CONFIG
# ===================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("weather_client")

DEFAULT_PRECIP = 0.0


# ===================================================
# WEATHER CLIENT
# ===================================================


# ---------------------------------------------------
# 1. Obtener forecast desde API
# ---------------------------------------------------
def get_weather_forecast(lat: float, lon: float, forecast_hours: int = 12, retries: int = 3):
    """
    Consulta la API de Open-Meteo y retorna precipitación horaria.

    Args:
        lat (float): latitud de la zona
        lon (float): longitud de la zona
        forecast_hours (int): número de horas a consultar
        retries (int): número de reintentos en caso de fallo

    Returns:
        df_weather (pd.DataFrame): datetime + precipitación
        timezone (str): timezone de la zona
    """

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "precipitation",
        "forecast_hours": forecast_hours,
        "timezone": "auto"
    }

    # ---------------------------------------------------
    # Reintentos ante fallos de red/API
    # ---------------------------------------------------
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code != 200:
                raise Exception(f"Error API: {response.status_code}")

            data = response.json()

            if "hourly" not in data:
                raise Exception("Respuesta sin 'hourly'")

            # timezone local de la zona
            timezone = data.get("timezone", "UTC")

            # construir dataframe
            df_weather = pd.DataFrame({
                "datetime": data["hourly"]["time"],
                "precipitation_mm": data["hourly"]["precipitation"]
            })

            # convertir a datetime (ya viene en hora local)
            df_weather["datetime"] = pd.to_datetime(df_weather["datetime"])

            return df_weather, timezone

        except Exception as e:
            logger.warning(f"Intento {attempt+1} fallido ({lat},{lon}): {e}")
    
    logger.error(f"API FALLÓ COMPLETAMENTE para ({lat},{lon})")


    # ---------------------------------------------------
    # fallback si todo falla
    # ---------------------------------------------------
    return pd.DataFrame(), "UTC"


# ---------------------------------------------------
# 2. Extraer precipitación +1h y +3h
# ---------------------------------------------------
def get_precip_next_hours(df_weather: pd.DataFrame, timezone: str):
    """
    Obtiene precipitación esperada en +1h y +3h.

    Args:
        df_weather (pd.DataFrame): forecast horario
        timezone (str): timezone local

    Returns:
        now, t+1h, t+3h, precip_1h, precip_3h
    """

    # ---------------------------------------------------
    # Hora actual en timezone de la zona
    # ---------------------------------------------------
    try:
        now = pd.Timestamp.now(ZoneInfo(timezone)).floor("h").tz_localize(None)
    except:
        now = pd.Timestamp.now().floor("h")

    # ---------------------------------------------------
    # Definir horizontes de forecast
    # ---------------------------------------------------
    t1 = now + pd.Timedelta(hours=1)
    t3 = now + pd.Timedelta(hours=3)

    if df_weather.empty:
        return now, t1, t3, DEFAULT_PRECIP, DEFAULT_PRECIP

    # ordenar por seguridad
    df_weather = df_weather.sort_values("datetime")

    # ---------------------------------------------------
    # Buscar índices más cercanos
    # ---------------------------------------------------
    idx1 = df_weather["datetime"].searchsorted(t1)
    idx3 = df_weather["datetime"].searchsorted(t3)

    # obtener valores
    p1 = df_weather.iloc[idx1]["precipitation_mm"] if idx1 < len(df_weather) else DEFAULT_PRECIP
    p3 = df_weather.iloc[idx3]["precipitation_mm"] if idx3 < len(df_weather) else DEFAULT_PRECIP

    return now, t1, t3, p1, p3


# ---------------------------------------------------
# 3. Pipeline por zonas
# ---------------------------------------------------
def get_weather_zones_forecast(zone_info: pd.DataFrame):
    """
    Genera forecast de precipitación para todas las zonas.

    Args:
        zone_info (pd.DataFrame): contiene lat/lon por zona

    Returns:
        pd.DataFrame: forecast por zona (+1h y +3h)
    """

    results = []

    for _, row in zone_info.iterrows():

        zone = row["ZONE"]
        lat = row["LATITUDE_CENTER"]
        lon = row["LONGITUDE_CENTER"]

        logger.info(f"Procesando {zone}")

        try:
            # ---------------------------------------------------
            # Obtener forecast de API
            # ---------------------------------------------------
            df_weather, timezone = get_weather_forecast(lat, lon)

            # ---------------------------------------------------
            # Extraer horizontes relevantes
            # ---------------------------------------------------
            now, t1, t3, p1, p3 = get_precip_next_hours(df_weather, timezone)

            results.append({

                "ZONE": zone,
                "LATITUDE": lat,
                "LONGITUDE": lon,
                "timezone": timezone,
                "datetime_local": now,
                "target_1h": t1,
                "target_3h": t3,
                "precipitation_1h": p1,
                "precipitation_3h": p3
            })

        except Exception as e:
            logger.error(f"Error total en {zone}: {e}")
            now, t1, t3, p1, p3 = None, None, None, DEFAULT_PRECIP, DEFAULT_PRECIP
            tz = "UTC"

            results.append({
            "ZONE": zone,
            "LATITUDE": lat,
            "LONGITUDE": lon,
            "timezone": timezone,
            "datetime_local": now,
            "target_1h": t1,
            "target_3h": t3,
            "precipitation_1h": p1,
            "precipitation_3h": p3
        })

    return pd.DataFrame(results)