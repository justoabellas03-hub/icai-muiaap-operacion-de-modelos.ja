import requests
import os
from dotenv import load_dotenv
import pandas as pd


load_dotenv()

BASE_URL = "https://opendata.aemet.es/opendata/api"
TIMEOUT = 30  # segundos máximos de espera por petición


def get_env_data(url: str, params: dict = None):
    API_KEY = os.getenv("API_KEY")
    print("API key cargada:", bool(API_KEY))  # diagnóstico: ¿se ha leído el .env?

    headers = {
        "api_key": API_KEY
    }

    # Paso 1: pedir el endpoint (devuelve una URL con los datos, no los datos)
    print("Paso 1: llamando a", f"{BASE_URL}{url}")
    response = requests.get(
        url=f"{BASE_URL}{url}",
        headers=headers,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    print("Paso 1 status:", response.status_code)

    info = response.json()
    print("Paso 1 respuesta:", info)

    if info.get("estado") != 200:
        raise ValueError(f"Error de AEMET: {info.get('descripcion')}")

    print("Paso 2: descargando datos desde", info["datos"])
    datos = requests.get(info["datos"], timeout=TIMEOUT)
    datos.raise_for_status()
    datos.encoding = "latin-1"
    print("Paso 2 status:", datos.status_code)
    print("Paso 2, primeros caracteres:", datos.text[:300])

    return datos.json()


if __name__ == "__main__":
    fecha_ini = "2019-10-01T00:00:00UTC"
    fecha_fin = "2019-10-30T23:59:59UTC"
    idema = "3194U"

    ENDPOINT = (f"/valores/climatologicos/diarios/datos/fechaini/{fecha_ini}/fechafin/{fecha_fin}/estacion/{idema}")
    datos = get_env_data(ENDPOINT)
    print("Registros recibidos:", len(datos))

    df = pd.DataFrame(datos)
    print(df)