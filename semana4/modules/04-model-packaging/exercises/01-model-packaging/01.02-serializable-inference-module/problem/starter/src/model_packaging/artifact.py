"""Puntos de extensión del taller de serialización."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from model_packaging.preprocess import PREPROCESSING_VERSION, FEATURE_NAMES
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
import tempfile
import joblib
import shutil
from model_packaging.preprocess import preprocess_wine_request

from model_packaging.contracts import (
    QualityBand,
    WineQualityPrediction,
    WineQualityRequest,
)

ARTIFACT_SCHEMA_VERSION = "wine-quality-bundle-v1"
DEFAULT_BUNDLE_PATH = Path("assets/wine_quality_bundle")
MANIFEST_FILENAME = "manifest.json"
MODEL_FILENAME = "model.joblib"
OUTPUT_LABELS: tuple[QualityBand, ...] = (
    "needs_review",
    "acceptable",
    "excellent",
)


class WineQualityEstimator(Protocol):
    """Interfaz mínima que debe cumplir el estimador cargado."""

    def predict(self, features: list[list[float]]) -> Sequence[str]:
        """Devuelve una etiqueta por fila."""

    def predict_proba(self, features: list[list[float]]) -> Sequence[Sequence[float]]:
        """Devuelve probabilidades por fila."""


class ArtifactManifest(BaseModel):
    """TODO: declara y valida los metadatos del bundle."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: str
    model_version: str = Field(min_length=1)
    preprocessing_version: str
    feature_names: tuple[str, ...]
    output_labels: tuple[QualityBand, ...]
    estimator_type: str = Field(min_length=1)

    @field_validator("feature_names")
    @classmethod
    def _check_features(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        if tuple(v) != tuple(FEATURE_NAMES):
            raise ValueError(f"feature_names no coincide con FEATURE_NAMES: {v}")
        return v

@dataclass(frozen=True)
class LoadedModelBundle:
    """Bundle cargado; no modificar esta interfaz pública."""

    estimator: WineQualityEstimator
    manifest: ArtifactManifest


def create_manifest(
    estimator: WineQualityEstimator, model_version: str
) -> ArtifactManifest:
    """TODO: devuelve un manifiesto compatible con el contrato."""
    return ArtifactManifest(
        schema_version=ARTIFACT_SCHEMA_VERSION,
        model_version=str(model_version),
        preprocessing_version=PREPROCESSING_VERSION,
        feature_names=FEATURE_NAMES,
        output_labels=OUTPUT_LABELS,
        estimator_type=type(estimator).__name__
    )


def save_model_bundle(bundle_path: Path, estimator: WineQualityEstimator,manifest: ArtifactManifest | None = None,) -> ArtifactManifest:
    bundle_path=Path(bundle_path)
    if manifest is None:
        manifest=create_manifest(estimator, model_version="0.1.0")
        
    manifest=ArtifactManifest.model_validate(manifest.model_dump())
    if not (hasattr(estimator,"predict") and hasattr(estimator, "predict_proba")):
        raise TypeError("El estimador debe tener predict() y predict_proba")
    if manifest.estimator_type != type(estimator).__name__:
        raise ValueError(f"estimator_type {manifest.estimator_type!r} no coincide con {type(estimator).__name__!r}")
        
    bundle_path.parent.mkdir(parents=True, exist_ok=True) ##Crea la carpeta padre si no existe todavía 

        # Crea una carpeta temporal con nombre único (p. ej. models/.tmp_bundle_x8k2) junto al destino.
        # Va en la misma carpeta padre para que luego renombrarla sea instantáneo (mismo disco)
    tmp_dir = Path(tempfile.mkdtemp(prefix=".tmp_bundle_", dir=bundle_path.parent))
        # Todo lo que puede fallar va dentro de try, para poder limpiar si algo sale mal
        
    try:
        # Escribe manifest.json dentro de la carpeta temporal.
        # model_dump_json(indent=2) convierte el manifest en texto JSON legible (con sangría)
        (tmp_dir / MANIFEST_FILENAME).write_text(
            manifest.model_dump_json(indent=2), encoding="utf-8"
        )

        # Guarda el modelo entrenado como model.joblib dentro de la carpeta temporal
        joblib.dump({"estimator":estimator}, tmp_dir / MODEL_FILENAME)

        if bundle_path.exists():
                # Nombre para apartar el bundle viejo, p. ej. models/wine_quality_bundle.old
            backup = bundle_path.with_name(bundle_path.name + ".old")

                # Si quedó un .old de una ejecución anterior que falló, lo borramos primero
            if backup.exists():
                shutil.rmtree(backup)

                # Apartamos el bundle viejo renombrándolo a .old
                # (en Windows no se puede renombrar una carpeta encima de otra que ya existe)
            bundle_path.rename(backup)

                # Ponemos la carpeta temporal (ya completa) en el sitio definitivo
            tmp_dir.rename(bundle_path)

                # El nuevo bundle ya está en su sitio: borramos el viejo
            shutil.rmtree(backup)

            # Caso B: no existía ningún bundle antes
        else:
                # Basta con renombrar la carpeta temporal a la ruta definitiva
            tmp_dir.rename(bundle_path)


    except Exception:
        shutil.rmtree(tmp_dir, ignore_errors=True)

        # Relanzamos el error original para que quien llamó a la función sepa que falló
        raise
    # Todo ha ido bien: devolvemos el manifest que se ha guardado en disco
    return manifest





def load_model_bundle(bundle_path: Path) -> LoadedModelBundle:
    """TODO: valida el manifiesto antes de cargar el estimador."""
    bundle_path=Path(bundle_path)

    manifest_path=bundle_path/MANIFEST_FILENAME
    model_path=bundle_path/MODEL_FILENAME

    #Comprobar si las rutas existen y esstán completas
    if not bundle_path.is_dir():
        raise FileNotFoundError(f"No existe la carpeta del bundle")
    if not manifest_path.is_file():
        raise FileNotFoundError(f"No existe el archivo {MANIFEST_FILENAME} en la carpeta bundle")
    if not model_path.is_file():
        raise FileNotFoundError(f"No existe el archivo {MODEL_FILENAME} en la carpeta bundle")

    texto=manifest_path.read_text(encoding="utf-8")
    try:
        manifest=ArtifactManifest.model_validate_json(texto)
    except ValidationError as e:
        raise ValueError(f"Manifest inválido en {manifest_path}: {e}") from e

    payload=joblib.load(model_path)
    if not isinstance(payload, Mapping) or "estimator" not in payload:
        raise ValueError("model.joblib debe contener un diccionario con la clave 'estimator'.")

    if not (hasattr(estimator, "predict") and hasattr(estimator, "predict_proba")):
        raise TypeError("El estimador cargado no tiene predict() y predict_proba()")
    if type(estimator).__name__ != manifest.estimator_type:
        raise ValueError(
            f"El manifest dice {manifest.estimator_type!r} pero se cargó "
            f"{type(estimator).__name__!r}"
        )
    return LoadedModelBundle(estimator=estimator, manifest=manifest)


def infer_wine_quality(
    bundle: LoadedModelBundle,
    request: WineQualityRequest,
) -> WineQualityPrediction:
    """TODO: preprocesa, invoca el estimador y valida la respuesta."""
    manifest=bundle.manifest
    estimator=bundle.estimator
    
    entrada_procesada=preprocess_wine_request(request)
    matrix=[entrada_procesada.as_vector()]
    
    pred=estimator.predict(matrix)[0]
    proba=estimator.predict_proba(matrix)[0]

    # 3) Validaciones que dependen del bundle
    etiqueta = str(pred)
    if etiqueta not in manifest.output_labels:
        raise ValueError(f"El modelo devolvió {etiqueta!r}, que no está en {manifest.output_labels}")


    return WineQualityPrediction(
        quality_band=etiqueta,
        confidence=max(proba),
        model_version=manifest.model_version,
        preprocessing_version=PREPROCESSING_VERSION

    )


    

   