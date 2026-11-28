"""Carga del bundle: casos que deben fallar antes de predecir (corrección S4.2)."""

import json
import subprocess
import sys
from pathlib import Path

import joblib
import pytest
from test_artifact import make_estimator, make_request
from test_predict_file import write_bundle, write_input

from model_packaging.artifact import (
    MANIFEST_FILENAME,
    MODEL_FILENAME,
    infer_wine_quality,
    load_model_bundle,
)
from model_packaging.preprocess import PREPROCESSING_VERSION

REAL_BUNDLE = Path(__file__).resolve().parents[1] / "assets" / "wine_quality_bundle"


def _edit_manifest(bundle_path: Path, **changes: str) -> None:
    manifest_path = bundle_path / MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(changes)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")


def test_load_round_trip_returns_estimator(tmp_path: Path) -> None:
    bundle_path = tmp_path / "bundle"
    write_bundle(bundle_path)

    loaded = load_model_bundle(bundle_path)
    prediction = infer_wine_quality(loaded, make_request())

    assert type(loaded.estimator).__name__ == "DummyClassifier"
    assert prediction.preprocessing_version == PREPROCESSING_VERSION


@pytest.mark.parametrize("missing", [MANIFEST_FILENAME, MODEL_FILENAME])
def test_load_rejects_a_bundle_with_a_missing_file(
    tmp_path: Path, missing: str
) -> None:
    bundle_path = tmp_path / "bundle"
    write_bundle(bundle_path)
    (bundle_path / missing).unlink()

    with pytest.raises(FileNotFoundError, match=missing):
        load_model_bundle(bundle_path)


def test_load_rejects_a_changed_preprocessing_version(tmp_path: Path) -> None:
    bundle_path = tmp_path / "bundle"
    write_bundle(bundle_path)
    _edit_manifest(bundle_path, preprocessing_version="wine-red-features-v2")

    with pytest.raises(ValueError, match="preprocessing_version"):
        load_model_bundle(bundle_path)


def test_load_rejects_an_unknown_schema_version(tmp_path: Path) -> None:
    bundle_path = tmp_path / "bundle"
    write_bundle(bundle_path)
    _edit_manifest(bundle_path, schema_version="wine-quality-bundle-v0")

    with pytest.raises(ValueError, match="schema_version"):
        load_model_bundle(bundle_path)


def test_load_rejects_a_truncated_model_file(tmp_path: Path) -> None:
    bundle_path = tmp_path / "bundle"
    write_bundle(bundle_path)
    model_path = bundle_path / MODEL_FILENAME
    content = model_path.read_bytes()
    model_path.write_bytes(content[: len(content) // 2])

    with pytest.raises(ValueError, match="No se pudo cargar"):
        load_model_bundle(bundle_path)


def test_load_rejects_a_payload_without_estimator(tmp_path: Path) -> None:
    bundle_path = tmp_path / "bundle"
    write_bundle(bundle_path)
    joblib.dump({"model": make_estimator()}, bundle_path / MODEL_FILENAME)

    with pytest.raises(ValueError, match="estimator"):
        load_model_bundle(bundle_path)


def test_cli_reports_an_incomplete_bundle_without_traceback(tmp_path: Path) -> None:
    bundle_path = tmp_path / "bundle"
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "predictions.csv"
    write_bundle(bundle_path)
    write_input(input_path)
    (bundle_path / MODEL_FILENAME).unlink()

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "model_packaging.predict_file",
            "--bundle",
            str(bundle_path),
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert MODEL_FILENAME in completed.stderr
    assert "Traceback" not in completed.stderr
    assert not output_path.exists()


@pytest.mark.skipif(not REAL_BUNDLE.is_dir(), reason="bundle real no disponible")
def test_real_bundle_loads_and_predicts() -> None:
    loaded = load_model_bundle(REAL_BUNDLE)
    prediction = infer_wine_quality(loaded, make_request())

    assert loaded.manifest.estimator_type == type(loaded.estimator).__name__
    assert prediction.quality_band in loaded.manifest.output_labels
    assert 0.0 <= prediction.confidence <= 1.0
