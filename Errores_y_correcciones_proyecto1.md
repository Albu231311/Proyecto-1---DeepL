# Errores y correcciones pendientes del Proyecto 1

## Resumen general

El notebook está bien encaminado y contiene una implementación funcional de los modelos A, B y C. Las secuencias son causales, la normalización se calcula únicamente con entrenamiento y el conjunto de prueba continúa sellado. Sin embargo, antes de considerar el proyecto terminado y ejecutar el *test* final, deben corregirse varios puntos de reproducibilidad, documentación y evaluación.

## 1. Semillas configuradas después de crear los modelos

### Problema

En los modelos B y C, `torch.manual_seed(seed)` se ejecuta dentro de la función de entrenamiento, pero las instancias de los modelos se crean antes de llamar a esa función. Por lo tanto, la inicialización de sus pesos no queda controlada por la semilla.

Además, los `DataLoader` que usan `shuffle=True` no reciben un generador con una semilla explícita. Esto puede cambiar el orden de los lotes entre ejecuciones.

### Impacto

Los resultados pueden variar al reiniciar el kernel, incluso si aparentemente se está usando la misma semilla. Esto afecta la reproducibilidad de las métricas y de la selección del modelo candidato.

### Corrección

Configurar todas las semillas **antes de construir cada modelo**:

```python
import random
import numpy as np
import torch

SEED = 2027

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

torch.use_deterministic_algorithms(True, warn_only=True)
```

También se debe controlar el orden del `DataLoader`:

```python
generator_b = torch.Generator().manual_seed(SEED)

loader_b = DataLoader(
    dataset_b,
    batch_size=BATCH_SIZE,
    shuffle=True,
    generator=generator_b,
)
```

Debe hacerse lo mismo para el modelo C. Después de aplicar el cambio, conviene ejecutar el notebook completo dos veces desde un kernel limpio y comprobar que las métricas coincidan.

## 2. La descripción del modelo C no coincide con su implementación

### Problema

La hipótesis describe al modelo C como una combinación de los agregados con el “estado final del GRU de B”. Sin embargo, el código crea un GRU nuevo para C y lo entrena desde cero; no reutiliza los pesos ni el estado del modelo B.

### Corrección recomendada

Cambiar la descripción por una formulación fiel al código:

> El modelo C utiliza una nueva red GRU con la misma arquitectura base que B y la entrena conjuntamente con las variables agregadas.

La otra alternativa sería reutilizar realmente los pesos de B, pero eso cambiaría el experimento. Para este proyecto, lo más simple y claro es corregir la redacción.

## 3. Falta evaluar el modelo C por mecanismo de fraude

### Problema

El análisis por mecanismo compara A, B y B con el historial permutado, pero no incorpora al modelo C. Esto deja incompleta la evaluación del modelo que fue seleccionado provisionalmente como candidato.

### Corrección

Agregar una tabla por tipo de fraude que incluya, como mínimo:

- Cantidad de positivos.
- AUC-PR de A, B y C.
- *Recall* de A, B y C usando sus umbrales globales fijados en validación.
- Diferencia de C respecto de B.

Esto permitirá comprobar si C conserva la mejora en `escalada`, cómo se comporta en `rafaga` y si recupera parte del problema observado en `comercio_atipico`.

## 4. La introducción del notebook quedó desactualizada

### Problema

La introducción indica que los modelos B y C y las pruebas de falsación se agregarán posteriormente, aunque esas secciones ya están incluidas.

### Corrección

Actualizarla para indicar que el notebook ya contiene:

- Modelo A: línea base tabular.
- Modelo B: modelo secuencial GRU.
- Modelo C: GRU con variables agregadas.
- Prueba de permutación del historial.
- Evaluación por mecanismo de fraude.
- Selección provisional en validación.
- Conjunto de prueba todavía sellado.

## 5. El README no coincide con los resultados del notebook

### Problema

Los números documentados para el modelo A no coinciden con la última ejecución del notebook. Por ejemplo, el README anterior reportaba aproximadamente:

| Resultado | README anterior | Notebook combinado |
|---|---:|---:|
| AUC-PR de A | 0.7368 | 0.7281 |
| Umbral de A | 0.85 | 0.90 |
| Costo de A | Q299,100 | Q297,300 |

### Corrección

No conviene actualizar esos valores todavía. Primero se deben corregir las semillas y volver a ejecutar todo desde cero. Después, el README debe copiar exactamente las métricas definitivas de esa ejecución reproducible.

También debe incorporar los resultados de B y C, las pruebas de falsación, las limitaciones y las versiones del entorno. No debe mostrar métricas de *test* hasta que la evaluación final se haya ejecutado una sola vez.

## 6. Hay interpretaciones que deben formularse con más precisión

### 6.1 El orden temporal no parece importar únicamente en `escalada`

La mayor mejora de B frente a A ocurre en `escalada`, lo cual respalda la hipótesis principal. Sin embargo, la permutación también perjudica fuertemente a `rafaga`. Por eso, no sería correcto afirmar que el orden temporal solo es importante para `escalada`.

Una conclusión más precisa sería:

> La mayor ganancia de B frente a A se observa en el mecanismo de escalada, pero la prueba de permutación muestra que el orden temporal también aporta información importante para detectar ráfagas.

### 6.2 El modelo B presenta una limitación en `comercio_atipico`

En la ejecución revisada, B obtuvo un AUC-PR muy bajo y *recall* igual a cero para `comercio_atipico`. Esto debe informarse como una limitación concreta, no ocultarse dentro del promedio global.

### 6.3 La menor precisión de C puede estar justificada económicamente

El modelo C muestra menor precisión, pero mayor *recall* y menor costo. Esto resulta coherente con la función económica utilizada, porque un falso negativo cuesta Q4,200 y un falso positivo Q180; es decir, el falso negativo cuesta aproximadamente 23.3 veces más.

La conclusión debe explicar que C acepta más falsas alarmas para evitar fraudes omitidos y reducir el costo total.

## 7. Los resultados actuales deben volver a calcularse

### Problema

Aunque C cumple los criterios de validación en la ejecución actual, la corrección de las semillas puede modificar las métricas. Por eso, los resultados guardados no deberían presentarse todavía como definitivos.

### Corrección

Después de corregir la reproducibilidad:

1. Reiniciar el kernel.
2. Ejecutar todas las celdas en orden.
3. Repetir el proceso desde otro kernel limpio.
4. Comparar las métricas de ambas ejecuciones.
5. Fijar el modelo candidato, los parámetros de preprocesamiento y los umbrales.
6. Solo entonces habilitar la evaluación final en *test*.

## 8. El conjunto de prueba todavía no se ha evaluado

Esto está bien desde el punto de vista metodológico, pero significa que el proyecto aún no está completo. Antes de abrir el *test* se deben congelar:

- Arquitecturas de A, B y C.
- Pesos entrenados.
- Columnas y parámetros de preprocesamiento.
- Longitud de secuencia, relleno y columnas de eventos.
- Variables agregadas.
- Umbrales seleccionados en validación.
- Pruebas de falsación y métricas que se reportarán.

### Evaluación final que debe realizarse una sola vez

Con los modelos y umbrales ya congelados, se debe evaluar sobre las mismas observaciones objetivo del conjunto de prueba:

- AUC-PR de A, B y C.
- Precisión, *recall* y F1 con los umbrales fijados en validación.
- Costo económico.
- Prueba de permutación del historial para B.
- Resultados por mecanismo de fraude.

El resultado de *test* no debe utilizarse para cambiar el umbral, seleccionar otra arquitectura ni volver a entrenar buscando una métrica mejor.

## 9. Faltan artefactos para cerrar la entrega

Después de la evaluación final se deben guardar o documentar:

- `state_dict` del modelo candidato.
- Media y desviación usadas para normalizar variables.
- Vocabularios o mapeos de variables categóricas.
- Longitud de secuencia y estrategia de *padding*.
- Columnas de eventos y variables agregadas.
- Configuración y semilla del generador de datos.
- Umbral final seleccionado en validación.
- Versiones de Python y dependencias.
- `requirements.txt` o archivo equivalente.
- README actualizado con los resultados definitivos.
- Recomendación final: reemplazar, complementar o conservar el sistema actual.

## 10. Observaciones menores

### Resultados piloto no reproducidos

Algunas celdas de texto mencionan resultados aproximados de pruebas piloto que no aparecen respaldados por celdas ejecutadas. Conviene eliminar los números exactos o conservar el código y una tabla que permita reproducirlos.

### Etiquetas de prueba cargadas en memoria

La variable general de etiquetas incluye las del conjunto de prueba, aunque el código revisado no las utiliza durante el desarrollo. No parece existir una fuga práctica, pero para una separación más estricta se pueden mantener las etiquetas de desarrollo y prueba en objetos distintos hasta la evaluación final.

### Versiones del entorno

Se deben registrar las versiones exactas de las bibliotecas principales para facilitar la reproducción de los resultados.

## Aspectos que ya están bien implementados

No todo requiere cambios. Estos puntos se observaron correctamente resueltos:

- Las secuencias se construyen respetando el orden temporal y sin usar eventos futuros.
- La normalización se calcula con datos de entrenamiento.
- Los modelos se comparan sobre las mismas observaciones objetivo y el mismo horizonte.
- Los modelos generan una puntuación continua de riesgo.
- La hipótesis de C se declaró antes de abrir el conjunto de prueba.
- La permutación conserva la transacción actual y altera únicamente el historial.
- La prueba de permutación utiliza varias semillas.
- Se incluye una segunda prueba de falsación por mecanismo de fraude.
- El conjunto de prueba permanece sellado.

## Prioridad recomendada

| Prioridad | Cambio |
|---|---|
| Crítica | Fijar las semillas antes de crear B y C y controlar el `DataLoader`. |
| Alta | Corregir la descripción de C y agregar su evaluación por mecanismo. |
| Alta | Reejecutar dos veces desde kernels limpios y congelar el experimento. |
| Media | Actualizar la introducción y eliminar resultados piloto no reproducidos. |
| Media | Sincronizar README, dependencias y versiones con la ejecución definitiva. |
| Final | Ejecutar *test* una sola vez y completar los artefactos de entrega. |

## Conclusión

El proyecto tiene una base sólida y la evidencia preliminar favorece al modelo C por su menor costo de validación. No obstante, la selección todavía debe considerarse provisional hasta corregir la reproducibilidad, completar el análisis por mecanismo y ejecutar nuevamente el notebook desde cero. Solo después debe abrirse el conjunto de prueba y cerrarse la documentación final.
