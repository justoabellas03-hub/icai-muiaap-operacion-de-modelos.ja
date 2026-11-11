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
| A | No:es una llamada a una funcion dentro del mismo programa | No | No hay ruta con accion  |
| B | Sí: hace una peticion a la api | SI | Sí en la rutra se normbra lacción POST |
| C | Sí, hace una peticion a la api  | Sí | Sí en la ruta se normbra lacción POST |



## 2. URL, path y query

```text
http://127.0.0.1:8000/v1/predictions/pred-42?include=explanation&limit=1
```

**TODO:** marcad scheme, host, port, path y cada parámetro de query. Después
decidid dónde pondríais:

scheme:http
host:127.0.0.1 
port:8000
path:/v1/predictions/pred-42
params:?include=explanation&limit=1

- el identificador de una predicción concreta;path
- un límite de resultados;parámetros
- cuatro medidas de una bomba:En el body de la query

**Comprobación:** las medidas estructuradas no deberían acabar en la URL.

## 3. JSON y Python

```python
{"machine_id": "pump-017", "ready": True, "comment": None, "axes": (1, 2)}
```
```python
{
   "machine_id":"pump-017",
   "ready":true,
   "comment": null,
   "axes": (1, 2)
}
```


**TODO:** convertid esta expresión Python a JSON interoperable. Investigad las
formas JSON de booleano, nulo y colección. Comprobad el resultado con un
validador local o `json.loads()`.

## 4. Cuatro estados HTTP esenciales

Para cada caso, elegid solo entre `200`, `400`, `422` y `503`. Escribid el
código y una razón de una frase.

1. Predicción correcta y devuelta: código _200___; razón: ____________________.
2. Texto truncado o que no es JSON: código __400__; razón: _Este fallo supone que el json de entrada no es el esparado o que no es un json___________________.
3. JSON válido, pero `vibration_mm_s` es la cadena `"alta"`: código _422___;
   razón: _JSON válido que incumple el contrato___________________.
4. Petición correcta, pero el modelo no está disponible temporalmente: código
   _503___; razón: __servicio temporalmente no disponible__________________.

## 5. Crear y consultar una predicción

Completad estas plantillas:

```text
Crear una predicción:    [MÉTODO] /v1/[RECURSO] POST /v1/predictions
Consultar la predicción: [MÉTODO] /v1/[RECURSO]/[ID] GET /v1/predictions/pred-42
```

¿Dónde van las mediciones: en el path, en la query o en el body JSON? ¿Dónde va
`pred-42`? ¿Qué podría pasar si se repite dos veces la creación? ¿Consultar dos
veces debería cambiar el estado del servidor?
Al crear una nueva predición el método es POST y por norma la mediciones irán ecomo parte del body
pred-42 a dentro de la url
Se obtendría dos predicciones idénticas unicamente difernciadas por su id.
No consuktar una predicción  solo lee no modifica datos.


- **segura:** está pensada solo para leer, sin cambiar el estado del servidor;
- **idempotente:** repetirla tiene el mismo efecto esperado que ejecutarla una
  sola vez.

Aplicad ambos términos a crear y consultar una predicción.
POST:¿es segura? No, ya que modifica el estado del servidor.
¿es idempotente?No, porque si envías la misma petición POST 5 veces seguidas, crearás 5 predicciones distintas en la base de datos

GET:¿es segura? Sí, porque está diseñada únicamente para leer.
   ¿es idempotente?Sí, aunque realices 100 veces un get el resultado de la petición será siempre el mismo.
