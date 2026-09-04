# Resumen Completo del Proyecto: Monitoreo Transaccional

## Este documento sirve como guía maestra para entender de principio a fin de qué trata el proyecto, cuál era el objetivo, cómo se resolvió y qué descubrimientos se hicieron.

## 1. El Contexto y el Problema (¿Qué había que hacer?)

El cliente del proyecto es el **Banco del Altiplano**, quien administra millones de tarjetas de crédito/débito. Actualmente, el banco se defiende del fraude utilizando un sistema tradicional basado en variables numéricas "agregadas" (por ejemplo: medir el _promedio gastado en 24 horas_, o _cuántas transacciones se hicieron en 1 hora_).
**El problema:** Al área de riesgos se le escapan muchos fraudes. Al analizarlos a mano, se dieron cuenta de algo crucial: el patrón delictivo no está escondido en cuánto gastó el estafador (los montos), sino en **el orden exacto en el que ocurrieron las transacciones**.
**El objetivo del proyecto:** Demostrar científicamente si el "orden temporal" de verdad importa para detectar fraudes, y averiguar cuánto dinero se puede ahorrar si se implementa un modelo de IA capaz de leer secuencias de datos.

---

## 2. Los Datos y los Mecanismos de Fraude

Para investigar esto, el equipo generó una base de datos de transacciones sintéticas (407,524 registros simulando a 3,000 clientes durante 6 meses). Dentro de estos datos, se inyectaron 3 tipos de comportamiento criminal:

1. **Escalada (Depende del orden):** El estafador hace 3 o 4 compras pequeñitas para comprobar que la tarjeta funciona, seguidas de 1 compra gigante para robar todo el dinero.
2. **Ráfaga (Velocidad):** El estafador hace 10 compras rápidas en cuestión de media hora cambiando de comercio constantemente.
3. **Comercio Atípico (Contexto histórico):** Una sola compra muy grande en un lugar que el usuario original jamás en su vida había visitado, a una hora extraña.

---

## 3. Los Modelos Desarrollados (¿Qué hicimos?)

Para comparar enfoques, se crearon 3 modelos distintos y se enfrentaron entre sí bajo las mismas reglas y con los mismos datos:

### Modelo A (Línea Base Tradicional)

- **Qué usaba:** Un algoritmo tabular clásico de ensamble de árboles (HistGradientBoosting).
- **Enfoque:** Representa al sistema antiguo del banco. Solo lee variables "agregadas" (máximos, promedios). Es completamente ciego al orden temporal en el que ocurrieron las compras.

### Modelo B (El Especialista Secuencial)

- **Qué usaba:** Una red neuronal recurrente pura (arquitectura GRU).
- **Enfoque:** Se le alimentó la lista "cruda" de transacciones paso a paso. No recibió ni un solo promedio ni sumatoria, tuvo que aprender los patrones de fraude empíricamente leyendo las compras en el orden en que ocurrieron.

### Modelo C (La Apuesta del Equipo / El Híbrido)
