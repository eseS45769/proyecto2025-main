# Migración de Saique a PostgreSQL

No aplicar el cambio de producción hasta recibir y verificar un ZIP de Administración → Realizar backup de la instalación actual.

1. Conservar el ZIP original fuera del servicio. Inspeccionarlo sin escrituras con `python -m backend.migrate_snapshot respaldo.zip --report inspeccion.json`.
2. Instalar `requirements.txt` y definir DATABASE_URL en el entorno de ejecución, nunca en archivos del repositorio.
3. Importar hacia una base VACÍA con `python -m backend.migrate_snapshot respaldo.zip --apply --report migracion.json`.
4. Comprobar cada fila y cada archivo, además de los conteos. Se cierran las sesiones; se conservan usuarios, contraseñas protegidas e identificadores.
5. Preparar la actualización de Render: instalar dependencias en el build, conservar host/puerto, activar cookie Secure y consultar `/health`.
6. Aplicar el despliegue solo después de la validación de datos. Ingresar de nuevo con una cuenta existente y comprobar consultas y operaciones centrales.

El importador rechaza un destino que ya contenga datos. No borra ni sustituye una base existente. Los ZIP históricos de respaldo no están contenidos en el ZIP de la instalación: sus metadatos se conservan, pero sus archivos deben conservarse por separado. Los adjuntos del respaldo sí se importan y se guardan en PostgreSQL.

El modo local SQLite y su restauración siguen disponibles cuando DATABASE_URL no está definido. El modo PostgreSQL utiliza copias lógicas versión 2, archivos persistidos en `archivos_contenido`, ZIP en `respaldos_contenido` y un registro de restauraciones separado.

Pruebas: `python -m unittest discover -s tests -v` verifica el modo SQLite. `python tests/postgresql_integration.py` utiliza siempre un esquema nuevo `saique_test_*` en la base de pruebas indicada por DATABASE_URL. Sus datos son temporales y no deben confundirse con registros del negocio.
