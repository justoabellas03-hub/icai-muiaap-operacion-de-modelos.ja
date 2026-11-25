"""Punto de entrada de la API: `fastapi dev` usa `wine_api.main:app`."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from wine_api.errors import install_error_handlers
from wine_api.predictor import Predictor, build_predictor
from wine_api.rate_limit import FixedWindowRateLimiter
from wine_api.request_id import REQUEST_ID_HEADER, request_id_middleware
from wine_api.routers import admin, health, predictions
from wine_api.security import API_KEY_HEADER
from wine_api.settings import Settings

# 2.0.0: exigir `X-API-Key` rompe a los clientes anónimos de 1.x (antes un
# `POST /v1/predictions` sin clave daba 200 y ahora da 401): cambio mayor.
# Regenera el contrato con `uv run python -m wine_api.export_openapi`.
API_VERSION = "2.0.0"

API_DESCRIPTION = """
Servicio de inferencia del proyecto **Wine Quality** de Operación de Modelos.

- Todas las respuestas incluyen `request_id` y la cabecera `X-Request-Id`.
- Todos los errores comparten el sobre `ErrorResponse`; programa contra
  `error.code`, no contra `error.message`.
- La predicción es determinista y docente: no es una garantía de calidad.

**Seguridad (2.0.0)**

- Autenticación: cada cliente envía su API key en la cabecera `X-API-Key`. Sin
  clave o con una clave desconocida la API responde `401` con `unauthorized`.
- Autorización por scopes: `predict` permite `POST /v1/predictions` y `admin`
  permite `GET /v1/admin/usage`. Sin el scope necesario la respuesta es `403`
  con `forbidden`.
- Cuota por cliente: cada clave tiene un límite de peticiones por minuto. Al
  superarlo la API responde `429` con `rate_limited` y la cabecera
  `Retry-After` (segundos enteros que hay que esperar).
- `GET /health` sigue siendo público y no consume cuota.
"""

OPENAPI_TAGS = [
    {"name": "health", "description": "Disponibilidad del servicio y del modelo."},
    {"name": "predictions", "description": "Inferencia de calidad de vino tinto."},
    {
        "name": "admin",
        "description": "Operación del servicio: consumo por cliente (scope `admin`).",
    },
]

RATE_LIMIT_HEADERS = ["Retry-After", "X-RateLimit-Limit", "X-RateLimit-Remaining"]


def create_app(
    predictor: Predictor | None = None,
    settings: Settings | None = None,
    rate_limiter: FixedWindowRateLimiter | None = None,
) -> FastAPI:
    """Crea la aplicación; los tests inyectan predictor, configuración y reloj."""

    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        app.state.predictor = predictor or build_predictor(settings.mode)
        yield

    # Ocultar la documentación solo reduce lo que se anuncia: la protección
    # real es la API key. Con `docs_enabled=False` las tres rutas dan 404.
    docs = settings.docs_enabled
    app = FastAPI(
        title="Wine Quality API",
        version=API_VERSION,
        summary="Predicción de la banda de calidad de vinos tintos.",
        description=API_DESCRIPTION,
        openapi_tags=OPENAPI_TAGS,
        lifespan=lifespan,
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
        openapi_url="/openapi.json" if docs else None,
    )
    app.state.settings = settings
    app.state.rate_limiter = rate_limiter or FixedWindowRateLimiter()

    app.middleware("http")(request_id_middleware)
    # CORS se añade el último para ser el middleware más externo: responde al
    # preflight `OPTIONS` antes de llegar a las rutas. El navegador no envía
    # `X-API-Key` en el preflight, así que exigir la clave ahí lo rompería.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", API_KEY_HEADER],
        allow_credentials=False,
        expose_headers=[REQUEST_ID_HEADER, *RATE_LIMIT_HEADERS],
    )
    install_error_handlers(app)
    app.include_router(health.router)
    app.include_router(predictions.router)
    app.include_router(admin.router)
    return app


app = create_app()
