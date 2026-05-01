import os
import logging
import requests
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path

# ===================================================
# CONFIGURACIÓN INICIAL
# ===================================================
env_path = Path(".env")  # o la ruta correcta
load_dotenv(env_path)


# configuración básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("alert_notifier")


# ===================================================
# CONFIGURACIÓN
# ===================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")
GROQ_API_KEY       = os.getenv("GROQ_API_KEY")
GROQ_MODEL         = os.getenv("GROQ_MODEL")


# ===================================================
# VALIDACIÓN DE CREDENCIALES
# ===================================================

# ---------------------------------------------------
# Validar variables de entorno
# ---------------------------------------------------
def validate_credentials():
    """
    Valida que todas las credenciales necesarias existan.

    Raises:
        EnvironmentError: si falta alguna variable
    """

    # ---------------------------------------------------
    # lista de variables requeridas
    # ---------------------------------------------------
    required_vars = {
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
        "GROQ_API_KEY": GROQ_API_KEY,
        "GROQ_MODEL": GROQ_MODEL  # 🆕 agregado
    }

    # ---------------------------------------------------
    # detectar faltantes
    # ---------------------------------------------------
    missing = [key for key, value in required_vars.items() if not value]

    # ---------------------------------------------------
    # error controlado
    # ---------------------------------------------------
    if missing:
        logger.error(f"Faltan variables de entorno: {missing}")

        raise EnvironmentError(
            f"Faltan variables de entorno: {', '.join(missing)}\n"
            f"Agrégalas en tu archivo .env"
        )

    # ---------------------------------------------------
    # validaciones adicionales básicas
    # ---------------------------------------------------
    if not TELEGRAM_BOT_TOKEN.startswith(""):
        logger.warning("TELEGRAM_BOT_TOKEN podría no tener formato válido")

    if not TELEGRAM_CHAT_ID:
        logger.warning("TELEGRAM_CHAT_ID vacío o inválido")

    logger.info("Credenciales validadas correctamente")

    return True


# ===================================================
# GENERADOR DE MENSAJE CON LLM (GROQ)
# ===================================================

# ---------------------------------------------------
# Prompt del sistema
# ---------------------------------------------------
SYSTEM_PROMPT = """Eres el asistente de alertas operacionales de Rappi.
Generas mensajes para el equipo de Operations.

REGLAS:
- Máximo 6 líneas
- Lenguaje directo, sin introducciones
- Siempre incluye el número exacto de earnings recomendado
- Termina con la ventana de tiempo para actuar
- Usa estos emojis al inicio según severidad:
  🔴 CRÍTICO | 🟠 ALTO | 🟡 MEDIO | 🔵 SOBREOFERTA"""


# ---------------------------------------------------
# Generar mensaje desde fila
# ---------------------------------------------------
def generate_message(row: pd.Series) -> str:
    """
    Genera mensaje de alerta usando LLM.

    Args:
        row (pd.Series): fila del dataset final

    Returns:
        str: mensaje generado
    """

    # ---------------------------------------------------
    # VALIDAR COLUMNAS NECESARIAS
    # ---------------------------------------------------
    required_cols = [
        "ZONE", "precipitation", "severity", "ratio",
        "earn_current", "earn_needed", "delta_earnings",
        "rt_predicted", "orders_forecast",
        "action_window_min"
    ]


    missing = [col for col in required_cols if col not in row.index]

    if missing:
        logger.error(f"Faltan columnas para LLM: {missing}")
        raise ValueError(f"Faltan columnas: {missing}")
    # ---------------------------------------------------
    # PREPARAR PROMPT
    # ---------------------------------------------------

    # 🆕 determinar dirección de acción
    direction = "subir" if row["delta_earnings"] > 0 else "bajar"

    # 🆕 texto limpio de acción
    action_text = row["action"].replace("_", " ")

    user_prompt = f"""Genera una alerta operacional con estos datos:

    Zona: {row['ZONE']}
    Precipitación esperada: {row['precipitation']:.1f} mm/hr en las próximas 3h
    Nivel de riesgo: {row['severity']} (ratio {row['ratio']})

    Acción recomendada: {action_text}

    Earnings actuales: {row['earn_current']:.1f} MXN
    Earnings sugeridos: {row['earn_needed']:.1f} MXN ({direction} {abs(row['delta_earnings']):.1f})

    Repartidores estimados: {row['rt_predicted']}
    Órdenes esperadas: {row['orders_forecast']:.0f}

    Ventana de acción: {row['action_window_min']} minutos

    Genera el mensaje ahora, sin preámbulo."""

    # ---------------------------------------------------
    # GENERACIÓN LLM
    # ---------------------------------------------------
    try:
        client = Groq(api_key=GROQ_API_KEY)

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=200,
            temperature=0.3,
        )

        return response.choices[0].message.content.strip()

    # ---------------------------------------------------
    # FALLBACK SI FALLA LLM
    # ---------------------------------------------------
    except Exception as e:
        logger.error(f"Error en LLM: {e}")

        direction = "subir" if row["delta_earnings"] > 0 else "bajar"

        return f"""
    {row['ZONE']} | {row['severity']}
    Acción: {row['action']}
    Earnings: {row['earn_current']} → {row['earn_needed']} ({direction} {abs(row['delta_earnings'])})
    Orders: {row['orders_forecast']} | RT: {row['rt_predicted']}
    Actuar en {row['action_window_min']} min
    """.strip()



# ===================================================
# ENVIAR MENSAJE TELEGRAM
# ===================================================

# ---------------------------------------------------
# Construir payload
# ---------------------------------------------------
def _build_payload(message: str) -> dict:
    """
    Construye el payload para Telegram API.

    Args:
        message (str): mensaje a enviar

    Returns:
        dict: payload listo para request
    """

    return {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",  # permite negritas, saltos, etc
    }



# ---------------------------------------------------
# Enviar mensaje a Telegram
# ---------------------------------------------------
def send_telegram(message: str) -> bool:
    """
    Envía mensaje a Telegram.

    Args:
        message (str): texto del mensaje

    Returns:
        bool: True si éxito, False si falla
    """

    # ---------------------------------------------------
    # VALIDACIÓN CONFIG
    # ---------------------------------------------------
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("❌ Telegram no configurado")
        return False

    # ---------------------------------------------------
    # URL API
    # ---------------------------------------------------
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    # ---------------------------------------------------
    # PAYLOAD
    # ---------------------------------------------------
    payload = _build_payload(message)

    # ---------------------------------------------------
    # REQUEST
    # ---------------------------------------------------
    try:
        response = requests.post(
            url,
            json=payload,
            timeout=15
        )

        response.raise_for_status()

        logger.info("📩 Mensaje enviado a Telegram")
        return True

    # ---------------------------------------------------
    # ERRORES HTTP (Telegram responde pero falla)
    # ---------------------------------------------------
    except requests.exceptions.HTTPError as e:
        logger.error("❌ Telegram HTTP error: %s", e)
        logger.error("Response: %s", response.text)
        return False

    # ---------------------------------------------------
    # ERROR DE CONEXIÓN
    # ---------------------------------------------------
    except requests.exceptions.ConnectionError:
        logger.error("❌ Sin conexión a internet")
        return False

    # ---------------------------------------------------
    # TIMEOUT
    # ---------------------------------------------------
    except requests.exceptions.Timeout:
        logger.error("❌ Timeout enviando mensaje a Telegram")
        return False

    # ---------------------------------------------------
    # ERROR GENERAL
    # ---------------------------------------------------
    except Exception as e:
        logger.error("❌ Error inesperado: %s", e)
        return False

# ===================================================
# FUNCIÓN PRINCIPAL
# ===================================================

def notify_alerts(df_final: pd.DataFrame) -> None:
    """
    Punto de entrada del módulo.
    Recibe el df_final del alert_runner (ya deduplicado)
    y envía una notificación por cada alerta activa.

    Args:
        df_final: DataFrame con las alertas finales
                  (salida del paso 9 del alert_runner)
    """

    # ---------------------------------------------------
    # VALIDAR CREDENCIALES
    # ---------------------------------------------------
    validate_credentials()

    # ---------------------------------------------------
    # VALIDAR DATASET
    # ---------------------------------------------------
    if df_final is None or df_final.empty:
        logger.info("Sin alertas activas — no se envía nada a Telegram")
        return

    # 🆕 asegurar que solo se envían alertas reales
    if "should_act" in df_final.columns:
        df_final = df_final[df_final["should_act"]]

    if df_final.empty:
        logger.info("No hay alertas accionables después del filtro")
        return

    logger.info("%d alerta(s) para notificar", len(df_final))

    # ---------------------------------------------------
    # ITERAR ALERTAS
    # ---------------------------------------------------
    for _, row in df_final.iterrows():

        zone = row.get("ZONE", "UNKNOWN")

        # ---------------------------------------------------
        # GENERAR MENSAJE (LLM)
        # ---------------------------------------------------
        logger.info("[%s] Generando mensaje con Groq...", zone)

        try:
            message = generate_message(row)

        except Exception as e:
            logger.error("[%s] Error al generar mensaje: %s", zone, e)

            # 🆕 fallback robusto
            message = _fallback_message(row)

        # ---------------------------------------------------
        # DEBUG LOCAL
        # ---------------------------------------------------
        print(f"\n── Mensaje generado para {zone} ──")
        print(message)
        print("─" * 48)

        # ---------------------------------------------------
        # ENVIAR A TELEGRAM
        # ---------------------------------------------------
        ok = send_telegram(message)

        if not ok:
            logger.warning("[%s] No se pudo enviar a Telegram", zone)

    # ---------------------------------------------------
    # 🆕 LOG FINAL
    # ---------------------------------------------------
    logger.info("Proceso de notificación finalizado")