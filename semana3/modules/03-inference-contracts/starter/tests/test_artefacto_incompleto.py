"""Carga controlada de artefactos incompletos o dañados (corrección S3.2).

Cada caso debe terminar con código 2, un mensaje que explique el problema y
sin escribir el CSV de salida, igual que los errores de contrato de entrada.
"""

from pathlib import Path

import joblib
import pytest
from sklearn.dummy import DummyClassifier
from test_predict_file import (
    EXPECTED_FEATURE_NAMES,
    run_predict_file,
    write_input_csv,
    write_instructor_model,
)


def _estimator() -> DummyClassifier:
    estimator = DummyClassifier(strategy="constant", constant="acceptable")
    estimator.fit([[0.0] * len(EXPECTED_FEATURE_NAMES)], ["acceptable"])
    return estimator


def _assert_controlled_failure(completed, output_path: Path, fragment: str) -> None:
    assert completed.returncode == 2
    assert fragment in completed.stderr
    assert "Traceback" not in completed.stderr
    assert not output_path.exists()


@pytest.mark.parametrize("missing_key", ["model_version", "feature_names"])
def test_rejects_artifact_without_required_key(
    tmp_path: Path, missing_key: str
) -> None:
    artifact = {
        "estimator": _estimator(),
        "feature_names": list(EXPECTED_FEATURE_NAMES),
        "model_version": "wine-quality-rf-v1",
    }
    del artifact[missing_key]
    model_path = tmp_path / "incomplete.joblib"
    input_path = tmp_path / "inference_samples.csv"
    output_path = tmp_path / "predictions.csv"
    joblib.dump(artifact, model_path)
    write_input_csv(input_path)

    completed = run_predict_file(model_path, input_path, output_path)

    _assert_controlled_failure(completed, output_path, missing_key)


def test_rejects_artifact_without_estimator_without_traceback(tmp_path: Path) -> None:
    model_path = tmp_path / "no_estimator.joblib"
    input_path = tmp_path / "inference_samples.csv"
    output_path = tmp_path / "predictions.csv"
    joblib.dump(
        {"feature_names": list(EXPECTED_FEATURE_NAMES), "model_version": "v1"},
        model_path,
    )
    write_input_csv(input_path)

    completed = run_predict_file(model_path, input_path, output_path)

    _assert_controlled_failure(completed, output_path, "clasificador compatible")


def test_rejects_truncated_artifact(tmp_path: Path) -> None:
    complete_path = tmp_path / "complete.joblib"
    model_path = tmp_path / "truncated.joblib"
    input_path = tmp_path / "inference_samples.csv"
    output_path = tmp_path / "predictions.csv"
    write_instructor_model(complete_path)
    content = complete_path.read_bytes()
    model_path.write_bytes(content[: len(content) // 2])
    write_input_csv(input_path)

    completed = run_predict_file(model_path, input_path, output_path)

    _assert_controlled_failure(
        completed, output_path, "No se pudo cargar el artefacto"
    )


def test_rejects_missing_artifact_file(tmp_path: Path) -> None:
    input_path = tmp_path / "inference_samples.csv"
    output_path = tmp_path / "predictions.csv"
    write_input_csv(input_path)

    missing_path = tmp_path / "no_existe.joblib"

    completed = run_predict_file(missing_path, input_path, output_path)

    _assert_controlled_failure(
        completed, output_path, "No se pudo cargar el artefacto"
    )
