from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import pandas as pd
from pydantic import ValidationError

from model_packaging.artifact import (
    DEFAULT_BUNDLE_PATH,
    infer_wine_quality,
    load_model_bundle,
)
from model_packaging.contracts import WineQualityRequest
from model_packaging.preprocess import FEATURE_NAMES


def predict_file(input_path: Path, output_path: Path, bundle_path: Path) -> int:
    """Valida todas las filas, predice y escribe el CSV solo al final."""

    cabecera_esperada = ["sample_id", *FEATURE_NAMES]
    validas: list[tuple[str, WineQualityRequest]] = []

    with open(input_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != cabecera_esperada:
            raise ValueError(
                f"Las columnas del CSV no son las esperadas: {reader.fieldnames}"
            )
        for n_fila, fila in enumerate(reader, start=2):
            sample_id = fila.pop("sample_id")
            try:
                validas.append((sample_id, WineQualityRequest(**fila)))
            except ValidationError as error:
                raise ValueError(f"fila {n_fila}: {error}") from error

    bundle = load_model_bundle(bundle_path)

    salidas = []
    for sample_id, request in validas:
        try:
            prediccion = infer_wine_quality(bundle, request)
        except ValidationError as error:
            raise ValueError(f"salida inválida para {sample_id}: {error}") from error
        salidas.append({"sample_id": sample_id, **prediccion.model_dump()})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(salidas).to_csv(output_path, index=False)
    return len(salidas)


def parse_args() -> argparse.Namespace:
    """Declara la interfaz del comando público."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--bundle", default=DEFAULT_BUNDLE_PATH, type=Path)
    return parser.parse_args()


def main() -> int:
    """Ejecuta el CLI con errores legibles y código de salida correcto."""

    arguments = parse_args()
    try:
        n = predict_file(arguments.input, arguments.output, arguments.bundle)
    except (FileNotFoundError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(f"{n} predicciones escritas en {arguments.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())