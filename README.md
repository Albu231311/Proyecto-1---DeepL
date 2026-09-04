# Proyecto 1: Monitoreo transaccional

Detectar lo que el orden revela. Universidad del Valle de Guatemala, Deep Learning 2026.

Equipo: Erick Guerra (23208) y Carlos Alburez (231311).

## Qué hay en este repositorio

- `proyecto1_Guerra_Alburez.ipynb`: notebook ejecutado con el Modelo A (línea base sin orden), el Modelo B (GRU secuencial), la Apuesta C (GRU con agregados), las dos pruebas de falsación y el análisis económico.
- `generador.py`: generador de datos sintéticos, determinista con la misma semilla.
- `informe.pdf`: informe para el comité de riesgos (máximo 7 páginas, sin código).
- `presentacion.pdf` y `presentacion_script.md`: diapositivas y guion de la presentación.
- `artefactos/`: pesos del modelo candidato y parámetros necesarios para reproducir sus puntajes.

## Cómo reproducir los resultados

1. Instalar dependencias: `pip install -r requirements.txt`.
2. Abrir `proyecto1_Guerra_Alburez.ipynb` y ejecutar todas las celdas en orden, desde un kernel limpio.
3. El generador usa `seed=2027`; con esa semilla el dataset sintético (3,000 clientes, 180 días) es idéntico en cualquier máquina.
4. Los modelos B y C fijan la semilla de PyTorch (`SEED_TORCH = 2027`) antes de inicializar los pesos y usan un `torch.Generator` explícito en los `DataLoader`, así que el entrenamiento es reproducible dentro de las restricciones deterministas de la versión instalada de PyTorch.
5. El conjunto de prueba (días 150 a 179) solo se evalúa en la sección final del notebook, después de congelar arquitecturas, umbrales y pruebas de falsación.

## Versiones

- Python: 3.13 / 3.14 (probado en ambas)
- PyTorch: 2.13
- scikit-learn: 1.8
- pandas: 2.3
- numpy: 2.3

Ver `requirements.txt` para el listado completo.

## Declaración de uso de IA

Usamos un asistente de IA (Claude) principalmente para dos cosas: revisar el notebook en busca de errores de reproducibilidad y de fuga de información antes de abrir el conjunto de prueba, y para redactar este README, el informe y el guion de la presentación a partir de los resultados y decisiones que ya habíamos tomado nosotros. No usamos IA para elegir arquitecturas, hiperparámetros, umbrales ni para interpretar si el orden aportaba valor; esas decisiones y su verificación en el notebook son nuestras.

Lo que verificamos nosotros: releímos cada corrección sugerida contra el código real antes de aplicarla, volvimos a ejecutar el notebook completo después de cada cambio y comparamos que las métricas reportadas en el informe coincidieran exactamente con la salida del notebook ejecutado.

Tres decisiones técnicas importantes:

1. **Fijar la semilla de PyTorch antes de construir los modelos B y C, no dentro de la función de entrenamiento.** Alternativa considerada: dejar la semilla dentro de `entrenar_modelo_secuencial`, como estaba originalmente. Evidencia que inclinó la decisión: al revisar el notebook nos dimos cuenta de que los pesos iniciales de `ModeloSecuencial` se creaban antes de llamar a esa función, así que la inicialización no quedaba controlada por la semilla, y el `DataLoader` con `shuffle=True` tampoco tenía un generador explícito. Movimos `fijar_semilla()` antes de instanciar el modelo y agregamos `torch.Generator().manual_seed(SEED_TORCH)` a cada `DataLoader`.
2. **No reutilizar los pesos del Modelo B al entrenar el Modelo C.** Alternativa considerada: inicializar C con los pesos ya entrenados de B y solo ajustar la cabeza que recibe los agregados. Evidencia que inclinó la decisión: reutilizar pesos habría dejado a C en ventaja artificial frente a B, contaminando la comparación; entrenamos C desde cero con la misma arquitectura, semilla y orden de minibatches que B, para que la única diferencia entre ambos sea la información agregada.
3. **Umbral de operación elegido por costo económico, no por F1 ni por un valor fijo como 0.5.** Alternativa considerada: usar el umbral que maximiza F1 en validación. Evidencia que inclinó la decisión: dado que un fraude no detectado cuesta Q4,200 y un bloqueo indebido cuesta Q180 (23 veces menos), buscamos en una malla de umbrales el que minimiza el costo total en validación para cada modelo, en lugar de optimizar una métrica que no refleja esa asimetría de costos.

En la presentación se escogerá al azar una de estas decisiones y cualquier integrante del equipo la defenderá.

## Candidato al Proyecto Final

- **Modelo que conservaríamos:** el Modelo C (GRU con embeddings de comercio y canal, más variables agregadas causales). Aunque no cumplió el criterio de mejora de AUC-PR que nos impusimos antes de entrenarlo, es el que menor costo económico produce en el conjunto de prueba y el que mejor recupera el mecanismo de comercio atípico, donde A y B fallan casi por completo. Su artefacto está en `artefactos/modelo_c.pt`, junto con `artefactos/deploy_config.json` (umbrales, columnas de entrada y longitud de secuencia).
- **Quién usaría el puntaje y qué decisión tomaría:** el equipo de operaciones antifraude, para decidir si bloquea una transacción en el momento de autorización o si la envía a revisión manual cuando el puntaje cae en una zona intermedia alrededor del umbral (0.23), en lugar de bloquear automáticamente todo lo que lo supere.
- **Contrato preliminar de entrada y salida:** entrada, hasta las últimas 20 transacciones del cliente (variables por evento: monto, tiempo desde la transacción anterior, hora, día de la semana, comercio y canal) más las variables agregadas causales (`monto_prom_24h`, `n_trans_ultima_hora`, `monto_max_dia`, `diversidad_comercios_7d`, frecuencia de comercio y canal). Salida, un puntaje continuo de riesgo entre 0 y 1 por transacción.
- **Límites, riesgos y datos que faltarían:** el modelo se entrenó y evaluó exclusivamente con datos sintéticos; antes de producción necesitaríamos validar contra transacciones reales de Banco del Altiplano. La precisión de C es baja (35% en test), así que llevarlo a producción sin una zona de revisión humana generaría muchas falsas alarmas. El mecanismo de comercio atípico tiene muy pocos casos en validación y prueba (9 a 10), por lo que esa mejora específica necesita confirmarse con más datos antes de confiar en ella operativamente.
