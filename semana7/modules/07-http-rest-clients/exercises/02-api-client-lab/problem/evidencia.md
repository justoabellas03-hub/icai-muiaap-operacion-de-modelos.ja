1.cinco tests verdes;

$ uv run python -m unittest discover -s exercises/02-api-client-lab/problem/starter -p "test_*.py" -v
test_converts_connection_error (test_client.ClientExerciseTest.test_converts_connection_error) ... ok
test_converts_http_error_and_preserves_status (test_client.ClientExerciseTest.test_converts_http_error_and_preserves_status) ... ok
test_converts_timeout (test_client.ClientExerciseTest.test_converts_timeout) ... ok
test_rejects_success_json_that_is_not_an_object (test_client.ClientExerciseTest.test_rejects_success_json_that_is_not_an_object) ... ok
test_sends_json_accept_and_timeout (test_client.ClientExerciseTest.test_sends_json_accept_and_timeout) ... ok

2.salida de un 200 y un 422;

$ curl -i -X POST "$baseUrl/v1/predictions" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  --data-binary @examples/pump-maintenance-api/samples/prediction-invalid.json;
HTTP/1.1 422 Unprocessable Content
Server: S7LocalAPI/1.0 Python/3.13.15
Date: Wed, 11 Nov 2026 13:55:34 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 218
X-Request-Id: req_048eb0e3f4a5

{"error": {"code": "validation_error", "message": "JSON is valid but violates the input contract", "fields": [{"field": "measurements.vibration_mm_s", "message": "must be a number"}]}, "request_id": "req_048eb0e3f4a5"}


$ curl.exe -i "$baseUrl/health"
HTTP/1.1 200 OK
Server: S7LocalAPI/1.0 Python/3.13.15
Date: Wed, 11 Nov 2026 13:53:35 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 153
X-Request-Id: req_db400e463b49

{"status": "ok", "service": "pump-maintenance-prediction", "model_status": "ready", "model_version": "pump-risk-1.0.0", "request_id": "req_db400e463b49"}

3.Una frase que explique por qué no conviene reintentar ciegamente un POST
Estp se debe a que no es idempotenete por lo tantp en el primer intento se pudo producir un error en el tiemout nlo cual no convendría hacer otra modificación en la base de datos.

4.ningún cambio en la API de caja negra.
 git status examples/pump-maintenance-api/
On branch semana_7
nothing to commit, working tree clean

git diff --stat examples/pump-maintenance-api/server.py