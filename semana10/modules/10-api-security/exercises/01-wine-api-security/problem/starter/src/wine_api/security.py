"""Autenticación por API key y autorización por scopes.

- Autenticación (401): ¿quién llama? La clave de `X-API-Key` debe coincidir con
  la de algún cliente configurado.
- Autorización (403): ¿qué puede hacer? El cliente debe tener el scope que
  exige el router.

La clave nunca se devuelve ni se registra en los logs.
"""

import logging
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Security
from fastapi.security import APIKeyHeader

from wine_api.dependencies import RequestIdDep, SettingsDep
from wine_api.errors import AuthenticationError, PermissionDeniedError
from wine_api.settings import Scope

logger = logging.getLogger("wine_api.security")

API_KEY_HEADER = "X-API-Key"

# `auto_error=False`: si falta la cabecera llega `None` y somos nosotros quienes
# lanzamos `AuthenticationError`, con el sobre `ErrorResponse` de siempre. Con
# `True`, FastAPI respondería con su propio error y rompería el contrato.
api_key_header = APIKeyHeader(
    name=API_KEY_HEADER,
    auto_error=False,
    description=(
        "API key del cliente en la cabecera `X-API-Key`. Cada clave tiene "
        "scopes (`predict`, `admin`) y una cuota por minuto."
    ),
)

ApiKeyDep = Annotated[str | None, Security(api_key_header)]


@dataclass(frozen=True)
class AuthenticatedClient:
    """Cliente ya autenticado. No guarda la clave: no la necesita nadie más."""

    name: str
    scopes: frozenset[str]
    rate_limit_per_minute: int


def authenticate_client(
    settings: SettingsDep, request_id: RequestIdDep, api_key: ApiKeyDep
) -> AuthenticatedClient:
    """Identifica al cliente por su API key o lanza `AuthenticationError`."""

    if api_key:
        # `compare_digest` tarda lo mismo acierte o falle en el primer byte: no
        # filtra por tiempo cuántos caracteres coinciden. Con bytes admite
        # cualquier carácter (con `str` solo ASCII y daría un 500).
        presented = api_key.encode()
        for name, config in settings.clients.items():
            expected = config.key.get_secret_value().encode()
            if secrets.compare_digest(presented, expected):
                return AuthenticatedClient(
                    name=name,
                    scopes=frozenset(config.scopes),
                    rate_limit_per_minute=config.rate_limit_per_minute,
                )
    # Solo el motivo y el `request_id`: la clave enviada nunca va al log.
    reason = "invalid" if api_key else "missing"
    logger.warning(
        "Authentication failed: %s API key (request_id=%s)",
        reason,
        request_id,
        extra={"request_id": request_id},
    )
    raise AuthenticationError()


ClientDep = Annotated[AuthenticatedClient, Security(authenticate_client)]


def require_scope(scope: Scope) -> Callable[..., AuthenticatedClient]:
    """Crea una dependencia que exige `scope`; se declara en el `APIRouter`.

    Sin scope es `403` y no `401`: el cliente ya se ha identificado (sabemos
    quién es), pero su clave no le da permiso para esta operación.
    """

    def check_scope(client: ClientDep, request_id: RequestIdDep) -> AuthenticatedClient:
        if scope not in client.scopes:
            logger.warning(
                "Permission denied: client %s lacks scope %s (request_id=%s)",
                client.name,
                scope,
                request_id,
                extra={"request_id": request_id},
            )
            raise PermissionDeniedError()
        return client

    return check_scope
