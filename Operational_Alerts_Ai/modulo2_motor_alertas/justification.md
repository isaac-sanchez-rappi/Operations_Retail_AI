# Justificación del Motor de Alertas (Módulo 2)

## 1. Enfoque general

El motor de alertas fue diseñado para anticipar desbalances operacionales (saturación o sobreoferta) combinando:

* **Predicción de la operación futura** (órdenes, earnings y repartidores)
* **Detección de riesgo climático** (precipitación)

La lógica se construye directamente a partir de patrones observados en el histórico, evitando reglas arbitrarias.

---

## 2. Umbral de precipitación (trigger de alertas)

Para determinar el nivel de lluvia que impacta la operación se construyó una curva empírica (ver validation.ipynb):

* Se define saturación como:
  **ratio = órdenes / repartidores > 1.8**
* Se discretiza la lluvia en niveles (cuantiles)
* Se calcula:
  **P(saturación | nivel de lluvia)**

El umbral se define como el punto donde:
**P(saturación) ≥ 20%**

### Resultado:

* Umbral encontrado: **0.7 mm/hr**
* Probabilidad de saturación en ese nivel: **30% – 60%**
* El umbral es consistente en todas las zonas:

### Conclusión:

✔ Se puede utilizar un **umbral global de 0.7 mm/hr** pero en aras de expandir la logica se crean tresholds ajustados a cada zona

---

## 3. Horizonte de anticipación (1h vs 3h)

Se evaluó el desempeño del forecast usando **walk-forward validation** (ver validation.ipynb):

### Resultados:

* MAE promedio 1h: **0.93**
* MAE promedio 3h: **1.04**
* Degradación promedio: **+12.2%**

### Interpretación:

* El error aumenta de forma moderada
* No hay pérdida significativa de estabilidad
* El modelo mantiene capacidad predictiva útil a 3h

### Decisión:

✔ Se selecciona horizonte de **3 horas**

**Trade-off:**

* 1h → más preciso pero reactivo
* 3h → ligeramente menos preciso pero permite actuar

✔ Se prioriza **capacidad de reacción operacional**

---

## 4. Modelo de oferta (repartidores)

Se entrena un modelo OLS:

```
CONNECTED_RT ~ EARNINGS + ORDERS + PRECIPITATION_MM
```

Esto permite estimar cuántos repartidores estarán disponibles bajo diferentes condiciones.

---

## 5. Cálculo de earnings óptimo

El objetivo del sistema es mantener un ratio saludable:

```
target = 1.2
```

Se calcula el nivel de earnings necesario para lograrlo:

```
rt_needed = órdenes / 1.2
```

Luego se despeja earnings usando el modelo.

### Controles aplicados:

* No bajar de mínimo histórico
* Máximo = +10% del histórico
* Cambios < ±2 MXN se ignoran (ruido)

✔ Resultado: acciones específicas, estables y realistas

---

## 6. Lógica de decisión

El motor combina tres señales:

1. **Ratio proyectado**
2. **Riesgo por lluvia (precipitación vs threshold)**
3. **Nivel de demanda**

### Reglas:

* Ratio alto o lluvia ≥ 0.7 → subir earnings
* Ratio bajo → bajar earnings
* Baja demanda → no actuar

### Severidad:

* Crítico: ratio ≥ 2.5
* Alto: ratio ≥ 1.8
* Medio: ratio ≥ 1.4

---

## 7. Control de alert fatigue

Se implementa deduplicación:

* Cooldown: **2 horas por zona**
* Persistencia en archivo (`alert_state.json`)
