"""Starter del cliente HTTP. Completa los TODO sin modificar la API."""

from __future__ import annotations

from typing import Any

# El TODO de la práctica usará este cliente para realizar la petición HTTP.
import requests  # noqa: F401


class PredictionClientError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


def request_prediction(
    payload: dict[str, Any],
    *,
    base_url: str = "http://127.0.0.1:8000",
    timeout: float = 5.0,
    session: Any | None = None,
) -> dict[str, Any]:
    """Envía una predicción y devuelve un objeto JSON de respuesta."""
    # TODO 3: selecciona `session` o `requests` y envía POST con `json=`,
    # `Accept` y `timeout`. Comprueba los argumentos con test_client.py.
    http=session or requests
    url=f"{base_url.rstrip('/')}/v1/predictions"

    try:
        response=http.post(url, json=payload, headers={"Accept":"application/json"}, timeout=timeout)
        response.raise_for_status()
    except requests.Timeout as error:
        raise PredictionClientError("No se pudo conectar a tiempo") from error          # TODO 5
    except requests.ConnectionError as error:
        raise PredictionClientError("No se pudo conectar") from error
    except requests.HTTPError as error:
        status = response.status_code                                           # TODO 4
        raise PredictionClientError(f"La API respondió con HTTP {status}", status_code=status) from error

    data=response.json()
    if not isinstance(data, dict):
        raise PredictionClientError("La respuesta de la API no es un objeto JSON")
    return data
    # TODO 4: llama a `raise_for_status()` y conserva el status de HTTPError.
    # TODO 5: traduce Timeout y ConnectionError a PredictionClientError.
    # TODO 6: convierte la respuesta con `.json()` y exige un diccionario.





