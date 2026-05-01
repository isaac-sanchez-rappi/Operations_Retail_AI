import json
import pandas as pd
import os

# ===================================================
# DEDUPLICADOR DE ALERTAS
# ===================================================

COOLDOWN_H = 2

class AlertDeduplicator:
    """
    Evita enviar múltiples alertas para la misma zona
    en un periodo de tiempo (cooldown).
    """

    STATE_FILE = "data/alert_state.json"

    os.makedirs("data", exist_ok=True)


    def __init__(self, cooldown_hours: int = COOLDOWN_H):
        self.cooldown_hours = cooldown_hours
        self._last = self._load()

    # ---------------------------------------------------
    # CARGAR ESTADO
    # ---------------------------------------------------
    def _load(self):
        try:
            with open(self.STATE_FILE) as f:
                raw = json.load(f)
            return {k: pd.Timestamp(v) for k, v in raw.items()}
        except Exception:
            return {}

    # ---------------------------------------------------
    # GUARDAR ESTADO
    # ---------------------------------------------------
    def _save(self):
        with open(self.STATE_FILE, "w") as f:
            json.dump({k: str(v) for k, v in self._last.items()}, f)

    # ---------------------------------------------------
    # VALIDAR SI SE DEBE ALERTAR
    # ---------------------------------------------------
    def should_alert(self, zone: str, now: pd.Timestamp) -> bool:

        if zone not in self._last:
            return True

        elapsed_h = (now - self._last[zone]).total_seconds() / 3600

        return elapsed_h >= self.cooldown_hours

    # ---------------------------------------------------
    # REGISTRAR ALERTA
    # ---------------------------------------------------
    def register(self, zone: str, now: pd.Timestamp):
        self._last[zone] = now
        self._save()