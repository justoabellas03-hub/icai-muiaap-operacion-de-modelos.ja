import requests
import os
from dotenv import load_dotenv
import pandas as pd


load_dotenv()

BASE_URL = "https://opendata.aemet.es/opendata/api"

def get_env_data(url:str, params:Dict=None):
    API_KEY=os.getenv("API_KEY")

    headers={
        "api_key":API_KEY
    }
    response=requests.get(
        url="f{BASE_URL}{ENDPOINT}", 
        headers=headers,
    )
    response.raise_for_status()
    
    if info.get("estado") != 200:
        raise ValueError(f"Error de AEMET: {info.get('descripcion')}")



    info = response.json()
    datos=requests.get(info["datos"]
    datos.raise_for_status()
    datos.encoding = "latin-1"

    return datos.json()

if __name__ =="__main__":
    fecha_ini = "2019-10-01T00:00:00UTC"
    fecha_fin = "2019-10-30T23:59:59UTC"
    idema = "3194U"

    ENDPOINT = (f"/valores/climatologicos/diarios/datos/fechaini/{fecha_ini}/fechafin/{fecha_fin}/estacion/{idema}")
    datos=get_aemet_data(url)
    df=pd.DataFrame(datos)

