# Microejercicios — HTTP, JSON y diseño de recursos

Trabajad por parejas. No hace falta levantar ningún servicio. En el ejercicio 3
sí haréis una comprobación breve con `json.loads()` o un validador local.
Conservad las decisiones: se reutilizarán en el laboratorio de clientes.

## 1. Tres formas de pedir una predicción

Comparad estos tres casos:

A. `infer_measurements(payload)` dentro del mismo programa Python.
B. Un cliente envía `POST /runPumpModel` a otro proceso mediante HTTP.
C. Un cliente envía `POST /v1/predictions` a otro proceso mediante HTTP.

Completad la tabla:

Un proceso es un programa en ejecución. En A todo ocurre en el mismo proceso;
en B y C, el cliente se comunica con el proceso servidor.

| Caso | ¿Sale del proceso Python? | ¿Usa HTTP? | ¿La ruta nombra una acción o un recurso? |
| --- | --- | --- | --- |
| A | No: es una llamada a una función dentro del mismo programa | No | No hay ruta HTTP; es una función local |
| B | Sí: hace una petición a la API | Sí | Acción: `runPumpModel` es un verbo ("ejecutar el modelo") |
| C | Sí: hace una petición a la API | Sí | Recurso: `predictions` es un sustantivo |

Para una API nueva elegiría C: el método HTTP (POST) expresa la operación y la
ruta nombra el recurso.

## 2. URL, path y query

```text
http://127.0.0.1:8000/v1/predictions/pred-42?include=explanation&limit=1
```

**TODO:** marcad scheme, host, port, path y cada parámetro de query. Después
decidid dónde pondríais:

- scheme: `http`
- host: `127.0.0.1`
- port: `8000`
- path: `/v1/predictions/pred-42`
- parámetros de query: `include=explanation` y `limit=1`

- el identificador de una predicción concreta: en el path
- un límite de resultados: en un parámetro de query
- cuatro medidas de una bomba: en el body JSON de la petición

**Comprobación:** las medidas estructuradas no deberían acabar en la URL.

## 3. JSON y Python

```python
{"machine_id": "pump-017", "ready": True, "comment": None, "axes": (1, 2)}
```

```json
{
   "machine_id": "pump-017",
   "ready": true,
   "comment": null,
   "axes": [1, 2]
}
```

JSON no tiene tuplas: las colecciones se representan como arrays con corchetes.
Comprobación:

```python
import json
json.loads('{"machine_id": "pump-017", "ready": true, "comment": null, "axes": [1, 2]}')
# {'machine_id': 'pump-017', 'ready': True, 'comment': None, 'axes': [1, 2]}
```

**TODO:** convertid esta expresión Python a JSON interoperable. Investigad las
formas JSON de booleano, nulo y colección. Comprobad el resultado con un
validador local o `json.loads()`.

## 4. Cuatro estados HTTP esenciales

Para cada caso, elegid solo entre `200`, `400`, `422` y `503`. Escribid el
código y una razón de una frase.

1. Predicción correcta y devuelta: código **200**; razón: la petición se ha
   procesado correctamente y la predicción se devuelve en el cuerpo.
2. Texto truncado o que no es JSON: código **400**; razón: el servidor no puede
   interpretar el cuerpo porque no es un JSON válido.
3. JSON válido, pero `vibration_mm_s` es la cadena `"alta"`: código **422**;
   razón: el JSON se puede leer, pero incumple el contrato de entrada.
4. Petición correcta, pero el modelo no está disponible temporalmente: código
   **503**; razón: el servicio está temporalmente no disponible.

## 5. Crear y consultar una predicción

Completad estas plantillas:

```text
Crear una predicción:    POST /v1/predictions
Consultar la predicción: GET  /v1/predictions/pred-42
```

¿Dónde van las mediciones: en el path, en la query o en el body JSON? ¿Dónde va
`pred-42`? ¿Qué podría pasar si se repite dos veces la creación? ¿Consultar dos
veces debería cambiar el estado del servidor?

- Al crear una nueva predicción el método es POST y las mediciones van en el
  body JSON de la petición.
- `pred-42` va en el path de la URL.
- Si se repite dos veces la creación, se obtendrían dos predicciones idénticas,
  diferenciadas únicamente por su id.
- No: consultar una predicción solo lee, no modifica datos.

- **segura:** está pensada solo para leer, sin cambiar el estado del servidor;
- **idempotente:** repetirla tiene el mismo efecto esperado que ejecutarla una
  sola vez.

Aplicad ambos términos a crear y consultar una predicción.

**POST (crear)**
- ¿Es segura? No, ya que modifica el estado del servidor.
- ¿Es idempotente? No, porque si envías la misma petición POST 5 veces seguidas,
  crearás 5 predicciones distintas.

**GET (consultar)**
- ¿Es segura? Sí, porque está diseñada únicamente para leer.
- ¿Es idempotente? Sí, aunque realices 100 veces un GET, el efecto sobre el
  servidor será siempre el mismo (ninguno).