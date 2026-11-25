# Nota de versionado: Wine Quality API 2.0.0

La API pasa de `1.1.0` a `2.0.0` porque el cambio rompe a los clientes
existentes: en 1.x un `POST /v1/predictions` sin clave devolvía `200` y ahora
devuelve `401 unauthorized`. Payloads, sobre de error y `request_id` no cambian,
pero exigir autenticación es incompatible hacia atrás y SemVer pide versión mayor.
Para seguir funcionando, el front de Streamlit de S7 debe enviar su clave en la
cabecera `X-API-Key` en cada predicción y tratar los códigos nuevos: `401`
(clave ausente o incorrecta), `403` (sin scope `predict`) y `429` (esperar los
segundos de `Retry-After` antes de reintentar). La clave del front se guardaría
fuera del código: en `.streamlit/secrets.toml` o en una variable de entorno del
contenedor, ignorados por Git, y en producción en un gestor de secretos.
