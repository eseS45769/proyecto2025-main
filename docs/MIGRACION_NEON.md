# Restauración del diseño original y migración a Neon

El frontend corresponde al commit original `3e87904b0d254d628ccf07e729276c90198e31ca`.
No incluye Aladín, animaciones ni estilos de los rediseños posteriores.

## Estado

- Esquema PostgreSQL creado y validado en `saique-alfombras`, base `saique`.
- Adaptador de PostgreSQL e importador que conserva las contraseñas existentes.
- Pruebas locales: 24 pasan con SQLite y pruebas unitarias del adaptador.
- Pendiente: respaldo del servicio Render, importación real, pruebas completas con PostgreSQL y despliegue.
- No se han cambiado la contraseña ni la base de datos del servicio activo.

## Migración sin sobrescribir registros

1. Obtener un ZIP verificado desde Administración → Realizar backup y descargarlo.
   Conservar también los archivos adjuntos y respaldos previos fuera del disco efímero de Render.
2. Instalar `python -m pip install -r requirements.txt`.
3. Configurar `DATABASE_URL` con la URL directa de Neon (sin `-pooler`) fuera del repositorio.
4. Extraer `database.sqlite3` del respaldo y ejecutar:

   ```sh
   python -m backend.migrate_postgres /ruta/al/respaldo/database.sqlite3
   ```

   El importador exige destino vacío, verifica integridad y conteos, conserva IDs,
   reajusta secuencias y conserva las contraseñas en la misma transacción.
   Ante un error revierte la importación; no modifica SQLite de origen.
5. Configurar el build de Render: `pip install -r requirements.txt && python -m compileall -q backend`.
   Conservar el comando de arranque existente. Configurar la URL pooled en `DATABASE_URL` y
   `SAIQUE_SECURE_COOKIE=1`. No desplegar antes de completar la importación.
6. Verificar inicio de sesión, módulos, transacciones de compra/venta y respaldo/restauración
   en un entorno de prueba conectado a una rama aislada antes del cambio definitivo.

SQLite sigue disponible para ejecución local cuando no hay `DATABASE_URL`.
La migración de registros a Neon no convierte los archivos adjuntos en almacenamiento
persistente: los ZIP y `/archivos/` siguen utilizando `SAIQUE_DATA` y requieren almacenamiento
persistente o una migración posterior a almacenamiento de objetos.
