"""Pruebas sin red: se sustituye requests.get por un doble que registra las llamadas."""

import pytest

from request_aemet import openapi

INVENTARIO = [
    {"indicativo": "3195", "nombre": "MADRID, RETIRO", "provincia": "MADRID"},
    {
        "indicativo": "3194U",
        "nombre": "MADRID, CIUDAD UNIVERSITARIA",
        "provincia": "MADRID",
    },
]


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = str(payload)
        self.encoding = None

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)

    def json(self):
        return self._payload


@pytest.fixture
def calls(monkeypatch):
    registro = []

    def fake_get(url, params=None, headers=None, timeout=None):
        registro.append({"url": url, "params": params, "headers": headers})
        if url.startswith(openapi.BASE_URL):
            return FakeResponse(
                {"estado": 200, "descripcion": "exito", "datos": "https://datos/tmp"}
            )
        return FakeResponse(INVENTARIO)

    monkeypatch.setenv("API_KEY", "clave-de-prueba")
    monkeypatch.setattr(openapi.requests, "get", fake_get)
    return registro


def test_api_key_goes_in_query_string_not_headers(calls):
    openapi.get_env_data(openapi.INVENTARIO_ENDPOINT)

    primera = calls[0]
    assert primera["url"] == openapi.BASE_URL + openapi.INVENTARIO_ENDPOINT
    assert primera["params"] == {"api_key": "clave-de-prueba"}
    assert not primera["headers"]


def test_data_url_is_downloaded_without_api_key(calls):
    openapi.get_env_data(openapi.INVENTARIO_ENDPOINT)

    segunda = calls[1]
    assert segunda["url"] == "https://datos/tmp"
    assert not segunda["params"] and not segunda["headers"]


def test_finds_ciudad_universitaria_in_inventory():
    assert openapi.buscar_indicativo(INVENTARIO) == "3194U"
    assert openapi.buscar_indicativo(INVENTARIO, " madrid, ciudad universitaria ") == "3194U"


def test_unknown_station_is_an_error():
    with pytest.raises(ValueError, match="No se ha encontrado"):
        openapi.buscar_indicativo(INVENTARIO, "MADRID, BARAJAS")


def test_missing_api_key_fails_before_calling_aemet(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.setattr(
        openapi.requests, "get", lambda *a, **k: pytest.fail("no debe llamar")
    )

    with pytest.raises(RuntimeError, match="API_KEY"):
        openapi.get_env_data(openapi.INVENTARIO_ENDPOINT)


def test_aemet_error_status_is_reported(monkeypatch):
    monkeypatch.setenv("API_KEY", "clave-de-prueba")
    monkeypatch.setattr(
        openapi.requests,
        "get",
        lambda *a, **k: FakeResponse({"estado": 401, "descripcion": "API key invalido"}),
    )

    with pytest.raises(ValueError, match="API key invalido"):
        openapi.get_env_data(openapi.INVENTARIO_ENDPOINT)


def test_climatologias_uses_the_station_from_the_inventory(calls):
    openapi.climatologias_diarias(
        "2019-10-01T00:00:00UTC", "2019-10-30T23:59:59UTC", "3194U"
    )

    assert calls[0]["url"].endswith(
        "/fechaini/2019-10-01T00:00:00UTC/fechafin/2019-10-30T23:59:59UTC"
        "/estacion/3194U"
    )
    assert calls[0]["params"] == {"api_key": "clave-de-prueba"}
