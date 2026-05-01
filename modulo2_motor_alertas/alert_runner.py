# ===================================================
# ALERT RUNNER (ORQUESTADOR PRINCIPAL)
# ================================================
import pandas as pd
from scr.features.data_loader import load_raw_data

from modulo2_motor_alertas.weather_client import get_weather_zones_forecast

from scr.features.time_series import (
    build_earnings_timeseries,
    build_orders_timeseries
)

from scr.models.earnings_forecast import forecast_earnings_all_zones
from scr.models.orders_forecast import forecast_orders_all_zones

from scr.models.rt_model import train_rt_model, predict_rt
from scr.features.forecast_builder import build_rt_forecast_dataset

from scr.features.weather_thresholds import (
    build_risk_features,
    create_rain_bins,
    build_rain_risk_curve,
    compute_rain_thresholds
)

from modulo2_motor_alertas.decision_engine import decision_engine
from modulo2_motor_alertas.deduplicator import AlertDeduplicator

# ---------------------------------------------------
# MAIN FUNCTION
# ---------------------------------------------------
def run_alerts():

    # ---------------------------------------------------
    # 1. CARGAR DATOS
    # ---------------------------------------------------
    df, zone_info = load_raw_data()


    # ===================================================
    # 2. WEATHER FORECAST
    # ===================================================
    weather_forecast_df = get_weather_zones_forecast(zone_info)
    weather_forecast_df

    # ===================================================
    # 3. FORECAST EARNINGS
    # ===================================================
    ts_earnings = build_earnings_timeseries(df)
    forecast_earnings_df = forecast_earnings_all_zones(ts_earnings)
    forecast_earnings_df

    # ===================================================
    # 4. FORECAST ORDERS
    # ===================================================
    ts_orders = build_orders_timeseries(df)
    forecast_orders_df = forecast_orders_all_zones(ts_orders)
    forecast_orders_df

    # ===================================================
    # 5. MODELO RT
    # ===================================================
    model_rt = train_rt_model(df)

    df_future = build_rt_forecast_dataset(
        forecast_earnings_df,
        forecast_orders_df,
        weather_forecast_df
    )

    df_predictions = predict_rt(model_rt, df_future)
    df_predictions

    # ===================================================
    # 6. THRESHOLDS DE LLUVIA
    # ===================================================
    df_thr = build_risk_features(df)
    df_thr = create_rain_bins(df_thr)
    zone_rain_curve = build_rain_risk_curve(df_thr)
    thresholds_df = compute_rain_thresholds(zone_rain_curve)
    thresholds_df


    # ===================================================
    # 7. DECISION ENGINE (EARNINGS)
    # ===================================================
    df_actions = decision_engine(
        df_predictions=df_predictions,
        thresholds_df=thresholds_df,
        model=model_rt,
        df_historical=df
    )

    # ===================================================
    # 8. OUTPUT FINAL (SIMPLE)
    # ===================================================
    print("\n===== ALERTAS =====\n")

    for _, row in df_actions.iterrows():

        forecast_hr = row.get('forecast_hour', None)
        hr_str = str(forecast_hr) if pd.notna(forecast_hr) else "N/A"

        earn_needed = row['earn_needed']
        earn_needed_str = round(earn_needed, 1) if pd.notna(earn_needed) else "Sin cambios"

        delta = row['delta_earnings']
        accion = row['action']
        delta_str = round(delta, 1) if pd.notna(delta) else 0

        print(f"Zona: {row['ZONE']}")
        print(f"Hora pronóstico: {hr_str}")
        print(f"Earnings actual: {row['earn_current']}")
        print(f"Earnings recomendado: {earn_needed_str}")
        print(f"Acción: {accion}")
        print(f"Delta: {delta_str}")
        print("--------------------------")

    # ===================================================
    # 9. DEDUPLICACIÓN 🆕🔥
    # ===================================================
    dedup = AlertDeduplicator()

    now = pd.Timestamp.now()

    final_alerts = []

    for _, row in df_actions.iterrows():

        zone = row["ZONE"]

        # solo alertas reales
        if not row["should_act"]:
            continue

        # validar cooldown
        if dedup.should_alert(zone, now):

            dedup.register(zone, now)
            final_alerts.append(row)

        else:
            print(f"⏱️ SKIP (cooldown): {zone}")

    df_final = pd.DataFrame(final_alerts)

    print("\nFINAL ALERTS:")
    print(df_final)
    
    return df_final 
   

# ---------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------
if __name__ == "__main__":
    run_alerts()