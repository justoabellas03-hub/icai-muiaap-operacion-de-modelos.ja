# S10.7 — Informe de carga

> **Pendiente de medir (S10.7c):** arranca la API y ejecuta Locust con
> `--csv reports/s10` (comandos abajo), versiona los CSV generados y copia en
> la tabla de resultados las cifras de **tu** `s10_stats.csv`. La estimación
> previa de este informe es un cálculo, no una medida: compárala con lo medido.

## Cómo se ha medido

| Dato | Valor |
| --- | --- |
| Comando de la API | `uv run fastapi dev` (1 proceso) |
| Comando de Locust | `uv run --group load locust -f locustfile.py --headless -u 20 -r 5 -t 1m --host http://127.0.0.1:8000 --csv reports/s10` |
| Cliente usado | `front` (scope `predict`), clave en `LOCUST_API_KEY` |
| `rate_limit_per_minute` del cliente | 60 (valor de `.env.example`) |
| Máquina | _pendiente: CPU y sistema operativo_ |

En PowerShell la clave se fija antes de lanzar Locust:

```powershell
$env:LOCUST_API_KEY="<clave-front-de-tu-.env>"
uv run --group load locust -f locustfile.py --headless -u 20 -r 5 -t 1m --host http://127.0.0.1:8000 --csv reports/s10
```

Archivos generados por Locust y versionados junto a este informe:
`s10_stats.csv`, `s10_failures.csv` y `s10_stats_history.csv`.

## Estimación previa (cálculo, no medida)

- 20 usuarios con `wait_time = between(0.5, 2)` esperan 1,25 s de media, así
  que cada uno lanza unas 0,8 tareas/s: unas 16 peticiones/s en total y unas
  900 en el minuto (descontando los 4 s de rampa a 5 usuarios/s).
- Con pesos 8:1:1 serían unas 720 predicciones válidas, 90 inválidas y 90
  `GET /health`.
- Las predicciones válidas **y** las inválidas consumen cuota (el límite se
  comprueba antes de validar el cuerpo): unas 810 peticiones contra un límite
  de 60/min. Pasarían unas 60 y el resto recibiría `429`: un `% 429` cercano
  al 92 %.
- La fila `/v1/predictions [422]` también mostrará muchos fallos: la mayoría
  de esos payloads reciben `429` antes de llegar a la validación.

## Resultados

Copia los valores de la fila `POST /v1/predictions` y de `Aggregated` de
`s10_stats.csv`.

| Endpoint | Peticiones | RPS | p50 (ms) | p95 (ms) | Fallos | % 429 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `POST /v1/predictions` | _pendiente_ | | | | | |
| `/v1/predictions [422]` | _pendiente_ | | | | | — |
| `GET /health` | _pendiente_ | | | | | — |
| Aggregated | _pendiente_ | | | | | |

`% 429` = fallos `429` de `s10_failures.csv` / peticiones de
`POST /v1/predictions` × 100.

## Análisis (5–10 líneas)

_Completar con las cifras medidas. Guion de lo que hay que contrastar:_

- **Cuota frente a demanda:** el límite deja pasar 60 peticiones por minuto
  del cliente `front` y Locust pide del orden de 800 que consumen cuota; el
  `% 429` medido debería rondar el 92 % de la estimación. Si se aleja, revisa
  si la prueba cruzó el final de la ventana (se reabre a los 60 s de la
  primera petición y entran otras 60).
- **Latencia:** `GET /health` no pasa por autenticación ni rate limit;
  `POST /v1/predictions` sí, y además valida e infiere. Los `429` son muy
  baratos (se rechazan antes del modelo), así que bajan el p50 agregado de las
  predicciones: compáralo con el p95.
- **Dos workers:** con `fastapi run --workers 2` cada proceso tiene su propio
  contador en memoria, así que el límite efectivo se duplica (hasta 120/min) y
  `GET /v1/admin/usage` solo informa del proceso que responde. Un límite
  global exige estado compartido (Redis) o aplicarlo en el API gateway.
- **Medir capacidad y no la política de cuotas:** usaría un cliente de carga
  propio (por ejemplo `loadtest`, solo con scope `predict`) con un
  `rate_limit_per_minute` muy alto, para que ningún `429` enmascare la
  latencia y el RPS reales del servicio.
