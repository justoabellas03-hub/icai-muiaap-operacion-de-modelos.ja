"""Configuración y secretos del servicio, leídos del entorno o de `.env`.

Todas las variables llevan el prefijo `WINE_API_`. Como ejemplo ya está migrada
`WINE_API_MODE`, que en S9 se leía con `os.environ`. Los tipos complejos
(`WINE_API_CLIENTS`, `WINE_API_CORS_ORIGINS`) se escribirán en JSON.
"""

from typing import Literal

from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Scope = Literal["predict", "admin"]

STREAMLIT_ORIGIN = "http://localhost:8501"


class ClientConfig(BaseModel):
    """Credencial, permisos y cuota de un cliente de la API."""

    # `SecretStr` enmascara la clave en `repr`, `str`, logs y `model_dump_json`;
    # solo `get_secret_value()` la revela, y solo la usa `authenticate_client`.
    key: SecretStr = Field(description="API key del cliente (secreta).")
    # `Literal` hace que un scope desconocido falle al arrancar, no en runtime.
    scopes: list[Scope] = Field(description="Permisos concedidos al cliente.")
    rate_limit_per_minute: int = Field(
        default=60, gt=0, description="Peticiones permitidas por minuto."
    )


class Settings(BaseSettings):
    """Configuración validada al arrancar: si algo es inválido, no arranca."""

    model_config = SettingsConfigDict(
        env_prefix="WINE_API_", env_file=".env", extra="ignore"
    )

    mode: Literal["ready", "unavailable"] = "ready"
    # Fail closed: sin clientes configurados no existe ninguna clave válida.
    clients: dict[str, ClientConfig] = Field(default_factory=dict)
    # Por defecto solo el front de Streamlit puede leer la API desde un navegador.
    cors_origins: list[str] = Field(default_factory=lambda: [STREAMLIT_ORIGIN])
    docs_enabled: bool = True

    @field_validator("cors_origins")
    @classmethod
    def _reject_wildcard_origin(cls, origins: list[str]) -> list[str]:
        """Obliga a listar los orígenes: un `*` abriría la API a cualquier web.

        Falla al construir `Settings`, es decir, al arrancar: un error de
        configuración se detecta en el despliegue y no en la primera petición.
        """

        if "*" in origins:
            raise ValueError("CORS origins must be listed explicitly, not '*'")
        return origins
