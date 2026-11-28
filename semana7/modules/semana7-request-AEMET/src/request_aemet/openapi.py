import requests
import os
from dotenv import load_dotenv
import pandas as pd


load_dotenv()

BASE_URL = "https://opendata.aemet.es/opendata/api"
TIMEOUT = 30  # segundos máximos de espera por petición

# Endpoint del inventario de estaciones (colección valores-climatológicos).
INVENTARIO_ENDPOINT = "/valores/climatologicos/inventarioestaciones/todasestaciones"
ESTACION_OBJETIVO = "MADRID, CIUDAD UNIVERSITARIA"


def get_api_key() -> str:
    API_KEY = os.getenv("API_KEY")
    if not API_KEY:
        raise RuntimeError(
            "Falta la variable de entorno API_KEY: copia .env.example a .env "
            "y pon tu API key de la AEMET (no la subas al repositorio)."
        )
    return API_KEY


def get_env_data(url: str, params: dict | None = None):
    # La API key se envía como query string (?api_key=...), tal y como pide el
    # enunciado y la documentación de la AEMET, y no como cabecera HTTP.
    # requests construye la URL final a partir de params.
    query = {**(params or {}), "api_key": get_api_key()}

    # Paso 1: pedir el endpoint (devuelve una URL con los datos, no los datos).
    # No se imprime response.url porque incluiría la API key.
    print("Paso 1: llamando a", f"{BASE_URL}{url}")
    response = requests.get(
        url=f"{BASE_URL}{url}",
        params=query,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    print("Paso 1 status:", response.status_code)

    info = response.json()
    print("Paso 1 respuesta:", {k: v for k, v in info.items() if k != "datos"})

    if info.get("estado") != 200:
        raise ValueError(f"Error de AEMET: {info.get('descripcion')}")

    # Paso 2: la URL de "datos" es temporal y ya no necesita la API key.
    print("Paso 2: descargando datos desde", info["datos"])
    datos = requests.get(info["datos"], timeout=TIMEOUT)
    datos.raise_for_status()
    datos.encoding = "latin-1"
    print("Paso 2 status:", datos.status_code)
    print("Paso 2, primeros caracteres:", datos.text[:300])

    return datos.json()


def buscar_indicativo(estaciones: list[dict], nombre: str = ESTACION_OBJETIVO) -> str:
    """Devuelve el indicativo (idema) de la estación cuyo nombre coincide."""
    objetivo = nombre.strip().upper()
    coincidencias = [
        estacion
        for estacion in estaciones
        if str(estacion.get("nombre", "")).strip().upper() == objetivo
    ]
    if not coincidencias:
        raise ValueError(f"No se ha encontrado la estación {nombre!r} en el inventario")
    if len(coincidencias) > 1:
        indicativos = [estacion.get("indicativo") for estacion in coincidencias]
        raise ValueError(f"Hay varias estaciones llamadas {nombre!r}: {indicativos}")
    return coincidencias[0]["indicativo"]


def climatologias_diarias(fecha_ini: str, fecha_fin: str, idema: str):
    endpoint = (
        f"/valores/climatologicos/diarios/datos/fechaini/{fecha_ini}"
        f"/fechafin/{fecha_fin}/estacion/{idema}"
    )
    return get_env_data(endpoint)


if __name__ == "__main__":
    # Fechas del enunciado (fechaFinStr = 2019-10-30T23:59:59UTC).
    fecha_ini = "2019-10-01T00:00:00UTC"
    fecha_fin = "2019-10-30T23:59:59UTC"

    # Paso A: inventario de estaciones -> indicativo (idema) de Ciudad Universitaria.
    estaciones = get_env_data(INVENTARIO_ENDPOINT)
    print("Estaciones en el inventario:", len(estaciones))
    idema = buscar_indicativo(estaciones)
    print(f"Indicativo de {ESTACION_OBJETIVO}: {idema}")

    # Paso B: climatologías diarias de esa estación en octubre de 2019.
    datos = climatologias_diarias(fecha_ini, fecha_fin, idema)
    print("Registros recibidos:", len(datos))

    df = pd.DataFrame(datos)
    print(df)
