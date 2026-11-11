# Respuestas — Microejercicios HTTP, JSON y diseño de recursos

## 1. Tres formas de pedir una predicción

| Caso | ¿Sale del proceso Python? | ¿Usa HTTP? | ¿La ruta nombra una acción o un recurso? |
| --- | --- | --- | --- |
| A | No | No | No aplica (no hay ruta, es una función) |
| B |  |  |  |
| C |  |  |  |

¿Qué puede fallar en B y C que no puede fallar en A?

-

## 2. URL, path y query

`http://127.0.0.1:8000/v1/predictions/pred-42?include=explanation&limit=1`

- scheme:
- host:
- port:
- path:
- parámetros de query:

¿Dónde pondría...?

- el identificador de una predicción concreta:
- un límite de resultados:
- cuatro medidas de una bomba:

## 3. JSON y Python

Expresión Python original:

```python
{"machine_id": "pump-017", "ready": True, "comment": None, "axes": (1, 2)}
```

Versión JSON:

```json

```

Comprobación con `json.loads()`:

-

## 4. Cuatro estados HTTP esenciales

1. Predicción correcta y devuelta: código ____; razón:
2. Texto truncado o que no es JSON: código ____; razón:
3. JSON válido, pero `vibration_mm_s` es `"alta"`: código ____; razón:
4. Petición correcta, pero el modelo no está disponible: código ____; razón:

## 5. Crear y consultar una predicción

```text
Crear una predicción:    [MÉTODO] /v1/[RECURSO]
Consultar la predicción: [MÉTODO] /v1/[RECURSO]/[ID]
```

- ¿Dónde van las mediciones (path, query o body)?
- ¿Dónde va `pred-42`?
- ¿Qué podría pasar si se repite dos veces la creación?
- ¿Consultar dos veces debería cambiar el estado del servidor?
- Crear: ¿segura? ¿idempotente?
- Consultar: ¿segura? ¿idempotente?
