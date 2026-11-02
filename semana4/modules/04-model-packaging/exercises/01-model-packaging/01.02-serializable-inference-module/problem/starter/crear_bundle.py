"""Convierte el joblib legado de la semana 3 en un bundle (model.joblib + manifest.json)."""

from pathlib import Path

import joblib

from model_packaging.artifact import create_manifest, save_model_bundle

legacy = joblib.load("assets/models/wine_quality_classifier.joblib")
print("Contenido del joblib legado:", list(legacy))

estimator = legacy["estimator"]
manifest = create_manifest(estimator, model_version=legacy["model_version"])
save_model_bundle(Path("assets/wine_quality_bundle"), estimator, manifest)
print("Bundle creado en assets/wine_quality_bundle")
