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
- **Nombre Técnico:** HistGradientBoostingClassifier (Ensamble de Árboles de Decisión).
- **En qué se basa:** Es un modelo tabular (Machine Learning clásico). Procesa los datos como si fueran una tabla estática, sacando métricas de resumen de cada cliente (ej. *sumatoria de montos en el mes*, *número de transacciones en la última hora* o *diversidad de comercios*).
- **Enfoque y Limitación:** Representa al sistema antiguo del banco. Como solo ve el "resumen" numérico global, es completamente ciego al **orden temporal**. Si un cliente hace 4 compras pequeñas y 1 gigante, el modelo sabe que hubo 5 compras, pero no tiene ni idea en qué orden ocurrieron.

### Modelo B (El Especialista Secuencial)
- **Nombre Técnico:** Red Neuronal Recurrente con arquitectura GRU (Gated Recurrent Unit).
- **En qué se basa:** A diferencia de los árboles, este modelo procesa la información como si fuera una película paso a paso. Se le alimentó la lista "cruda" de transacciones (*monto 1 -> monto 2 -> monto 3*). Utiliza "embeddings" matemáticos para representar el comercio y canal, y usa su capa GRU como memoria para recordar qué pasó antes.
- **Enfoque y Limitación:** Su especialidad es encontrar la "narrativa" o el ritmo en el tiempo (es buenísimo para atrapar la "escalada" de fraude). Sin embargo, al estar tan concentrado en leer el historial paso a paso, sufre de amnesia de largo plazo y pierde de vista el contexto histórico global del cliente (fracasando en transacciones aisladas como el "comercio atípico").

### Modelo C (La Apuesta del Equipo / El Híbrido)
- **Nombre Técnico:** Red Neuronal Híbrida (GRU + Inyección de Variables Agregadas).
- **En qué se basa:** Es una red neuronal construida desde cero. Utiliza exactamente la misma memoria secuencial (GRU) del Modelo B para entender el orden de las compras, pero, justo antes de dar su veredicto final, se le "inyectan" o concatenan las variables tabulares históricas del Modelo A. 
- **Enfoque y Limitación:** El objetivo fue darle al modelo "lo mejor de dos mundos". Querían que la red entendiera el ritmo temporal inmediato (para cazar ráfagas) pero que al mismo tiempo tuviera el contexto general del cliente (para cazar transacciones raras en comercios atípicos). 

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
