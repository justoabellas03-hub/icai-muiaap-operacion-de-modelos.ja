from fastapi import APIRouter, Depends

from wine_api.dependencies import RequestIdDep, SettingsDep
from wine_api.rate_limit import RateLimiterDep
from wine_api.schemas import ClientUsage, ErrorResponse, UsageResponse
from wine_api.security import require_scope

# Solo el scope `admin`. Sin rate limit: consultar el consumo no debe gastar la
# cuota que se está midiendo (y `ops` tiene que poder mirarlo aunque la agote).
router = APIRouter(
    prefix="/v1/admin",
    tags=["admin"],
    dependencies=[Depends(require_scope("admin"))],
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Falta la cabecera `X-API-Key` o la clave no es válida.",
        },
        403: {
            "model": ErrorResponse,
            "description": "La clave no tiene el scope `admin`.",
        },
    },
)


@router.get(
    "/usage",
    summary="Consultar el consumo de cada cliente",
    response_description="Peticiones de cada cliente en la ventana actual.",
)
def read_usage(
    settings: SettingsDep, limiter: RateLimiterDep, request_id: RequestIdDep
) -> UsageResponse:
    """Devuelve, por cliente configurado, su consumo en la ventana actual.

    - Un elemento por cliente, ordenados por nombre, con las peticiones
      contadas en la ventana del rate limit y su límite por minuto.
    - Nunca incluye las API keys: identifica a cada cliente por su nombre.
    - Exige una API key con scope `admin` y no consume cuota.
    """

    clients = [
        ClientUsage(
            client=name,
            requests_in_window=limiter.usage(name),
            limit=config.rate_limit_per_minute,
        )
        for name, config in sorted(settings.clients.items())
    ]
    return UsageResponse(clients=clients, request_id=request_id)
