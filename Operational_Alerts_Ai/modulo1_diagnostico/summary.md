# Resumen de Hallazgos — Diagnóstico Operacional

El análisis del histórico muestra que la operación tiene patrones claros y predecibles, pero actualmente no está siendo gestionada de forma óptima.

## 1. Cuándo ocurre la saturación

La saturación se concentra principalmente en dos momentos del día:

- Mediodía (12h–14h):  
  - Ratio: ~1.52 – 1.60  
  - Saturación: ~26%  
  → Aproximadamente 1 de cada 4 horas está en saturación  

- Noche (19h–21h):  
  - Ratio: ~1.36 – 1.39  
  - Saturación: ~8%  

En contraste, durante la madrugada hay sobre-oferta (~50%), lo que indica ineficiencia en costos.

---

## 2. Qué causa el deterioro

La variable que más impacta la operación es la lluvia.

- Sin lluvia:
  - Saturación: ~3.7%

- Lluvia extrema:
  - Saturación: ~39.6%

→ La probabilidad de saturación aumenta más de 10 veces.

Esto ocurre porque:

- Las órdenes aumentan ~155%
- Los repartidores solo aumentan ~63%

→ La demanda crece más rápido que la oferta.

---

## 3. No todas las zonas se comportan igual

Hay zonas mucho más sensibles a la lluvia.

- Zonas más vulnerables:
  - Santiago, Carretera Nacional  
  - Incrementos de saturación de hasta ~0.4

- Zonas más estables:
  - Mejor balance entre órdenes y repartidores

Esto indica que la operación debe manejarse por zona, no de forma general.

---

## 4. El sistema de incentivos no está bien calibrado

Se identifican dos problemas claros:

- Sub-reacción:
  - El ratio sube, pero los earnings no aumentan

- Sobre-gasto:
  - El ratio baja, pero los earnings se mantienen altos

Ejemplos:

- 2024-03-05 → 58 eventos (principalmente sub-reacción)
- 2024-03-22 → 57 eventos (sobre-gasto)

Esto muestra que el sistema responde de forma inconsistente.

---

## 5. Cómo realmente funcionan los earnings

Earnings no impacta directamente la saturación.

Funciona de forma indirecta:

EARNINGS → CONNECTED_RT → RATIO

- Earnings aumenta la oferta (repartidores)
- La saturación depende del balance entre oferta y demanda

→ No se debe modelar el ratio directamente, sino la oferta.

---

## Conclusión general

La operación presenta:

- Patrones claros por hora
- Fuerte impacto de la lluvia
- Diferencias importantes por zona
- Un sistema de incentivos mal calibrado

Esto crea oportunidades claras para:

- Anticipar eventos de saturación
- Ajustar incentivos de forma más precisa
- Gestionar la operación por zona y no de forma uniforme