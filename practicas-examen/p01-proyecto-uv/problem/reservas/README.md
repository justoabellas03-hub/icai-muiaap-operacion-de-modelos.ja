
Preguntas de repaso (para el examen)
¿Qué diferencia hay entre dependencies y el grupo dev? ¿Qué instala uv sync --no-dev?
dev:Herramientas que solo usas tú para desarrollar, probar o formatear el código y dependencies son las librerías que se van a usar en el código, uv sync --no-dev instala únicamente las dependencias principales

¿Por qué uv.lock sí se sube al repositorio y .venv/ no?
uv lock es una archivo de texto que recopila la version de las librerías instaladas y .venv contien las librerñías del entorno por lo que ocupa muchísmo espacio y no conviene subirlo a guithub
Un compañero clona tu repositorio. ¿Qué dos comandos necesita para tener el modelo entrenado?
uv sync 
uv run entrenar
¿Qué pasaría con RUTA_DATOS = "reservas_hotel.csv" si ejecutas los tests desde otra carpeta?
Python buscaría reservas_hotel.csv dentro de la carpeta desde donde lanzaste el comando pytest. Al no encontrarlo ahí, lanzaría un error FileNotFoundError
Que el proyecto no sería reproducible
¿Para qué sirve .python-version? ¿Y requires-python?
.python-version indica la versión exacta de python que el proyecto necesita
 requires-python indica el rango mínimo de python que necesita el proyecto.

