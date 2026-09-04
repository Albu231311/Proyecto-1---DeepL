# Resumen Completo del Proyecto: Monitoreo Transaccional

Este documento sirve como guía maestra para entender de principio a fin de qué trata el proyecto, cuál era el objetivo, cómo se resolvió y qué descubrimientos se hicieron. 

---

## 1. El Contexto y el Problema (¿Qué había que hacer?)
El cliente del proyecto es el **Banco del Altiplano**, quien administra millones de tarjetas de crédito/débito. Actualmente, el banco se defiende del fraude utilizando un sistema tradicional basado en variables numéricas "agregadas" (por ejemplo: medir el *promedio gastado en 24 horas*, o *cuántas transacciones se hicieron en 1 hora*).

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
- **Qué usaba:** Una red GRU combinada con las variables agregadas del Modelo A.
- **Enfoque:** El equipo pensó: *"¿Por qué elegir uno u otro? Démosle a la red neuronal la capacidad de leer la secuencia de eventos, pero al final inyectémosle el resumen histórico de las variables agregadas"*. 

---

## 4. Las Pruebas: ¿De verdad importa el orden?
Para probar que el Modelo B (la red neuronal) era mejor gracias a leer el orden, y no por simple suerte matemática, se le sometió a dos pruebas de fuego ("pruebas de falsificación"):

1. **Permutación Controlada:** Se tomó el historial de los clientes y se barajaron al azar las compras, rompiendo el orden del tiempo pero manteniendo los mismos montos y comercios.
   - *Resultado:* El rendimiento del Modelo B colapsó por completo (el AUC-PR cayó de 0.77 a 0.24). **Conclusión oficial: El orden de las transacciones es oro.**
2. **Desglose por Mecanismo de Fraude:** Al revisar en qué era bueno cada modelo, se vio que el Modelo B destruía al Modelo A detectando "Escaladas" (porque leía la secuencia). Sin embargo, el Modelo B fracasó terriblemente detectando el fraude de "Comercio Atípico" (dado que era una transacción aislada sin secuencia). 

---

## 5. El Análisis Económico
El comité fijó las reglas monetarias: 
- Dejar pasar un fraude (Falso Negativo) cuesta carísimo: **Q 4,200.**
- Bloquearle la tarjeta a un cliente inocente por accidente (Falso Positivo) es molesto pero barato: **Q 180.**

Con esta regla, los modelos ajustaron sus niveles de sensibilidad buscando ahorrarle la mayor cantidad de dinero posible al banco en el set de prueba.

### Tabla Final de Resultados (Conjunto de Test)

| Modelo | Descripción | AUC-PR (Poder Predictivo) | Costo Total |
| :--- | :--- | :--- | :--- |
| **A** | Árboles tabulares | 0.749 | Q 255,120 |
| **B** | GRU Secuencial | 0.775 | Q 253,980 |
| **C** | Híbrido (GRU + Agregados) | **0.783** | **Q 234,540** |

---

## 6. Conclusión y Veredicto Final
El ganador absoluto del proyecto fue el **Modelo C (Híbrido)**.

**¿Por qué fue el mejor?**
Porque logró corregir los puntos ciegos de todos los modelos anteriores. Al tener la red secuencial (GRU), atrapó maravillosamente los fraudes de "escalada" y "ráfagas". Al inyectarle las variables numéricas globales, recuperó la capacidad de atrapar los "comercios atípicos" donde la red sola fracasaba.

Aunque el Modelo C tiene una "precisión" baja (es decir, se asusta fácil y bloquea tarjetas inocentes constantemente), esto fue una **decisión económica inteligente**. Al banco le sale infinitamente más barato molestar a varios clientes pidiéndoles que confirmen su compra por SMS (Q 180), que tragarse la pérdida de un fraude multimillonario (Q 4,200). 

Gracias a esto, el Modelo C superó al sistema tradicional del banco (Modelo A), logrando **un ahorro estimado superior a los Q 20,500 mensuales**.
