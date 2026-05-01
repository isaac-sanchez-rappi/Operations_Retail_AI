# 🚀 Sistema de Alertas Operacionales con AI

## 🧠 ¿De qué trata este proyecto?

Este proyecto implementa un sistema que ayuda al team de operaciones a **anticiparse a problemas en tiempo real**, en lugar de reaccionar tarde.

Detecta cuándo la operación puede entrar en:

* 🚨 **Saturación** → demasiadas órdenes para pocos repartidores
* 💸 **Sobreoferta** → demasiados repartidores sin suficientes órdenes

Y propone acciones claras, como ajustar incentivos (**earnings**) antes de que el problema ocurra.

---

## 🧩 Estructura del proyecto

```bash
├── modulo1_diagnostico/
├── modulo2_motor_alertas/
├── modulo3_agente_telegram/
├── scr/
├── data/
├── README.md
```

---

# ⚙️ Setup (instalación)

## 1. Descargar el proyecto

**Opción A (recomendada):**

* Descargar ZIP desde GitHub
* Descomprimir

**Opción B (usando git):**

```bash
git clone <repo_url>
cd Operations_Retail_AI\Operational_Alerts_Ai
```

---

## 2. Instalar dependencias

```bash
pip install -e .
```

⚠️ Si falla:

```bash
pip install .
```

---

# 🔐 Variables de entorno (.env)

Crear un archivo `.env` en la raíz:

```env
TELEGRAM_BOT_TOKEN=your_token_here (8792157810:AAHG3u1zhAj0YwNOKmWgoJQsHkeR8TcuZ7M) -> Usar esta para ejecutarlo
TELEGRAM_CHAT_ID=your_chat_id_here (1003708218816) -> Usar esta para ejecutarlo

GROQ_API_KEY=your_api_key_here (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) -> Usar esta para ejecutarlo
GROQ_MODEL=llama3-70b-8192
```



---

# 🤖 Configurar bot de Telegram (para la demo)

1. Crear bot con **@BotFather** en Telegram
2. Copiar el `TELEGRAM_BOT_TOKEN`
3. Enviar un mensaje al bot
4. Obtener tu `CHAT_ID`:

```bash
https://api.telegram.org/bot<TOKEN>/getUpdates
```

5. Agregar ambos valores en el `.env`

---

# ▶️ Cómo ejecutar el sistema

```bash
python modulo3_agente_telegram/run_alerts_pipeline.py
```

---

# 🔄 Reproducción por módulos

## 📊 Módulo 1 — Diagnóstico

```bash
modulo1_diagnostico/notebook.ipynb
```

* Ejecutar el notebook completo
* Contiene análisis y hallazgos

---

## ⚡ Módulo 2 — Motor de alertas

```bash
modulo2_motor_alertas/alert_runner.py
```

* Forecast de órdenes y earnings
* Predicción de repartidores
* Integración con clima
* Cálculo de acciones
* Justificaciones de metodos y tresholds seleccionados

---

## 🤖 Módulo 3 — Agente AI

```bash
modulo3_agente_telegram/run_alerts_pipeline.py
```

* Generación de mensajes con LLM
* Envío a Telegram

---

# 🌦️ API utilizada

**Open-Meteo**

* Gratis
* Sin API key
* Devuelve precipitación en mm/hr

---

# 💸 Costos estimados

| Servicio     | Costo                     |
| ------------ | ------------------------- |
| Open-Meteo   | Gratis                    |
| Telegram API | Gratis                    |
| Groq (LLM)   | ~$0.01 – $0.03 por alerta |

---

# 📊 Decisiones clave

* Horizonte: **3h** (trade-off precisión vs acción)
* Threshold lluvia: **0.7 mm/hr**
* Ratio objetivo: **1.2**
* Saturación: **>1.8**

---

# 📩 Ejemplo de alerta

```text
🔴 Santiago

Lluvia fuerte esperada (7.2 mm/hr)
Riesgo alto de saturación

Acción: subir earnings 55 → 78 MXN

Actuar en los próximos 30 minutos
```

---

# ⚠️ Consideraciones

* Incluye fallback si falla el clima o el LLM
* Evita spam con cooldown de 2 horas

---
