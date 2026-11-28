"""TODO: carga del .joblib e inferencia sobre características preparadas."""
import joblib
from model_inference.preprocess import FEATURE_NAMES
from model_inference.contracts import WineQualityRequest, WineQualityPrediction
from model_inference.preprocess import preprocess_wine_request, PREPROCESSING_VERSION

DEFAULT_MODEL_PATH = "model/wine_quality_classifier.joblib"

# Claves que debe tener el artefacto para poder predecir y trazar la versión.
REQUIRED_ARTIFACT_KEYS = ("estimator", "feature_names", "model_version")


def load_wine_quality_model(path=DEFAULT_MODEL_PATH):
    # Un archivo inexistente, truncado o corrupto puede lanzar errores muy
    # distintos (FileNotFoundError, EOFError, struct.error, IndexError...).
    # Se convierten en ValueError para que el CLI responda con código 2 y un
    # mensaje claro en lugar de un traceback.
    try:
        model = joblib.load(path)
    except Exception as error:
        raise ValueError(
            f"No se pudo cargar el artefacto {path}: {type(error).__name__}: {error}"
        ) from error

    if not isinstance(model, dict):
        raise TypeError(f"Se esperaba un dict, llegó {type(model).__name__}")

    # Artefacto incompleto: se comprueban las claves con .get() antes de usarlas,
    # porque model["estimator"] sobre un dict sin esa clave lanzaba KeyError, que
    # el CLI no capturaba.
    estimator = model.get("estimator")
    ##hecho con ia
    if not (callable(getattr(estimator, "predict", None))
            and callable(getattr(estimator, "predict_proba", None))):
        raise TypeError("El artefacto no contiene un clasificador compatible")
    #hecho con ia

    missing = [key for key in REQUIRED_ARTIFACT_KEYS if key not in model]
    if missing:
        raise ValueError(
            "El artefacto está incompleto: faltan las claves " + ", ".join(missing)
        )

    model_version = model["model_version"]
    if not isinstance(model_version, str) or not model_version.strip():
        raise ValueError("model_version debe ser un texto no vacío")

    if list(FEATURE_NAMES) != list(model["feature_names"]):
        raise ValueError ("feature_names no coincide con el contrato")
    return model

def infer_wine_quality(model:dict, request:WineQualityRequest):
    pedido_precesado=preprocess_wine_request(request).as_vector()
    target=model["estimator"].predict([pedido_precesado])[0]
    confidence=float(max(model["estimator"].predict_proba([pedido_precesado])[0]))

    return WineQualityPrediction(
        sample_id=request.sample_id,
        quality_band=str(target),
        confidence=confidence,
        model_version=model["model_version"],
        preprocessing_version=PREPROCESSING_VERSION
    )


# Declara DEFAULT_MODEL_PATH, load_wine_quality_model() e infer_wine_quality().
# Comprueba las características del artefacto antes de llamar al clasificador.
