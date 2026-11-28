# Práctica AEMET — Requests

Climatología diaria de la estación **MADRID, CIUDAD UNIVERSITARIA** del
1 al 30 de octubre de 2019 con `requests` y la API OpenData de la AEMET.

## Preparación

```bash
cd semana7/modules/semana7-request-AEMET
uv sync
cp src/request_aemet/.env.example src/request_aemet/.env   # y pon tu API key
```

`.env` está en `.gitignore`: la API key no se sube al repositorio.

## Ejecución

```bash
uv run python -m request_aemet.openapi
```

El script hace dos llamadas a la API, cada una con su paso de descarga:

1. **Inventario de estaciones**
   (`/valores/climatologicos/inventarioestaciones/todasestaciones`). Busca en
   el listado la estación cuyo `nombre` es `MADRID, CIUDAD UNIVERSITARIA` y
   toma su `indicativo` (idema): `3194U`.
2. **Climatologías diarias**
   (`/valores/climatologicos/diarios/datos/fechaini/{fechaIniStr}/fechafin/{fechaFinStr}/estacion/{idema}`)
   con `fechaIniStr = 2019-10-01T00:00:00UTC`,
   `fechaFinStr = 2019-10-30T23:59:59UTC` (las fechas del enunciado) y el
   indicativo del paso anterior.

En las dos, la API key va como **query string** (`?api_key=...`), con
`requests.get(..., params={"api_key": API_KEY})`, no como cabecera. La
respuesta de la AEMET trae una URL temporal en `datos`, que se descarga en una
segunda petición que ya no necesita la key.

### Búsqueda manual (comprobación)

Para comprobar el indicativo a mano: ejecutar la primera llamada, abrir la URL
de `datos` que devuelve y buscar `"CIUDAD UNIVERSITARIA"`. La entrada es la de
`"nombre": "MADRID, CIUDAD UNIVERSITARIA"` con `"indicativo": "3194U"`. El
script hace esa misma búsqueda con `buscar_indicativo()`.

## Pruebas

Las pruebas no llaman a la AEMET: sustituyen `requests.get` por un doble y
comprueban que la key va en `params` y no en `headers`, que la estación se
encuentra en el inventario y que los errores (sin `API_KEY`, `estado` distinto
de 200, estación inexistente) se notifican.

```bash
uv run --with pytest pytest -q
```
