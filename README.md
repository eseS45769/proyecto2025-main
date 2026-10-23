# Saique · Sistema de gestión de alfombras

Frontend y backend funcionales para los **14 casos de uso generales y sus 55 operaciones hijas** del documento `Saique_Proyecto_ER_Conectado.docx`. Incluye persistencia SQLite, autenticación, permisos por operación, auditoría y archivos asociados.

## Iniciar en Windows

Requiere **Python 3.11 o posterior**. No necesita instalar paquetes, Node ni un servidor de base de datos.

Desde esta carpeta:

```powershell
python -m backend.server
```

Abrí **http://127.0.0.1:8000**. El usuario inicial es **admin**. La contraseña aleatoria se muestra en la terminal **solo al crear la base por primera vez**. Podés cambiarla en Administración → Gestionar usuarios.

Para elegir tu contraseña antes del primer inicio:

```powershell
$env:SAIQUE_ADMIN_PASSWORD = 'TuClaveDeAlMenos10Caracteres'
python -m backend.server
```

También podés usar `iniciar.ps1` si tu configuración de PowerShell permite scripts. Para cerrar el servidor, presioná `Ctrl+C` en su terminal. Los registros permanecen guardados.

## Organización

- `frontend/modules/`: un archivo JavaScript por módulo, con cada formulario hijo definido por separado.
- `frontend/app.js`: navegación, formularios, consultas, estados de carga, tablas paginadas y exportación.
- `frontend/panels.js` y `frontend/document-theme.css`: paneles según las interfaces del documento, tablas, indicadores y formularios compactos.
- `backend/panels.py`: consultas de los indicadores y paneles con datos reales.
- `frontend/styles.css`: presentación adaptable a escritorio y móvil e impresión.
- `backend/modules/`: un archivo Python por módulo, con autorización de cada operación.
- `backend/business.py`: reglas compartidas de reservas, ventas, compras, cobros y movimientos atómicos.
- `backend/schema.sql`: las 35 tablas del modelo relacional del documento, más sesiones técnicas.
- `backend/server.py`: servidor HTTP y API del mismo origen.
- `docs/DISENO_INTERFACES.md`: criterios visuales y distribución por módulo.
- `docs/TRAZABILIDAD.md`: correspondencia CU / interfaz / frontend / backend y criterios documentales.
- `tests/`: pruebas de consistencia y pruebas del navegador.
- `data/`: base de datos, archivos, respaldos y registro externo de restauraciones. Se crea al iniciar y está excluida de Git.

## Módulos

Finanzas, Reportes, Administración, Reclamos, Pagos, Pedidos, Ventas, Clientes, Inventario, Productos, Proveedores, Marketing Digital, Envíos y Compras. Compras tiene acceso propio y acceso desde Proveedores; ambas pantallas de recepción ejecutan **la misma operación**.

Los padres organizan la navegación. Abrirlos no confirma operaciones. Los hijos automáticos muestran resultados de su documento de origen, sin crear otra recepción, otro historial o movimientos manuales.

## Flujo del documento

1. Registrá un cliente y un proveedor.
2. Registrá `ALF-001`, precio Bs 180,00, stock inicial **0**.
3. En Compras o Proveedores, recibí `CP-001`: 10 unidades a Bs 120,00. Físico: **10**.
4. Registrá un pedido de 3 unidades: total Bs 540,00; reservado **3**, disponible **7**.
5. Registrá y verificá un pago de Bs 540,00. Se reconoce un ingreso único.
6. Registrá la venta desde el pedido. Físico **7**, reservado **0**, disponible **7**.
7. Generá el comprobante interno; el mismo pago conserva su mismo número de recibo.
8. Registrá el envío, asigná transporte, registrá guía y confirmá entrega con evidencia. Físico: **7**.

## Roles y datos

El administrador puede crear cuentas internas, vincular cuentas de clientes y modificar la matriz de permisos. Los roles iniciales son Administrador, Ventas, Inventario, Marketing, Envíos y Cliente. Ventas no recibe por defecto permiso para anular ventas o pagos; el administrador lo puede autorizar. Cliente solo ve sus propios documentos.

Los importes se guardan en **centavos enteros** y se muestran en bolivianos con dos decimales, evitando errores de punto flotante. Las cantidades son unidades enteras. La disponibilidad se calcula desde físico y reservas; no se guarda un tercer saldo.

El sistema comienza sin clientes, alfombras, compras ni ventas inventados. Se incluyen las cinco categorías descritas en el documento. Los transportistas se crean desde Asignar transporte.

## Archivos, reportes y recuperación

Los formularios admiten enlaces HTTP(S) o carga de PNG, JPG, WebP, PDF y MP4 de hasta 8 MB. Los archivos se guardan junto a la base y se incluyen en respaldos.

Reportes exporta **Excel .xlsx**. **Imprimir / PDF** usa la impresión del navegador con una vista preparada para guardar como PDF. Los comprobantes son recibos internos, no facturas fiscales.

Administración genera respaldos ZIP con una copia SQLite consistente, archivos y manifiesto de hashes SHA-256. Restaurar requiere confirmación, conserva una copia previa, valida estructura e integridad, recupera el estado anterior ante un fallo y cierra las sesiones. Los ZIP descargados son copias externas; la pantalla restaura respaldos registrados en esta instalación. Para recuperar otra instalación, conservá la carpeta completa `data/`.

TikTok y WhatsApp permiten preparar contenido y registrar evidencia de difusión real. WhatsApp abre la acción de compartir para que el operador confirme el envío allí. Las métricas se ingresan con fuente; sus totales usan el último corte por publicación e indicador y no suman cortes acumulados.

## Validación

```powershell
python -m unittest discover -s tests -v
```

Comprueba los **12 escenarios PR01–PR12** del documento, más permisos, estados, saldos, métricas, correspondencia y Excel. Usa una base temporal; no toca `data/`.

La prueba opcional de navegador requiere Node 22+ y Chrome instalado:

```powershell
node tests/browser.mjs
```

Usa Chrome sin ventana, revisa los 14 padres y 55 hijos y ejecuta el flujo completo mediante sus formularios. Genera evidencia en `test-results/`, con datos separados de la instalación.

## Alcance de esta entrega

El sistema está preparado para ejecución local. No se publicó en un servidor externo ni se conectó a las APIs de TikTok, WhatsApp, bancos o transportistas. Los cobros y evidencias se verifican por el operador, como establece el documento. La operación con datos reales requiere cargar y conciliar existencias y configurar las cuentas correspondientes.

Para un servidor con HTTPS, configurá `SAIQUE_SECURE_COOKIE=1`; el servicio puede escuchar otra interfaz con `--host` y otro puerto con `--port`. La copia periódica puede programarse ejecutando `python -m backend.backup_task` desde el mismo entorno y conservando las copias fuera del equipo.
