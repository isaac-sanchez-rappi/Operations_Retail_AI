import logging

# ===================================================
# IMPORTS PIPELINE
# ===================================================

# 🆕 importar runner del módulo 2
from modulo2_motor_alertas.alert_runner import run_alerts

# 🆕 importar notifier
from alert_notifier import notify_alerts


# ===================================================
# CONFIG LOGGING
# ===================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("alerts_pipeline")


# ===================================================
# MAIN PIPELINE
# ===================================================
def run_pipeline():
    """
    Ejecuta pipeline completo:
    1. Genera alertas (módulo 2)
    2. Envía alertas (módulo 3)
    """

    logger.info("Iniciando pipeline completo de alertas")

    # ---------------------------------------------------
    # STEP 1: GENERAR ALERTAS
    # ---------------------------------------------------
    try:
        df_final = run_alerts()  # 🆕 ahora retorna dataframe

    except Exception as e:
        logger.error("❌ Error en alert_runner: %s", e)
        return

    # ---------------------------------------------------
    # VALIDAR OUTPUT
    # ---------------------------------------------------
    if df_final is None:
        logger.warning("⚠️ alert_runner retornó None")
        return

    if df_final.empty:
        logger.info("📭 No hay alertas para enviar")
        return

    logger.info("Alertas generadas: %d", len(df_final))

    # ---------------------------------------------------
    # STEP 2: ENVIAR ALERTAS
    # ---------------------------------------------------
    try:
        notify_alerts(df_final)

    except Exception as e:
        logger.error("Error en notifier: %s", e)


# ===================================================
# ENTRYPOINT
# ===================================================
if __name__ == "__main__":
    run_pipeline()