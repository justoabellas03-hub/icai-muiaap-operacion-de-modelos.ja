"""Punto de extensión del CLI de inferencia sobre un bundle."""

from __future__ import annotations

import argparse
from pathlib import Path
import csv
import pandas as pd

from model_packaging.artifact import DEFAULT_BUNDLE_PATH
from pydantic import ValidationError 
from model_packaging.contracts import WineQualityRequest
from model_packaging.preprocess import preprocess_wine_request, FEATURE_NAMES, PREPROCESSING_VERSION
from model_packaging.artifact import load_model_bundle, infer_wine_quality


def predict_file(
    input_path: Path,
    output_path: Path,
    bundle_path: Path,
) -> int:
    validas = []
    cabecera_esperada = ["sample_id", *FEATURE_NAMES]

    with open(input_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        
        if reader.fieldnames!=cabecera_esperada:
            raise ValueError(f"Las columnas del CSV no son las esperadas: {reader.fieldnames}")
        for n_fila, fila in enumerate(reader, start=2):
            sample_id=fila.pop("sample_id")
            try:
                request=WineQualityRequest(**fila)
                validas.append(request)
            except ValidationError as e:
                raise ValueError(f"Error :{e} en la fila {n_fila}")

    loaded_bundle=load_model_bundle(bundle_path)        

    salidas=[]
    for r in validas:
        try:
            salidas.append(infer_wine_quality(loaded_bundle,r))
        except ValidationError as error:
            raise ValueError(f"Error de salida:{error}")
    
    df = pd.DataFrame([s.model_dump() for s in salidas])
    df.to_csv(output_path, index=False)

    return len(salidas)


def parse_args() -> argparse.Namespace:
    """Declara la interfaz del comando público."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--bundle", default=DEFAULT_BUNDLE_PATH, type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    raise SystemExit(
        predict_file(
            input_path=arguments.input,
            output_path=arguments.output,
            bundle_path=arguments.bundle,
        )
    )
