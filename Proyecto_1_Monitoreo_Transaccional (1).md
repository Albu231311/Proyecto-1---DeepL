# Proyecto 1

## Monitoreo transaccional: detectar lo que el orden revela

**Universidad del Valle**  
**Deep Learning 2026**  
**Kevin Recinos**

| Información | Detalle |
|---|---|
| **Entrega final** | viernes 4 de septiembre de 2026, 23:59 |
| **Presentación** | viernes 4 de septiembre de 2026, durante la sesión virtual - 8 minutos + 4 de preguntas |
| **Modalidad** | parejas |
| **Ponderación** | 8 puntos sobre la nota final del curso |

## 1. El encargo

Banco del Altiplano opera 1.4 millones de tarjetas de débito y crédito. Su sistema antifraude actual es un motor construido sobre variables agregadas por ventana de tiempo: monto promedio de las últimas 24 horas, número de transacciones por hora, monto máximo del día y diversidad de comercios.

El sistema funciona, pero el área de riesgos tiene una queja concreta y repetida:

> "Cuando revisamos los casos que se nos escaparon, el patrón siempre está ahí. No en los montos: en el orden en que ocurrieron."

El comité no le pide una arquitectura específica. Le pide diseñar y defender una investigación que permita decidir si vale la pena incorporar un modelo de secuencias. Cada equipo puede elegir su propio enfoque; no se espera que todos utilicen el mismo modelo. La calificación dependerá de qué tan bien diseñen, evalúen y expliquen sus experimentos, no de usar la arquitectura más compleja.

La pregunta central no es "¿puedo entrenar una LSTM?". Es: **¿el orden de las transacciones aporta información que las variables agregadas no capturan, bajo qué condiciones y cuánto vale esa información en quetzales?**

## 2. Núcleo común y espacio de creatividad

Todos los equipos deben construir el mismo núcleo comparable, pero cada equipo decide cómo resolverlo:

| Pieza | Requisito |
|---|---|
| **A - Línea base sin orden** | Un modelo competitivo sobre variables agregadas. Puede ser regresión, árboles, una red densa u otra opción justificada. Representa lo que se puede lograr sin leer la secuencia. |
| **B - Modelo secuencial** | Un modelo que reciba eventos ordenados: RNN, LSTM, GRU, CNN temporal, TCN, atención, Transformer u otra arquitectura defendible. La complejidad por sí sola no da puntos. |
| **C - Apuesta del equipo** | Una extensión con hipótesis propia. Debe tener un control experimental y una métrica de éxito declarada antes de ver el conjunto de prueba. |

La apuesta C puede explorar, entre otras posibilidades: detección no supervisada de fraudes nuevos; un modelo híbrido que combine agregados y secuencia; embeddings de comercio o canal; atención interpretable; aprendizaje con pocas etiquetas; robustez ante un mecanismo de fraude no visto; o una arquitectura distinta a la de B. La lista es **ilustrativa, no cerrada**.

Antes de entrenar C, escriba en el notebook una frase con esta forma:

> *"Creemos que ____ mejorará ____ porque ____. Lo consideraremos útil si ____."*

Los modelos A y B, y cualquier modelo de C que produzca una predicción, deben devolver un **puntaje continuo de riesgo**. La decisión de umbral ocurre después. Todas las comparaciones deben usar los mismos datos, la misma partición y el mismo horizonte de predicción.

## 3. Dos pruebas obligatorias para demostrar el valor del orden

Una mejora de métricas no demuestra, por sí sola, que el modelo usó el orden. Debe intentar **refutar su propia conclusión** con dos pruebas:

1. **Permutación controlada.** Evalúe el modelo B después de barajar el orden dentro de cada secuencia, sin cambiar sus eventos ni sus variables agregadas. Compare contra la secuencia original y explique el cambio.
2. **Prueba elegida por el equipo.** Escoja una: recortar la historia; retirar las variables temporales; evaluar por mecanismo de fraude; simular un cambio de canal o comportamiento; probar secuencias más largas que las de entrenamiento; u otra prueba que pueda hacer fallar su afirmación.

Si el desempeño no cae al destruir el orden, el resultado es válido, pero la conclusión debe ser honesta: con esa evidencia, no puede afirmar que el orden aportó.

## 4. Los datos

Puede elegir una de dos rutas. Ambas valen lo mismo.

### 4.1. Ruta A - Datos sintéticos con generador propio

En esta ruta, usted crea los datos. Genere secuencias de transacciones con al menos **tres tipos de fraude**. Por lo menos uno debe depender principalmente del orden; por ejemplo, varias compras pequeñas seguidas de una compra grande. Usted decide los tipos de fraude, las variables y qué tan difícil será detectarlos.

El generador es parte del entregable. Debe producir los mismos datos cuando se use la misma semilla. Explique con palabras sencillas qué patrón representa cada tipo de fraude e incluya al menos un caso en el que espera que su modelo falle.

### 4.2. Ruta B - Datos públicos reales

En esta ruta, use un conjunto público de transacciones reales que incluya el orden de las operaciones y una etiqueta de fraude. Los datos deben permitir identificar las transacciones de un mismo cliente o tarjeta para formar las secuencias. Explique qué representa cada secuencia, cuántas transacciones contiene y qué intenta predecir el modelo.

En ambas rutas, la separación debe respetar el tiempo: use los datos más antiguos para entrenar, datos más recientes para validar y los últimos para probar. No mezcle transacciones del futuro con las del pasado. El conjunto de prueba se revisa una sola vez, después de tomar todas las decisiones del modelo.

## 5. Entregables

| Entregable | Detalle |
|---|---|
| `proyecto1_<apellidos>.ipynb` | Notebook ejecutado con A, B, la apuesta C, las dos pruebas de falsificación y el análisis económico. |
| `artefactos/` | Pesos del modelo candidato y los parámetros de preparación necesarios para volver a producir sus puntajes. No se pide todavía un servicio. |
| `informe.pdf` | Máximo 7 páginas. Escrito para el comité de riesgos, no para el profesor. Sin código adentro. |
| `presentacion.pdf` | Máximo 8 diapositivas. |
| `README.md` | Reproducción, versiones, declaración de uso de IA y la sección "Candidato al Proyecto Final". |

### 5.1. Las seis evidencias que debe contener el informe

La estructura puede ser creativa, pero el comité debe poder localizar estas seis evidencias sin adivinarlas:

1. **Integridad de datos:** origen, tamaño, tasa de fraude, construcción de secuencias, partición temporal y controles contra fuga de información.
2. **Comparación común:** A contra B con AUC-PR y, en el umbral elegido, precisión, exhaustividad y F1. No reporte exactitud como métrica principal.
3. **Valor del orden:** resultado de la permutación controlada y de la segunda prueba elegida.
4. **Apuesta del equipo:** hipótesis previa, control, resultado y veredicto, aunque haya fallado.
5. **Decisión económica:** si un fraude no detectado cuesta en promedio Q4,200 y bloquear una transacción legítima cuesta Q180, ¿dónde coloca el umbral y cuánto ahorra o pierde al mes?
6. **Recomendación y límites:** reemplazar, complementar o conservar el sistema actual; al menos un patrón de error concreto y las condiciones bajo las que cambiaría su recomendación.

Agregue al final una tabla de una página o menos con las columnas: evidencia, figura o tabla donde aparece, conclusión y limitación. Esta matriz será también la guía de calificación.

## 6. Rúbrica

| Criterio | Puntos |
|---|---:|
| Datos y protocolo temporal. Secuencias documentadas, tres particiones correctas, sin fuga de información. | 15 |
| Núcleo A y B. Implementación correcta, comparación común y decisiones de diseño justificadas. | 20 |
| Evidencia del valor del orden. Permutación controlada y segunda prueba de falsificación, interpretadas sin exagerar. | 20 |
| Apuesta del equipo. Hipótesis previa, control experimental, métrica de éxito y veredicto. | 15 |
| Umbral, costo y recomendación. Decisión cuantificada, análisis de error y límites explícitos. | 15 |
| Comunicación y reproducibilidad. Informe, matriz de evidencias, presentación y artefactos reutilizables. | 15 |
| **Total** | **100** |

### 6.1. Puntos que se descuentan sin excepción

- **-20:** partición aleatoria de datos con estructura temporal.
- **-15:** normalizar, seleccionar variables o ajustar el ventaneo usando estadísticas del conjunto completo.
- **-15:** reportar exactitud como métrica principal en un problema desbalanceado.
- **-10:** elegir arquitectura, umbral o apuesta mirando el conjunto de prueba.
- **-10:** afirmar que el orden aporta sin ejecutar la permutación controlada.

## 7. Sobre el uso de asistentes de IA

Puede usarlos y debe declarar en el README para qué los usó y qué verificó usted. Además, identifique tres decisiones técnicas importantes, las alternativas que consideró y la evidencia que inclinó la decisión.

En la presentación se escogerá al azar una de esas decisiones y cualquier integrante deberá defenderla. Si no puede explicar por qué una parte del código existe, esa evidencia no recibe crédito, sin importar quién la escribió. No se califica cuántas líneas produjo usted; se califica la calidad de las decisiones y de la verificación.

## 8. Puente hacia el Proyecto Final

El Proyecto Final toma uno de los Proyectos 1, 2 o 3 y lo lleva a producción. Por eso este trabajo no debe tratarse como un notebook desechable. En la sección **"Candidato al Proyecto Final"** del README deje registrado:

- cuál modelo conservaría y dónde está su artefacto;
- quién usaría su puntaje y qué decisión tomaría;
- el contrato preliminar de entrada y salida; y
- sus principales límites, riesgos y datos que todavía faltarían.

Todavía no se pide API, MLflow, monitoreo ni dashboard. Esos elementos se introducen y se califican exclusivamente en el Proyecto Final. Aquí se espera que deje una base suficientemente sólida para no tener que reconstruir el modelo desde cero al final del curso.
